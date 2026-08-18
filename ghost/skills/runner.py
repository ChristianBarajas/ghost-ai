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

            # ------------------------------------------
            # NAVIGATE
            # ------------------------------------------

            if step.action_type == "navigate":
                print(f"👻 OPEN → {url}")

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                )

            # ------------------------------------------
            # INPUT
            # ------------------------------------------

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

            # ------------------------------------------
            # CLICK / SUBMIT
            # ------------------------------------------

            elif step.action_type == "click":
                print(
                    f"👻 ACTION → {target}"
                )

                # Search workflows are more reliable
                # when submitted directly from the
                # input that received the query.
                if (
                    skill.name == "web_search"
                    and target
                    and "search" in target.lower()
                    and last_input_locator is not None
                ):
                    print(
                        "👻 SUBMIT → pressing ENTER"
                    )

                    old_url = page.url

                    last_input_locator.press(
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
                            "⚠️ No URL change detected "
                            "after ENTER."
                        )

                    continue

                # Normal click behavior for non-search skills.
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

        print()
        print("✅ Skill finished.")
        print("Press ENTER to close the browser.")

        input()

        browser.close()