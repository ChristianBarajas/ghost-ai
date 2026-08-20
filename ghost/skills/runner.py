from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from ghost.skills.storage import load_skill
from ghost.skills.providers import get_provider


def replace_variables(value, variables):
    if value is None:
        return None

    for name, variable_value in variables.items():
        value = value.replace(
            f"{{{{{name}}}}}",
            variable_value,
        )

    return value


def get_domain(url):
    if not url:
        return None

    return urlparse(url).netloc.lower()


def resolve_semantic_target(page, target):
    if target == "search_input":
        print(
            "👻 RESOLVE → looking for search input"
        )

        candidates = [
            page.locator('input[type="search"]'),
            page.get_by_role("searchbox"),
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
            page.locator('input[name="q"]'),
            page.locator('textarea[name="q"]'),
        ]

        for locator in candidates:
            try:
                if locator.count() > 0:
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


def resolve_literal_target(page, target):
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


def resolve_relevant_result(page):
    print(
        "👻 RESOLVE → looking for relevant result"
    )

    candidates = [
        page.locator("li.b_algo h2 a"),
        page.locator("main h2 a"),
        page.locator("main h3 a"),
        page.locator('a[href^="http"]'),
    ]

    for locator_group in candidates:
        try:
            count = locator_group.count()

            for index in range(
                min(count, 20)
            ):
                locator = locator_group.nth(
                    index
                )

                try:
                    if not locator.is_visible():
                        continue

                    href = locator.get_attribute(
                        "href"
                    )

                    text = (
                        locator.inner_text()
                        .strip()
                    )

                    if not href:
                        continue

                    if len(text) < 5:
                        continue

                    print(
                        "✅ RESOLVE → relevant result found"
                    )

                    print(
                        f"👻 RESULT → {text[:100]}"
                    )

                    return locator

                except Exception:
                    continue

        except Exception:
            continue

    print(
        "❌ RESOLVE → relevant result not found"
    )

    return None


def submit_search(
    page,
    locator,
    provider,
):
    old_url = page.url

    submit_strategy = (
        provider.get("submit_strategy")
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


def open_selected_result(
    page,
    selected_result,
):
    if selected_result is None:
        print(
            "❌ No selected result to open."
        )
        return page

    href = None

    try:
        href = selected_result.get_attribute(
            "href"
        )
    except Exception:
        pass

    print(
        "👻 OPEN → selected result"
    )

    if href:
        try:
            page.goto(
                href,
                wait_until="domcontentloaded",
                timeout=15000,
            )

            # Give redirects time to reach
            # the real external destination.
            try:
                page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=8000,
                )
            except Exception:
                pass

            page.wait_for_timeout(
                1500
            )

            print(
                f"👻 NAVIGATED → {page.url}"
            )

            return page

        except Exception:
            pass

    old_url = page.url

    try:
        selected_result.click()

        page.wait_for_timeout(
            1500
        )

    except Exception as error:
        print(
            f"❌ Could not open result: {error}"
        )

        return page

    try:
        page.wait_for_load_state(
            "domcontentloaded",
            timeout=8000,
        )
    except Exception:
        pass

    if page.url != old_url:
        print(
            f"👻 NAVIGATED → {page.url}"
        )

    return page


def verify_web_search(page):
    current_url = page.url.lower()

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
        "❌ Search results could not be verified."
    )

    print(
        f"Current page: {page.url}"
    )

    return False


def verify_research_topic(page):
    search_domains = {
        "www.bing.com",
        "bing.com",
        "duckduckgo.com",
        "www.duckduckgo.com",
    }

    # Retry because external pages can take
    # a moment to finish redirects/rendering.
    for attempt in range(3):
        current_url = page.url

        current_domain = get_domain(
            current_url
        )

        external_page = (
            current_domain
            and current_domain
            not in search_domains
        )

        try:
            page_text = (
                page
                .locator("body")
                .inner_text(
                    timeout=5000
                )
            )

            enough_content = (
                len(
                    page_text.strip()
                ) > 200
            )

        except Exception:
            enough_content = False

        if external_page and enough_content:
            print(
                "✅ External research source detected."
            )

            print(
                f"✅ Source domain: {current_domain}"
            )

            print(
                f"✅ Current page: {page.url}"
            )

            return True

        if attempt < 2:
            print(
                "👻 VERIFY → waiting for source content..."
            )

            page.wait_for_timeout(
                1250
            )

    print(
        "❌ Research source could not be verified."
    )

    print(
        f"Current page: {page.url}"
    )

    return False


def verify_skill(
    skill,
    page,
):
    print()
    print("👻 VERIFYING RESULT")
    print("-------------------")

    if skill.name == "web_search":
        return verify_web_search(
            page
        )

    if skill.name == "research_topic":
        return verify_research_topic(
            page
        )

    print(
        f"⚠️ No verification rule exists "
        f"for '{skill.name}'."
    )

    return None


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
    print("👻 GHOST SKILL RUNNER")
    print("---------------------")
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
                f"👻 OPEN → {provider['start_url']}"
            )

            page.goto(
                provider["start_url"],
                wait_until="domcontentloaded",
            )

        last_input_locator = None
        selected_result = None

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

            # NAVIGATE
            if step.action_type == "navigate":
                print(
                    f"👻 OPEN → {url}"
                )

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                )

            # INPUT
            elif step.action_type == "input":
                print(
                    f'👻 TYPE → {target}: "{value}"'
                )

                locator = None

                if target == "search_input":
                    locator = resolve_semantic_target(
                        page,
                        target,
                    )

                if locator is None:
                    locator = resolve_literal_target(
                        page,
                        target,
                    )

                if locator is None:
                    print(
                        f"❌ Could not resolve input: "
                        f"{target}"
                    )

                    continue

                last_input_locator = locator

                locator.fill(
                    value
                )

            # SUBMIT
            elif step.action_type == "submit":
                print(
                    f"👻 SUBMIT → {target}"
                )

                locator = last_input_locator

                if (
                    locator is None
                    and target == "search_input"
                ):
                    locator = resolve_semantic_target(
                        page,
                        target,
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

            # SELECT
            elif step.action_type == "select":
                if target == "relevant_result":
                    selected_result = (
                        resolve_relevant_result(
                            page
                        )
                    )

            # OPEN
            elif step.action_type == "open":
                if target == "external_source":
                    page = open_selected_result(
                        page,
                        selected_result,
                    )

            # OLD CLICK SUPPORT
            elif step.action_type == "click":
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
                        f"⚠️ Could not find click "
                        f"target: {target}"
                    )

                    continue

                locator.first.click()

                page.wait_for_timeout(
                    750
                )

        result = verify_skill(
            skill,
            page,
        )

        print()

        if result is True:
            print(
                "✅ GHOST verified successful completion."
            )

        elif result is False:
            print(
                "❌ GHOST could not verify completion."
            )

        else:
            print(
                "⚠️ Workflow finished without verification."
            )

        print()
        print(
            "Press ENTER to close the browser."
        )

        input()

        context.close()
        browser.close()