import json

from openai import OpenAI


class OpenAIProvider:
    def __init__(
        self,
        model="gpt-5.6-luna",
    ):
        self.model = model
        self.client = OpenAI()

    # --------------------------------------------------
    # RESEARCH SUMMARIZATION
    # --------------------------------------------------

    def summarize(
        self,
        query,
        title,
        content,
    ):
        content_preview = content[:12000]

        instructions = """
You are the reasoning layer inside an AI software
agent named GHOST.

The user asked GHOST to research a topic.
GHOST found and extracted content from a webpage.

Produce a concise useful answer based ONLY on
the supplied webpage content.

Return ONLY valid JSON:

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
- Ignore navigation, cookie banners, citation clutter,
  and unrelated page content.
- Do not invent facts.
- Prefer plain English.
- key_terms must be meaningful concepts.
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

    # --------------------------------------------------
    # WORKFLOW GENERALIZATION
    # --------------------------------------------------

    def analyze_demonstrations(
        self,
        demonstrations,
    ):
        instructions = """
You are the workflow-learning brain inside GHOST.

GHOST learns browser workflows by observing several
human demonstrations.

Your job is to infer the reusable behavior shared
across ALL demonstrations.

IMPORTANT:
You must output instructions using GHOST's semantic
workflow language.

Return ONLY valid JSON:

{
  "skill_name": "snake_case_name",
  "description": "One sentence description.",
  "intent": "What the user is trying to accomplish.",
  "variables": [
    {
      "name": "variable_name",
      "example_value": "example",
      "description": "Meaning of the variable."
    }
  ],
  "steps": [
    {
      "action_type": "action",
      "target": "semantic_target",
      "value": null,
      "url": null
    }
  ],
  "optional_behavior": [],
  "confidence": 0.0
}

--------------------------------------------------
GHOST LANGUAGE
--------------------------------------------------

Allowed action types:

navigate
input
submit
select
open
extract
verify
click

Preferred semantic targets:

search_input
relevant_result
external_source
useful_content

Variables MUST use this exact syntax:

{{variable_name}}

Never use:

$variable
{variable}
<variable>

--------------------------------------------------
VARIABLE RULES
--------------------------------------------------

Only create a variable when something meaningful
changes between demonstrations.

For example:

Demo:
"what is deep learning"

Demo:
"what is computer vision"

The changing user input should become ONE variable:

{
  "name": "query",
  "example_value": "what is deep learning"
}

The workflow step should then contain:

"value": "{{query}}"

Do NOT split that into:

"what is {{topic}}"

unless the demonstrations prove that only the
topic portion changes while the surrounding phrase
is an intentional fixed template.

Do NOT treat the search engine as a variable simply
because Bing was used.

--------------------------------------------------
KNOWN GHOST SKILLS
--------------------------------------------------

If the user simply performs a web search:

skill_name must be:

web_search

Typical semantic workflow:

input search_input {{query}}
submit search_input

If the user searches for information, selects a
result, opens an external information source, and
uses that source for research:

skill_name must be:

research_topic

Typical semantic workflow:

input search_input {{query}}
submit search_input
select relevant_result
open external_source
extract useful_content

Do NOT add a navigate step for a search engine
homepage unless the exact URL itself is essential
to the learned task.

GHOST's provider system handles search-engine
selection separately.

--------------------------------------------------
IMPORTANT GENERALIZATION RULES
--------------------------------------------------

- Infer intent, not literal mouse history.
- Ignore exact scroll distances.
- Ignore accidental clicks.
- Ignore duplicate navigation events caused by redirects.
- Do not hardcode article titles.
- Do not hardcode external domains unless required.
- Search-result selection should use relevant_result.
- Opening the chosen source should use external_source.
- Reading research content should use useful_content.
- Optional behaviors belong in optional_behavior,
  not required steps.
- confidence must be between 0.0 and 1.0.
- Do not invent unsupported workflow behavior.
"""

        demonstrations_json = json.dumps(
            demonstrations,
            indent=2,
        )

        prompt = f"""
GHOST OBSERVED THESE DEMONSTRATIONS:

{demonstrations_json}

Determine the reusable workflow shared by them.
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
                "OpenAI returned invalid workflow JSON."
            ) from error

        required_fields = {
            "skill_name",
            "description",
            "intent",
            "variables",
            "steps",
            "optional_behavior",
            "confidence",
        }

        missing = (
            required_fields
            - set(
                result.keys()
            )
        )

        if missing:
            raise ValueError(
                "OpenAI workflow analysis "
                "is missing: "
                + ", ".join(
                    sorted(missing)
                )
            )

        confidence = result.get(
            "confidence"
        )

        if not isinstance(
            confidence,
            (int, float),
        ):
            raise ValueError(
                "Workflow confidence "
                "must be numeric."
            )

        if not (
            0.0
            <= confidence
            <= 1.0
        ):
            raise ValueError(
                "Workflow confidence must "
                "be between 0.0 and 1.0."
            )

        return result

    # --------------------------------------------------
    # SKILL ROUTING
    # --------------------------------------------------

    def route_request(
        self,
        user_request,
        skills,
    ):
        instructions = """
You are the routing brain inside an AI software
agent named GHOST.

GHOST has a collection of reusable skills.

Your job is to understand the user's request and
choose the single best existing skill.

You MUST choose only from the skills supplied to
you.

Return ONLY valid JSON:

{
  "skill": "skill_name",
  "confidence": 0.0,
  "variables": {},
  "missing_variables": [],
  "reason": "Short explanation of why this skill fits."
}

--------------------------------------------------
ROUTING RULES
--------------------------------------------------

- Choose exactly one supplied skill.
- Never invent a skill.
- confidence must be between 0.0 and 1.0.
- Extract variables from the user's request.
- Never invent missing information.
- Variable names must exactly match the selected
  skill's declared variables.
- If a required value is absent, do not invent it.
- Put its name in missing_variables instead.

--------------------------------------------------
RESEARCH
--------------------------------------------------

For informational questions or requests to explain,
learn about, investigate, or research a topic,
prefer the most appropriate research skill.

The complete user's question may be used as the
query variable.

Examples:

"What is reinforcement learning?"

should generally route to a research skill with:

{
  "query": "What is reinforcement learning?"
}

--------------------------------------------------
PROJECT VERIFICATION
--------------------------------------------------

Requests about checking whether a software project
is healthy, compiling, linting, building, testing,
or verifying a local project should use an
appropriate project verification skill when one
exists.

Only extract project_path when the user actually
provides a filesystem path.

Example:

"Check if ~/Desktop/ghost is healthy"

may produce:

{
  "project_path": "~/Desktop/ghost"
}

But:

"Check if my project is healthy"

does NOT contain a filesystem path.

Do not invent one.

--------------------------------------------------
IMPORTANT
--------------------------------------------------

GHOST already knows how to execute these skills.

You are selecting a skill and extracting its
inputs.

You are NOT executing the skill yourself.
"""

        skills_json = json.dumps(
            skills,
            indent=2,
        )

        prompt = f"""
AVAILABLE GHOST SKILLS:

{skills_json}

USER REQUEST:

{user_request}

Choose the best GHOST skill.
"""

        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
        )

        raw_text = (
            response.output_text.strip()
        )

        try:
            result = json.loads(
                raw_text
            )

        except json.JSONDecodeError as error:
            raise ValueError(
                "OpenAI returned invalid "
                "routing JSON."
            ) from error

        required_fields = {
            "skill",
            "confidence",
            "variables",
            "missing_variables",
            "reason",
        }

        missing = (
            required_fields
            - set(
                result.keys()
            )
        )

        if missing:
            raise ValueError(
                "OpenAI routing response "
                "is missing: "
                + ", ".join(
                    sorted(missing)
                )
            )

        confidence = result.get(
            "confidence"
        )

        if not isinstance(
            confidence,
            (int, float),
        ):
            raise ValueError(
                "Routing confidence "
                "must be numeric."
            )

        if not (
            0.0
            <= confidence
            <= 1.0
        ):
            raise ValueError(
                "Routing confidence must "
                "be between 0.0 and 1.0."
            )

        if not isinstance(
            result.get("variables"),
            dict,
        ):
            raise ValueError(
                "Routing variables must "
                "be an object."
            )

        if not isinstance(
            result.get(
                "missing_variables"
            ),
            list,
        ):
            raise ValueError(
                "missing_variables must "
                "be a list."
            )

        return result