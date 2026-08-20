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


def verify_skill(
    skill,
    page,
    variables,
):
    print()
    print("👻 VERIFYING RESULT")
    print("-------------------")

    if skill.name == "web_search":
        query = variables.get(
            "query"
        )

        if not query:
            print(
                "❌ No search query was provided."
            )
            return False

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

    print(
        f"⚠️ No verification rule exists "
        f"for '{skill.name}'."
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
        else "enter"
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
            timeout=5000,
        )

        print(
            "👻 RESULT → page changed"
        )

    except Exception:
        print(
            "⚠️ No URL change detected."
        )

    page.wait_for_timeout(
        750
    )


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

        page = browser.new_page()

        # ------------------------------------------
        # PROVIDER / ENVIRONMENT
        # ------------------------------------------

        if provider:
            print(
                f"👻 OPEN → {provider['start_url']}"
            )

            page.goto(
                provider["start_url"],
                wait_until="domcontentloaded",
            )

        last_input_locator = None

        # ------------------------------------------
        # RUN LEARNED SKILL
        # ------------------------------------------

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

        # ------------------------------------------
        # VERIFY
        # ------------------------------------------

        result = verify_skill(
            skill,
            page,
            variables,
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

        browser.close()