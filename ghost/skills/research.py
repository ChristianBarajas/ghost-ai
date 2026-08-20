from urllib.parse import urlparse

from ghost.ai.client import ai_client
from ghost.skills.summarizer import (
    summarize_content,
    extract_key_terms,
    is_useful_source,
)


# --------------------------------------------------
# BASIC HELPERS
# --------------------------------------------------

def get_domain(url):
    if not url:
        return None

    return urlparse(url).netloc.lower()


# --------------------------------------------------
# SEARCH RESULTS
# --------------------------------------------------

def collect_results_from_selector(
    page,
    selector,
    results,
    seen,
):
    try:
        group = page.locator(
            selector
        )

        count = group.count()

    except Exception:
        return

    for index in range(
        min(count, 25)
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

            key = (
                text.lower(),
                href,
            )

            if key in seen:
                continue

            seen.add(
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


def get_result_candidates(page):
    """
    Find likely search-result links.

    Bing changes its markup occasionally,
    so GHOST checks several result patterns.
    """

    selectors = [
        "#b_results li.b_algo h2 a",
        "ol#b_results li.b_algo h2 a",
        "li.b_algo h2 a",
        "#b_results h2 a",
        "main li h2 a",
        "main h2 a",
        "main h3 a",
    ]

    results = []
    seen = set()

    for selector in selectors:
        collect_results_from_selector(
            page,
            selector,
            results,
            seen,
        )

    return results


def wait_for_result_candidates(
    page,
    timeout_ms=10000,
):
    """
    Search pages often render results after the
    first navigation event.

    Instead of checking once, GHOST waits and
    retries until results appear.
    """

    print(
        "👻 RESOLVE → waiting for search results"
    )

    elapsed = 0
    interval = 500

    while elapsed < timeout_ms:
        results = get_result_candidates(
            page
        )

        if results:
            print(
                f"✅ RESOLVE → found "
                f"{len(results)} search results"
            )

            return results

        page.wait_for_timeout(
            interval
        )

        elapsed += interval

    print(
        "❌ RESOLVE → search results "
        "did not appear"
    )

    return []


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
        # A timeout does not necessarily mean
        # the page failed. Redirect chains can
        # trigger Playwright timeouts.
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
                "❌ Could not extract "
                "page content."
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
    Find search results, then try them until
    one produces useful research content.
    """

    results_url = page.url

    # NEW:
    # Wait for Bing's rendered results instead
    # of checking the DOM immediately.
    results = wait_for_result_candidates(
        page,
        timeout_ms=10000,
    )

    if not results:
        print()
        print(
            "❌ No search results found."
        )

        print(
            f"Current page: {page.url}"
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

        # Return to results before trying
        # another source.
        if page.url != results_url:
            try:
                page.goto(
                    results_url,
                    wait_until="domcontentloaded",
                    timeout=10000,
                )

            except Exception:
                pass

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
                "⚠️ Result could not "
                "be opened."
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
        "❌ GHOST could not find "
        "a useful source."
    )

    return (
        page,
        None,
    )


# --------------------------------------------------
# RESULT BUILDING
# --------------------------------------------------

def build_research_result(
    extracted_content,
    query,
):
    if extracted_content is None:
        return None

    content = extracted_content.get(
        "content",
        "",
    )

    title = extracted_content.get(
        "title",
        "",
    )

    # --------------------------------------------------
    # AI FIRST
    # --------------------------------------------------

    if ai_client.is_available():
        print()
        print(
            "🧠 GHOST AI → analyzing research"
        )

        try:
            ai_result = ai_client.summarize(
                query=query,
                title=title,
                content=content,
            )

        except Exception as error:
            print(
                f"⚠️ AI summarization failed: "
                f"{error}"
            )

            ai_result = None

        if ai_result:
            summary = ai_result.get(
                "summary"
            )

            key_terms = ai_result.get(
                "key_terms",
                [],
            )

            if summary:
                print(
                    "✅ AI summary generated."
                )

                return {
                    **extracted_content,
                    "query": query,
                    "summary": summary,
                    "key_terms": key_terms,
                    "summary_source": "ai",
                }

    # --------------------------------------------------
    # LOCAL FALLBACK
    # --------------------------------------------------

    print()
    print(
        "👻 LOCAL FALLBACK → "
        "summarizing content"
    )
    print(
        "--------------------------------------"
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

    print(
        "✅ Local summary generated."
    )

    return {
        **extracted_content,
        "query": query,
        "summary": summary,
        "key_terms": key_terms,
        "summary_source": "local",
    }


# --------------------------------------------------
# PRINT RESEARCH RESULT
# --------------------------------------------------

def print_research_result(
    result,
):
    if result is None:
        return

    print()
    print(
        "👻 GHOST RESEARCH RESULT"
    )
    print(
        "------------------------"
    )

    print(
        f"Topic: {result['query']}"
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

    print(
        f"Summary engine: "
        f"{result.get('summary_source', 'unknown')}"
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

    for term in result.get(
        "key_terms",
        [],
    ):
        print(
            f"- {term}"
        )