import json

from openai import OpenAI


class OpenAIProvider:
    def __init__(
        self,
        model="gpt-5.6-luna",
    ):
        self.model = model
        self.client = OpenAI()

    def summarize(
        self,
        query,
        title,
        content,
    ):
        # Limit how much webpage text we send.
        # This keeps development requests smaller
        # and cheaper.
        content_preview = content[:12000]

        instructions = """
You are the reasoning layer inside an AI software
agent named GHOST.

The user asked GHOST to research a topic.
GHOST found and extracted content from a webpage.

Produce a concise, useful research result based
ONLY on the supplied webpage content.

Return ONLY valid JSON in exactly this shape:

{
  "summary": "3 to 5 clear sentences",
  "key_terms": [
    "term 1",
    "term 2",
    "term 3",
    "term 4",
    "term 5"
  ]
}

Rules:
- Answer the user's query directly.
- Ignore navigation menus, cookie banners,
  citation clutter, and unrelated page content.
- Do not invent facts.
- Prefer plain English.
- Keep the summary concise.
- key_terms should contain useful concepts,
  not random high-frequency words.
"""

        prompt = f"""
USER QUERY:
{query}

PAGE TITLE:
{title}

PAGE CONTENT:
{content_preview}
"""

        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
        )

        raw_text = response.output_text.strip()

        try:
            result = json.loads(
                raw_text
            )

        except json.JSONDecodeError as error:
            raise ValueError(
                "OpenAI returned invalid JSON."
            ) from error

        summary = result.get(
            "summary"
        )

        key_terms = result.get(
            "key_terms",
            [],
        )

        if not summary:
            raise ValueError(
                "OpenAI response contained no summary."
            )

        return {
            "summary": summary,
            "key_terms": key_terms,
        }

    def analyze_demonstrations(
        self,
        demonstrations,
    ):
        raise NotImplementedError(
            "AI workflow generalization "
            "will be added next."
        )