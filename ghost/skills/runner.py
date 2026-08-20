from playwright.sync_api import sync_playwright

from ghost.skills.storage import load_skill
from ghost.skills.providers import get_provider
from ghost.skills.research import (
    find_useful_research_source,
    build_research_result,
    print_research_result,
    get_domain,
)


# --------------------------------------------------
# BASIC HELPERS
# --------------------------------------------------

def replace_variables(
    value,
    variables,
):
    if value is None:
        return None

    for name, variable_value in variables.items():
        value = value.replace(
            f"{{{{{name}}}}}",
            variable_value,
        )

    return value


# --------------------------------------------------
# TARGET RESOLUTION
# --------------------------------------------------

def resolve_semantic_target(
    page,
    target,
):
    if target != "search_input":
        return None

    print(
        "👻 RESOLVE → looking for search input"
    )

    candidates = [
        page.locator(
            'input[type="search"]'
        ),
        page.get_by_role(
            "searchbox"
        ),
        page.locator(
            'input[placeholder*="search" i]'
        ),
        page.locator(
            'textarea[placeholder*="search" i]'
        ),
        page.locator(
            'input[aria-label*="search" i]'
        ),
        page.locator(
            'textarea[aria-label*="search" i]'
        ),
        page.locator(
            'input[name="q"]'
        ),
        page.locator(
            'textarea[name="q"]'
        ),
    ]

    for locator in candidates:
        try:
            if locator.count() == 0:
                continue

            element = locator.first

            if element.is_visible():
                print(
                    "✅ RESOLVE → search input found"
                )

                return element

        except Exception:
            continue

    print(
        "❌ RESOLVE → search input not found"
    )

    return None


def resolve_literal_target(
    page,
    target,
):
    candidates = [
        page.get_by_label(
            target,
            exact=True,
        ),
        page.get_by_placeholder(
            target,
            exact=True,
        ),
        page.get_by_role(
            "textbox",
            name=target,
            exact=True,
        ),
    ]

    for locator in candidates:
        try:
            if locator.count() > 0:
                return locator.first

        except Exception:
            continue

    return None


# --------------------------------------------------
# SEARCH SUBMISSION
# --------------------------------------------------

def submit_search(
    page,
    locator,
    provider,
):
    old_url = page.url

    submit_strategy = (
        provider.get(
            "submit_strategy"
        )
        if provider
        else "form"
    )

    if submit_strategy == "form":
        print(
            "👻 SUBMIT → submitting parent form"
        )

        try:
            submitted = locator.evaluate(
                """
                element => {
                    if (!element.form) {
                        return false;
                    }

                    element.form.requestSubmit();

                    return true;
                }
                """
            )

        except Exception:
            submitted = False

        if not submitted:
            print(
                "⚠️ Form submission unavailable. "
                "Falling back to ENTER."
            )

            locator.press(
                "Enter"
            )

    else:
        print(
            "👻 SUBMIT → pressing ENTER"
        )

        locator.press(
            "Enter"
        )

    try:
        page.wait_for_url(
            lambda current_url:
                current_url != old_url,
            timeout=7000,
        )

        print(
            "👻 RESULT → page changed"
        )

    except Exception:
        print(
            "⚠️ No URL change detected."
        )

    try:
        page.wait_for_load_state(
            "domcontentloaded",
            timeout=5000,
        )

    except Exception:
        pass

    page.wait_for_timeout(
        750
    )


# --------------------------------------------------
# LEGACY CLICK SUPPORT
# --------------------------------------------------

def perform_click(
    page,
    target,
):
    print(
        f"👻 ACTION → {target}"
    )

    locator = page.get_by_role(
        "button",
        name=target,
        exact=True,
    )

    if locator.count() == 0:
        locator = page.get_by_role(
            "link",
            name=target,
            exact=True,
        )

    if locator.count() == 0:
        locator = page.get_by_text(
            target,
            exact=True,
        )

    if locator.count() == 0:
        print(
            f"⚠️ Could not find "
            f"click target: {target}"
        )

        return False

    locator.first.click()

    page.wait_for_timeout(
        750
    )

    return True


# --------------------------------------------------
# VERIFICATION
# --------------------------------------------------

def verify_web_search(
    page,
):
    current_url = (
        page.url.lower()
    )

    looks_like_results_url = (
        "/search" in current_url
        or "?q=" in current_url
        or "&q=" in current_url
    )

    if looks_like_results_url:
        print(
            "✅ Search results detected."
        )

        print(
            f"✅ Current page: {page.url}"
        )

        return True

    print(
        "❌ Search results could not "
        "be verified."
    )

    print(
        f"Current page: {page.url}"
    )

    return False


def verify_research_topic(
    page,
    research_result,
):
    search_domains = {
        "www.bing.com",
        "bing.com",
        "duckduckgo.com",
        "www.duckduckgo.com",
    }

    current_domain = get_domain(
        page.url
    )

    external_page = (
        current_domain
        and current_domain
        not in search_domains
    )

    has_summary = (
        research_result is not None
        and len(
            research_result.get(
                "summary",
                "",
            )
        ) > 100
    )

    if (
        external_page
        and has_summary
    ):
        print(
            "✅ External research source detected."
        )

        print(
            "✅ Research summary generated."
        )

        print(
            f"✅ Source domain: "
            f"{current_domain}"
        )

        print(
            f"✅ Current page: {page.url}"
        )

        return True

    if not external_page:
        print(
            "❌ GHOST did not reach "
            "a valid external source."
        )

    if not has_summary:
        print(
            "❌ GHOST did not produce "
            "a usable summary."
        )

    return False


def verify_skill(
    skill,
    page,
    research_result=None,
):
    print()
    print(
        "👻 VERIFYING RESULT"
    )
    print(
        "-------------------"
    )

    if skill.name == "web_search":
        return verify_web_search(
            page
        )

    if skill.name == "research_topic":
        return verify_research_topic(
            page,
            research_result,
        )

    print(
        f"⚠️ No verification rule exists "
        f"for '{skill.name}'."
    )

    return None


# --------------------------------------------------
# RESEARCH EXECUTION
# --------------------------------------------------

def run_research_step(
    page,
    variables,
):
    query = variables.get(
        "query"
    )

    page, extracted_content = (
        find_useful_research_source(
            page,
            query,
            max_attempts=5,
        )
    )

    if extracted_content is None:
        return (
            page,
            None,
        )

    research_result = (
        build_research_result(
            extracted_content,
            query,
        )
    )

    if research_result is not None:
        print_research_result(
            research_result
        )

    return (
        page,
        research_result,
    )


# --------------------------------------------------
# SKILL RUNNER
# --------------------------------------------------

def run_skill(
    skill_name: str,
    variables: dict,
    provider_name=None,
):
    skill = load_skill(
        skill_name
    )

    provider = get_provider(
        skill_name,
        provider_name,
    )

    print()
    print(
        "👻 GHOST SKILL RUNNER"
    )
    print(
        "---------------------"
    )

    print(
        f"Skill: {skill.name}"
    )

    if provider:
        print(
            f"Provider: {provider['name']}"
        )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False
        )

        context = browser.new_context()

        page = context.new_page()

        if provider:
            print(
                f"👻 OPEN → "
                f"{provider['start_url']}"
            )

            page.goto(
                provider["start_url"],
                wait_until="domcontentloaded",
            )

        last_input_locator = None
        research_result = None

        for step in skill.steps:
            target = replace_variables(
                step.target,
                variables,
            )

            value = replace_variables(
                step.value,
                variables,
            )

            url = replace_variables(
                step.url,
                variables,
            )

            # ----------------------------------
            # NAVIGATE
            # ----------------------------------

            if step.action_type == "navigate":
                print(
                    f"👻 OPEN → {url}"
                )

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                )

            # ----------------------------------
            # INPUT
            # ----------------------------------

            elif step.action_type == "input":
                print(
                    f'👻 TYPE → '
                    f'{target}: "{value}"'
                )

                locator = None

                if target == "search_input":
                    locator = (
                        resolve_semantic_target(
                            page,
                            target,
                        )
                    )

                if locator is None:
                    locator = (
                        resolve_literal_target(
                            page,
                            target,
                        )
                    )

                if locator is None:
                    print(
                        f"❌ Could not resolve "
                        f"input: {target}"
                    )

                    continue

                last_input_locator = locator

                locator.fill(
                    value
                )

            # ----------------------------------
            # SUBMIT
            # ----------------------------------

            elif step.action_type == "submit":
                print(
                    f"👻 SUBMIT → {target}"
                )

                locator = last_input_locator

                if (
                    locator is None
                    and target == "search_input"
                ):
                    locator = (
                        resolve_semantic_target(
                            page,
                            target,
                        )
                    )

                if locator is None:
                    print(
                        "❌ Could not resolve "
                        "submission target."
                    )

                    continue

                submit_search(
                    page,
                    locator,
                    provider,
                )

            # ----------------------------------
            # SELECT
            # ----------------------------------

            elif step.action_type == "select":
                # research_topic performs selection
                # inside research.py because it may
                # need to try multiple results.
                if skill.name == "research_topic":
                    continue

                print(
                    f"👻 SELECT → {target}"
                )

            # ----------------------------------
            # OPEN
            # ----------------------------------

            elif step.action_type == "open":
                if (
                    skill.name == "research_topic"
                    and target == "external_source"
                ):
                    (
                        page,
                        research_result,
                    ) = run_research_step(
                        page,
                        variables,
                    )

            # ----------------------------------
            # EXTRACT
            # ----------------------------------

            elif step.action_type == "extract":
                # Extraction already happens inside
                # research.py while evaluating sources.
                if (
                    skill.name == "research_topic"
                    and research_result is not None
                ):
                    print(
                        "👻 EXTRACT → "
                        "research content ready"
                    )

                elif (
                    skill.name == "research_topic"
                ):
                    print(
                        "⚠️ No accepted research "
                        "source available to extract."
                    )

            # ----------------------------------
            # CLICK
            # ----------------------------------

            elif step.action_type == "click":
                perform_click(
                    page,
                    target,
                )

            # ----------------------------------
            # UNKNOWN ACTION
            # ----------------------------------

            else:
                print(
                    f"⚠️ Unknown action type: "
                    f"{step.action_type}"
                )

        result = verify_skill(
            skill,
            page,
            research_result,
        )

        print()

        if result is True:
            print(
                "✅ GHOST verified "
                "successful completion."
            )

        elif result is False:
            print(
                "❌ GHOST could not "
                "verify completion."
            )

        else:
            print(
                "⚠️ Workflow finished "
                "without verification."
            )

        print()
        print(
            "Press ENTER to close the browser."
        )

        input()

        context.close()
        browser.close()

        return research_result