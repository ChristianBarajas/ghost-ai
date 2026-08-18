from playwright.sync_api import sync_playwright

from ghost.skills.storage import load_skill


def replace_variables(value, variables):
    if value is None:
        return None

    for name, variable_value in variables.items():
        value = value.replace(
            f"{{{{{name}}}}}",
            variable_value,
        )

    return value


def verify_skill(skill, page, variables):
    print()
    print("👻 VERIFYING RESULT")
    print("-------------------")

    if skill.name == "web_search":
        query = variables.get("query")

        if not query:
            print("❌ No search query was provided.")
            return False

        current_url = page.url.lower()

        query_words = [
            word.lower()
            for word in query.split()
            if len(word) > 2
        ]

        url_match = any(
            word in current_url
            for word in query_words
        )

        try:
            page_text = page.locator(
                "body"
            ).inner_text().lower()
        except Exception:
            page_text = ""

        page_match = any(
            word in page_text
            for word in query_words
        )

        if url_match or page_match:
            print("✅ Search results detected.")
            print(f"✅ Current page: {page.url}")
            return True

        print("❌ Search results could not be verified.")
        print(f"Current page: {page.url}")

        return False

    print(
        f"⚠️ No verification rule exists for '{skill.name}'."
    )

    return None


def run_skill(skill_name: str, variables: dict):
    skill = load_skill(skill_name)

    print()
    print("👻 GHOST SKILL RUNNER")
    print("---------------------")
    print(f"Skill: {skill.name}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        last_input_locator = None

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

            if step.action_type == "navigate":
                print(f"👻 OPEN → {url}")

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                )

            elif step.action_type == "input":
                print(
                    f'👻 TYPE → {target}: "{value}"'
                )

                locator = page.get_by_label(
                    target,
                    exact=True,
                )

                if locator.count() == 0:
                    locator = page.get_by_placeholder(
                        target,
                        exact=True,
                    )

                if locator.count() == 0:
                    locator = page.get_by_role(
                        "textbox",
                        name=target,
                        exact=True,
                    )

                if locator.count() == 0:
                    print(
                        f"⚠️ Could not find input: {target}"
                    )
                    continue

                last_input_locator = locator.first

                last_input_locator.fill(
                    value
                )

            elif step.action_type == "click":
                print(
                    f"👻 ACTION → {target}"
                )

                if (
                    skill.name == "web_search"
                    and target
                    and "search" in target.lower()
                    and last_input_locator is not None
                ):
                    print(
                        "👻 SUBMIT → pressing ENTER"
                    )

                    last_input_locator.press(
                        "Enter"
                    )

                    try:
                        page.wait_for_load_state(
                            "domcontentloaded",
                            timeout=5000,
                        )
                    except Exception:
                        pass

                    page.wait_for_timeout(
                        1000
                    )

                    continue

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
                        f"⚠️ Could not find click target: {target}"
                    )
                    continue

                locator.first.click()

                page.wait_for_timeout(
                    750
                )

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