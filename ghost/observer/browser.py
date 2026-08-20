import time

from playwright.sync_api import sync_playwright

from ghost.memory.database import save_action
from ghost.models.action import Action


last_action = None
last_action_time = 0


def should_ignore_url(url: str) -> bool:
    if not url:
        return True

    ignored_parts = [
        "about:blank",
        "chrome-error://",
        "/sorry/",
        "recaptcha",
    ]

    return any(
        part in url.lower()
        for part in ignored_parts
    )


def is_duplicate(action: Action) -> bool:
    global last_action
    global last_action_time

    now = time.time()

    if last_action is None:
        last_action = action
        last_action_time = now
        return False

    same = (
        action.action_type == last_action.action_type
        and action.target == last_action.target
        and action.value == last_action.value
        and action.url == last_action.url
    )

    if same and (now - last_action_time) < 1.0:
        return True

    last_action = action
    last_action_time = now

    return False


def save_clean_action(
    workflow_id: int,
    action: Action,
):
    if should_ignore_url(
        action.url
    ):
        return

    if is_duplicate(
        action
    ):
        return

    save_action(
        workflow_id,
        action,
    )

    if action.action_type == "navigate":
        print(
            f"👻 NAVIGATE → {action.url}"
        )

    elif action.action_type == "click":
        print(
            f"👻 CLICK → {action.target}"
        )

    elif action.action_type == "input":
        print(
            f'👻 INPUT → {action.target}: "{action.value}"'
        )


def handle_browser_action(
    workflow_id: int,
    data: dict,
):
    action = Action(
        action_type=data.get(
            "action_type"
        ),
        target=data.get(
            "target"
        ),
        value=data.get(
            "value"
        ),
        url=data.get(
            "url"
        ),
    )

    save_clean_action(
        workflow_id,
        action,
    )


OBSERVER_SCRIPT = """
(() => {
    if (window.__ghostObserverInstalled) {
        return;
    }

    window.__ghostObserverInstalled = true;

    function describeElement(element) {
        if (!element) {
            return "unknown";
        }

        const aria =
            element.getAttribute?.("aria-label");

        const placeholder =
            element.getAttribute?.("placeholder");

        const name =
            element.getAttribute?.("name");

        const id =
            element.id
                ? `#${element.id}`
                : null;

        const text =
            element.innerText
                ?.trim()
                ?.replace(/\\s+/g, " ")
                ?.slice(0, 120);

        return (
            aria ||
            placeholder ||
            name ||
            text ||
            id ||
            element.tagName?.toLowerCase() ||
            "unknown"
        );
    }

    function recordInput(element) {
        if (
            !element ||
            ![
                "INPUT",
                "TEXTAREA",
                "SELECT"
            ].includes(element.tagName)
        ) {
            return;
        }

        window.ghostRecordAction({
            action_type: "input",
            target: describeElement(element),
            value: element.value,
            url: window.location.href
        });
    }

    document.addEventListener(
        "click",
        (event) => {
            window.ghostRecordAction({
                action_type: "click",
                target: describeElement(
                    event.target
                ),
                value: null,
                url: window.location.href
            });
        },
        true
    );

    document.addEventListener(
        "change",
        (event) => {
            recordInput(
                event.target
            );
        },
        true
    );

    document.addEventListener(
        "keydown",
        (event) => {
            if (event.key === "Enter") {
                recordInput(
                    event.target
                );
            }
        },
        true
    );

    document.addEventListener(
        "blur",
        (event) => {
            recordInput(
                event.target
            );
        },
        true
    );

    let scrollTimer = null;

    window.addEventListener(
        "scroll",
        () => {
            clearTimeout(
                scrollTimer
            );

            scrollTimer = setTimeout(
                () => {
                    window.ghostRecordAction({
                        action_type: "scroll",
                        target: "page",
                        value: String(
                            Math.round(
                                window.scrollY
                            )
                        ),
                        url: window.location.href
                    });
                },
                300
            );
        },
        true
    );
})();
"""


def attach_observer_to_page(
    page,
    workflow_id: int,
):
    """
    Attach GHOST listeners to one browser page/tab.
    """

    print(
        f"👻 WATCHING TAB → {page.url}"
    )

    def record_navigation(frame):
        if frame != page.main_frame:
            return

        url = frame.url

        if should_ignore_url(
            url
        ):
            return

        save_clean_action(
            workflow_id,
            Action(
                action_type="navigate",
                url=url,
            ),
        )

    page.on(
        "framenavigated",
        record_navigation,
    )

    try:
        page.expose_function(
            "ghostRecordAction",
            lambda data:
                handle_browser_action(
                    workflow_id,
                    data,
                ),
        )
    except Exception:
        pass

    try:
        page.add_init_script(
            OBSERVER_SCRIPT
        )
    except Exception:
        pass

    try:
        if not page.is_closed():
            page.evaluate(
                OBSERVER_SCRIPT
            )
    except Exception:
        pass


def observe_browser(
    workflow_id: int,
):
    print()
    print("👻 GHOST OBSERVER")
    print("----------------")
    print(
        "A browser will open."
    )
    print(
        "Use it normally."
    )
    print(
        "GHOST will now watch new tabs too."
    )
    print(
        "When finished, RETURN TO TERMINAL "
        "and press ENTER."
    )
    print(
        "Do not close the browser manually."
    )
    print()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False
        )

        context = browser.new_context()

        # ------------------------------------------
        # WATCH EVERY NEW TAB / PAGE
        # ------------------------------------------

        def handle_new_page(page):
            attach_observer_to_page(
                page,
                workflow_id,
            )

        context.on(
            "page",
            handle_new_page,
        )

        # Create the first page.
        page = context.new_page()

        attach_observer_to_page(
            page,
            workflow_id,
        )

        # Bing is currently useful for
        # research workflow testing.
        page.goto(
            "https://www.bing.com/"
        )

        input(
            "\n👻 Press ENTER here when your "
            "workflow is finished..."
        )

        try:
            open_pages = context.pages

            for open_page in open_pages:
                try:
                    if not open_page.is_closed():
                        open_page.wait_for_timeout(
                            250
                        )
                except Exception:
                    pass

        except Exception:
            pass

        try:
            context.close()
        except Exception:
            pass

        try:
            browser.close()
        except Exception:
            pass