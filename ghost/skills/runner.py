from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from ghost.skills.storage import load_skill
from ghost.skills.providers import get_provider
from ghost.skills.summarizer import (
    summarize_content,
    extract_key_terms,
    is_useful_source,
)


# --------------------------------------------------
# BASIC HELPERS
# --------------------------------------------------

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


# --------------------------------------------------
# TARGET RESOLUTION
# --------------------------------------------------

def resolve_semantic_target(page, target):
    if target != "search_input":
        return None

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


# --------------------------------------------------
# SEARCH RESULTS
# --------------------------------------------------

def get_result_candidates(page):
    """
    Return likely search-result links.

    Bing result links are preferred first,
    followed by generic result structures.
    """

    candidate_groups = [
        page.locator(
            "li.b_algo h2 a"
        ),
        page.locator(
            "main h2 a"
        ),
        page.locator(
            "main h3 a"
        ),
    ]

    results = []
    seen_text = set()

    for group in candidate_groups:
        try:
            count = group.count()

        except Exception:
            continue

        for index in range(
            min(count, 20)
        ):
            locator = group.nth(
                index
            )

            try:
                if not locator.is_visible():
                    continue

                text = (
                    locator.inner_text()
                    .strip()
                )

                href = locator.get_attribute(
                    "href"
                )

                if not text:
                    continue

                if len(text) < 5:
                    continue

                if not href:
                    continue

                key = text.lower()

                if key in seen_text:
                    continue

                seen_text.add(
                    key
                )

                results.append(
                    {
                        "text": text,
                        "href": href,
                    }
                )

            except Exception:
                continue

    return results


def print_result_choice(
    index,
    result,
):
    print()
    print(
        f"👻 TRYING RESULT #{index + 1}"
    )

    print(
        f"👻 RESULT → "
        f"{result['text'][:120]}"
    )


# --------------------------------------------------
# OPEN RESULT
# --------------------------------------------------

def open_result(
    page,
    result,
):
    href = result.get(
        "href"
    )

    if not href:
        return False

    print(
        "👻 OPEN → selected result"
    )

    try:
        page.goto(
            href,
            wait_until="domcontentloaded",
            timeout=15000,
        )

    except Exception:
        # A timeout does not always mean the
        # destination failed to load.
        pass

    try:
        page.wait_for_load_state(
            "domcontentloaded",
            timeout=7000,
        )

    except Exception:
        pass

    page.wait_for_timeout(
        1250
    )

    print(
        f"👻 NAVIGATED → {page.url}"
    )

    return True


# --------------------------------------------------
# CONTENT EXTRACTION
# --------------------------------------------------

def clean_page_text(text):
    if not text:
        return ""

    lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        lines.append(
            line
        )

    return "\n".join(
        lines
    )


def extract_page_content(
    page,
    quiet=False,
):
    if not quiet:
        print()
        print(
            "👻 EXTRACTING USEFUL CONTENT"
        )
        print(
            "----------------------------"
        )

    try:
        page.wait_for_load_state(
            "domcontentloaded",
            timeout=5000,
        )

    except Exception:
        pass

    page.wait_for_timeout(
        500
    )

    try:
        title = (
            page.title()
            .strip()
        )

    except Exception:
        title = ""

    if not title:
        title = "Unknown title"

    content = ""

    candidates = [
        page.locator(
            "article"
        ),
        page.locator(
            "main"
        ),
        page.locator(
            '[role="main"]'
        ),
    ]

    for locator in candidates:
        try:
            if locator.count() == 0:
                continue

            text = locator.first.inner_text(
                timeout=5000
            )

            text = clean_page_text(
                text
            )

            if len(text) >= 250:
                content = text
                break

        except Exception:
            continue

    if not content:
        try:
            text = page.locator(
                "body"
            ).inner_text(
                timeout=5000
            )

            content = clean_page_text(
                text
            )

        except Exception:
            content = ""

    if not content:
        if not quiet:
            print(
                "❌ Could not extract page content."
            )

        return None

    if not quiet:
        print(
            "✅ Page content extracted."
        )

    return {
        "title": title,
        "url": page.url,
        "domain": get_domain(
            page.url
        ),
        "content": content,
    }


# --------------------------------------------------
# SOURCE QUALITY
# --------------------------------------------------

def check_source_quality(
    extracted_content,
    query,
):
    if extracted_content is None:
        return (
            False,
            "no content could be extracted",
        )

    title = extracted_content.get(
        "title",
        "",
    )

    content = extracted_content.get(
        "content",
        "",
    )

    useful, reason = is_useful_source(
        title,
        content,
        query=query,
    )

    return (
        useful,
        reason,
    )


# --------------------------------------------------
# RESEARCH RETRY LOOP
# --------------------------------------------------

def find_useful_research_source(
    page,
    query,
    max_attempts=5,
):
    """
    Try search results one by one until
    GHOST finds a source that passes
    quality checks.
    """

    results_url = page.url

    results = get_result_candidates(
        page
    )

    if not results:
        print(
            "❌ No search results found."
        )

        return (
            page,
            None,
        )

    attempts = min(
        len(results),
        max_attempts,
    )

    print()
    print(
        f"👻 FOUND {len(results)} "
        f"POSSIBLE RESULTS"
    )

    for index in range(
        attempts
    ):
        result = results[
            index
        ]

        # Return to search results before
        # each new attempt.
        if page.url != results_url:
            try:
                page.goto(
                    results_url,
                    wait_until="domcontentloaded",
                    timeout=10000,
                )

            except Exception:
                pass

            page.wait_for_timeout(
                500
            )

        print_result_choice(
            index,
            result,
        )

        opened = open_result(
            page,
            result,
        )

        if not opened:
            print(
                "⚠️ Result could not be opened."
            )

            continue

        extracted = extract_page_content(
            page,
            quiet=True,
        )

        useful, reason = (
            check_source_quality(
                extracted,
                query,
            )
        )

        if useful:
            print(
                "✅ SOURCE ACCEPTED"
            )

            print(
                f"👻 QUALITY → {reason}"
            )

            print(
                f"👻 SOURCE → {page.url}"
            )

            return (
                page,
                extracted,
            )

        print(
            "⚠️ SOURCE REJECTED"
        )

        print(
            f"👻 REASON → {reason}"
        )

        print(
            "👻 Trying another result..."
        )

    print()
    print(
        "❌ GHOST could not find a "
        "useful source."
    )

    return (
        page,
        None,
    )


# --------------------------------------------------
# SUMMARIZATION
# --------------------------------------------------

def build_research_result(
    extracted_content,
    query,
):
    if extracted_content is None:
        return None

    print()
    print(
        "👻 SUMMARIZING CONTENT"
    )
    print(
        "----------------------"
    )

    content = extracted_content.get(
        "content",
        "",
    )

    summary = summarize_content(
        content,
        query=query,
        max_sentences=5,
    )

    key_terms = extract_key_terms(
        content,
        limit=6,
    )

    if not summary:
        print(
            "❌ Could not generate summary."
        )

        return None

    result = {
        **extracted_content,
        "query": query,
        "summary": summary,
        "key_terms": key_terms,
    }

    print(
        "✅ Summary generated."
    )

    print()
    print(
        "👻 GHOST RESEARCH RESULT"
    )
    print(
        "------------------------"
    )

    print(
        f"Topic: {query}"
    )

    print(
        f"Title: {result['title']}"
    )

    print(
        f"Source: {result['domain']}"
    )

    print(
        f"URL: {result['url']}"
    )

    print()
    print(
        "SUMMARY"
    )
    print(
        "-------"
    )

    print(
        result["summary"]
    )

    print()
    print(
        "KEY TERMS"
    )
    print(
        "---------"
    )

    for term in result[
        "key_terms"
    ]:
        print(
            f"- {term}"
        )

    return result


# --------------------------------------------------
# VERIFICATION
# --------------------------------------------------

def verify_web_search(page):
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
                    f'👻 TYPE → {target}: "{value}"'
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
                if (
                    target == "relevant_result"
                    and skill.name
                    != "research_topic"
                ):
                    print(
                        "👻 SELECT → relevant result"
                    )

            # ----------------------------------
            # OPEN
            # ----------------------------------

            elif step.action_type == "open":
                if (
                    target == "external_source"
                    and skill.name
                    == "research_topic"
                ):
                    page, extracted = (
                        find_useful_research_source(
                            page,
                            variables.get(
                                "query"
                            ),
                            max_attempts=5,
                        )
                    )

                    if extracted is not None:
                        research_result = (
                            build_research_result(
                                extracted,
                                variables.get(
                                    "query"
                                ),
                            )
                        )

            # ----------------------------------
            # EXTRACT
            # ----------------------------------

            elif step.action_type == "extract":
                # research_topic already performs
                # extraction during its source-quality
                # retry loop.
                if (
                    target == "useful_content"
                    and research_result is None
                ):
                    print(
                        "⚠️ No accepted research "
                        "source available to extract."
                    )

            # ----------------------------------
            # LEGACY CLICK
            # ----------------------------------

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
                        f"⚠️ Could not find "
                        f"click target: {target}"
                    )

                    continue

                locator.first.click()

                page.wait_for_timeout(
                    750
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