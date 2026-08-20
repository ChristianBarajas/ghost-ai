import re
from collections import Counter


STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "if",
    "then",
    "than",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "as",
    "at",
    "by",
    "from",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "it",
    "its",
    "this",
    "that",
    "these",
    "those",
    "into",
    "about",
    "through",
    "which",
    "who",
    "what",
    "when",
    "where",
    "how",
    "can",
    "may",
    "also",
    "such",
}


ERROR_PHRASES = {
    "page you requested cannot be displayed",
    "page not found",
    "404 not found",
    "access denied",
    "request blocked",
    "something went wrong",
    "service unavailable",
    "temporarily unavailable",
    "enable javascript",
}


JUNK_PHRASES = {
    "about cookies on this site",
    "privacy statement",
    "cookie preferences",
    "do not sell or share my personal information",
    "accept all cookies",
    "manage cookies",
}


def clean_content(text):
    if not text:
        return ""

    lines = []

    ignored_lines = {
        "article",
        "talk",
        "read",
        "edit",
        "view history",
        "tools",
        "appearance",
    }

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.lower() in ignored_lines:
            continue

        if len(line) < 20:
            continue

        lines.append(
            line
        )

    return " ".join(
        lines
    )


def tokenize(text):
    return re.findall(
        r"\b[a-zA-Z]{3,}\b",
        text.lower(),
    )


def meaningful_query_words(query):
    return [
        word
        for word in tokenize(
            query or ""
        )
        if word not in STOP_WORDS
    ]


def query_relevance_score(
    title,
    content,
    query,
):
    query_words = meaningful_query_words(
        query
    )

    if not query_words:
        return 1.0

    title_words = set(
        tokenize(
            title or ""
        )
    )

    content_words = set(
        tokenize(
            (content or "")[:12000]
        )
    )

    matched_words = set()

    for word in query_words:
        if (
            word in title_words
            or word in content_words
        ):
            matched_words.add(
                word
            )

    return (
        len(matched_words)
        / len(set(query_words))
    )


def is_useful_source(
    title,
    content,
    query=None,
):
    title_lower = (
        title or ""
    ).lower()

    content_lower = (
        content or ""
    ).lower()

    combined = (
        title_lower
        + " "
        + content_lower[:5000]
    )

    # Reject obvious error pages.
    for phrase in ERROR_PHRASES:
        if phrase in combined:
            return (
                False,
                f"error page detected: {phrase}",
            )

    cleaned = clean_content(
        content
    )

    if len(cleaned) < 300:
        return (
            False,
            "not enough readable content",
        )

    # Reject pages dominated by cookie/privacy text.
    junk_hits = sum(
        1
        for phrase in JUNK_PHRASES
        if phrase in combined
    )

    if junk_hits >= 2:
        return (
            False,
            "page appears dominated by "
            "cookie/privacy content",
        )

    # --------------------------------------------------
    # QUERY RELEVANCE
    # --------------------------------------------------

    relevance = query_relevance_score(
        title,
        cleaned,
        query,
    )

    # Require most meaningful query terms to
    # appear somewhere in the page.
    #
    # Example:
    # "artificial general intelligence"
    #
    # A dictionary page containing only
    # "artificial" should fail.
    if relevance < 0.67:
        return (
            False,
            "source is not relevant enough "
            f"to the full query "
            f"(relevance={relevance:.2f})",
        )

    # Stronger title check for multi-word topics.
    query_words = meaningful_query_words(
        query
    )

    title_words = set(
        tokenize(
            title or ""
        )
    )

    if len(query_words) >= 2:
        title_matches = sum(
            1
            for word in set(query_words)
            if word in title_words
        )

        # If the title matches none or only one
        # important word, require extremely strong
        # body relevance.
        if (
            title_matches <= 1
            and relevance < 0.90
        ):
            return (
                False,
                "page title does not appear "
                "specific enough to the query",
            )

    return (
        True,
        f"source looks useful "
        f"(relevance={relevance:.2f})",
    )


def split_sentences(text):
    return [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+",
            text,
        )
        if len(
            sentence.strip()
        ) > 40
    ]


def summarize_content(
    text,
    query=None,
    max_sentences=5,
):
    cleaned = clean_content(
        text
    )

    if not cleaned:
        return None

    sentences = split_sentences(
        cleaned
    )

    if not sentences:
        return None

    words = [
        word
        for word in tokenize(
            cleaned
        )
        if word not in STOP_WORDS
    ]

    frequencies = Counter(
        words
    )

    query_words = set(
        meaningful_query_words(
            query
        )
    )

    scored_sentences = []

    for index, sentence in enumerate(
        sentences
    ):
        sentence_words = tokenize(
            sentence
        )

        score = sum(
            frequencies.get(
                word,
                0,
            )
            for word in sentence_words
        )

        for word in sentence_words:
            if word in query_words:
                score += 10

        if index < 8:
            score += 5

        scored_sentences.append(
            (
                score,
                index,
                sentence,
            )
        )

    best = sorted(
        scored_sentences,
        key=lambda item: item[0],
        reverse=True,
    )[:max_sentences]

    best = sorted(
        best,
        key=lambda item: item[1],
    )

    return " ".join(
        sentence
        for _, _, sentence in best
    )


def extract_key_terms(
    text,
    limit=6,
):
    cleaned = clean_content(
        text
    )

    words = [
        word
        for word in tokenize(
            cleaned
        )
        if word not in STOP_WORDS
    ]

    counts = Counter(
        words
    )

    return [
        word
        for word, _ in counts.most_common(
            limit
        )
    ]