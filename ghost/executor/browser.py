from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from ghost.memory.database import get_actions


def find_input(page, target: str):
    strategies = [
        lambda: page.get_by_label(target, exact=True),
        lambda: page.get_by_placeholder(target, exact=True),
        lambda: page.get_by_role("textbox", name=target, exact=True),
    ]

    for strategy in strategies:
        try:
            locator = strategy()

            if locator.count() > 0:
                return locator.first
        except Exception:
            pass

    return None


def find_click_target(page, target: str):
    strategies = [
        lambda: page.get_by_role("button", name=target, exact=True),
        lambda: page.get_by_role("link", name=target, exact=True),
        lambda: page.get_by_text(target, exact=True),
    ]

    for strategy in strategies:
        try:
            locator = strategy()

            if locator.count() > 0:
                return locator.first
        except Exception:
            pass

    # If GHOST recorded an ID like #something
    if target and target.startswith("#"):
        try:
            locator = page.locator(target)

            if locator.count() > 0:
                return locator.first
        except Exception:
            pass

    return None


def replay_workflow(workflow_id: int):
    actions = get_actions(workflow_id)

    if not actions:
        print(f"❌ No actions found for workflow #{workflow_id}.")
        return

    print()
    print("👻 GHOST REPLAY")
    print("----------------")
    print(f"Replaying workflow #{workflow_id}")
    print()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False
        )

        context = browser.new_context()
        page = context.new_page()

        first_navigation_done = False

        for action in actions:
            action_type = action["action_type"]
            target = action["target"]
            value = action["value"]
            url = action["url"]

            # --------------------------------------------------
            # NAVIGATION
            # --------------------------------------------------

            if action_type == "navigate":
                # For V1, only replay the first direct navigation.
                # Later navigation events were usually caused by
                # the user's clicks or form submissions.
                if first_navigation_done:
                    continue

                print(f"👻 OPEN → {url}")

                try:
                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=15000,
                    )

                    first_navigation_done = True

                except PlaywrightTimeoutError:
                    print(
                        "⚠️ Page load timed out, continuing anyway."
                    )

                    first_navigation_done = True

            # --------------------------------------------------
            # INPUT
            # --------------------------------------------------

            elif action_type == "input":
                # Ignore observer noise such as empty focus events.
                if value is None or value.strip() == "":
                    continue

                print(
                    f'👻 TYPE → {target}: "{value}"'
                )

                locator = find_input(
                    page,
                    target
                )

                if locator is None:
                    print(
                        f"⚠️ Could not find input: {target}"
                    )
                    continue

                try:
                    locator.fill(value)

                except Exception as error:
                    print(
                        f"⚠️ Input failed: {error}"
                    )

            # --------------------------------------------------
            # CLICK
            # --------------------------------------------------

            elif action_type == "click":
                if not target:
                    continue

                print(
                    f"👻 CLICK → {target}"
                )

                locator = find_click_target(
                    page,
                    target
                )

                if locator is None:
                    print(
                        f"⚠️ Could not find: {target}"
                    )
                    continue

                try:
                    locator.click(
                        timeout=5000
                    )

                    page.wait_for_timeout(
                        750
                    )

                except Exception as error:
                    print(
                        f"⚠️ Click failed: {error}"
                    )

        print()
        print("✅ Replay finished.")
        print(
            "Press ENTER to close the browser."
        )

        input()

        context.close()
        browser.close()
