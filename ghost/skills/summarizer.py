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

        lines.append(line)

    return " ".join(lines)


def tokenize(text):
    return re.findall(
        r"\b[a-zA-Z]{3,}\b",
        text.lower(),
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
        + content_lower[:4000]
    )

    # Reject obvious error pages.
    for phrase in ERROR_PHRASES:
        if phrase in combined:
            return False, (
                f"error page detected: {phrase}"
            )

    cleaned = clean_content(
        content
    )

    if len(cleaned) < 300:
        return False, (
            "not enough readable content"
        )

    # Detect pages dominated by cookie/privacy text.
    junk_hits = sum(
        1
        for phrase in JUNK_PHRASES
        if phrase in combined
    )

    if junk_hits >= 2:
        return False, (
            "page appears dominated by "
            "cookie/privacy content"
        )

    # Check whether the page has at least some
    # vocabulary related to the user's query.
    query_words = {
        word
        for word in tokenize(
            query or ""
        )
        if word not in STOP_WORDS
    }

    content_words = set(
        tokenize(
            cleaned[:8000]
        )
    )

    if query_words:
        overlap = (
            query_words
            & content_words
        )

        if not overlap:
            return False, (
                "content does not appear "
                "related to the query"
            )

    return True, "source looks useful"


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
        tokenize(
            query or ""
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