import re
from urllib.parse import urlparse

from ghost.ai.client import ai_client
from ghost.memory.database import get_actions
from ghost.models.skill import (
    Skill,
    SkillStep,
    SkillVariable,
)


# --------------------------------------------------
# DEMONSTRATION CLEANING
# --------------------------------------------------

def meaningful_actions(workflow_id: int):
    actions = get_actions(workflow_id)

    clean = []

    for action in actions:
        action_type = action["action_type"]
        value = action["value"]
        target = action["target"]

        # Ignore empty text input.
        if action_type == "input":
            if value is None or value.strip() == "":
                continue

        # Ignore obvious click noise.
        if action_type == "click":
            if target in {
                "img",
                "svg",
                "VERIFY",
            }:
                continue

        clean.append(action)

    return clean


def action_signature(action):
    return action["action_type"]


def clean_action_for_ai(action):
    """
    Convert sqlite3.Row into a plain dictionary
    containing only information useful to the LLM.
    """

    return {
        "action_type": action["action_type"],
        "target": action["target"],
        "value": action["value"],
        "url": action["url"],
    }


def build_ai_demonstrations(
    workflow_ids,
    demonstrations,
):
    result = []

    for workflow_id, actions in zip(
        workflow_ids,
        demonstrations,
    ):
        result.append(
            {
                "workflow_id": workflow_id,
                "actions": [
                    clean_action_for_ai(action)
                    for action in actions
                ],
            }
        )

    return result


# --------------------------------------------------
# VARIABLE NORMALIZATION
# --------------------------------------------------

def normalize_variable_reference(
    value,
    variable_names,
):
    """
    Convert variable formats produced by an LLM
    into GHOST's {{variable}} format.

    Examples:

    $topic_query
        ->
    {{topic_query}}

    topic_query
        ->
    {{topic_query}}

    {{topic_query}}
        ->
    {{topic_query}}
    """

    if value is None:
        return None

    if not isinstance(value, str):
        return value

    value = value.strip()

    # Already in GHOST format.
    match = re.fullmatch(
        r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}",
        value,
    )

    if match:
        return value

    # $variable format.
    match = re.fullmatch(
        r"\$([A-Za-z_][A-Za-z0-9_]*)",
        value,
    )

    if match:
        name = match.group(1)

        if name in variable_names:
            return "{{" + name + "}}"

    # Bare variable name.
    if value in variable_names:
        return "{{" + value + "}}"

    return value


# --------------------------------------------------
# AI RESULT → GHOST SKILL
# --------------------------------------------------

def skill_from_ai_analysis(
    analysis,
):
    skill_name = analysis.get(
        "skill_name"
    )

    description = analysis.get(
        "description"
    )

    raw_variables = analysis.get(
        "variables",
        [],
    )

    raw_steps = analysis.get(
        "steps",
        [],
    )

    if not skill_name:
        raise ValueError(
            "AI analysis did not provide "
            "a skill name."
        )

    if not description:
        raise ValueError(
            "AI analysis did not provide "
            "a skill description."
        )

    if not raw_steps:
        raise ValueError(
            "AI analysis did not provide "
            "any workflow steps."
        )

    variables = []

    for variable in raw_variables:
        name = variable.get(
            "name"
        )

        if not name:
            continue

        variables.append(
            SkillVariable(
                name=name,
                example_value=variable.get(
                    "example_value"
                ),
                description=variable.get(
                    "description"
                ),
            )
        )

    variable_names = {
        variable.name
        for variable in variables
    }

    steps = []

    for raw_step in raw_steps:
        action_type = raw_step.get(
            "action_type"
        )

        if not action_type:
            continue

        target = raw_step.get(
            "target"
        )

        value = normalize_variable_reference(
            raw_step.get(
                "value"
            ),
            variable_names,
        )

        url = raw_step.get(
            "url"
        )

        # If the AI represented navigation as:
        #
        # navigate
        # target=search_engine
        # value=Bing
        #
        # don't turn "Bing" into a literal value
        # that the browser runner cannot understand.
        #
        # The runner/provider architecture can choose
        # the actual search engine.
        if (
            action_type == "navigate"
            and target == "search_engine"
            and not url
        ):
            continue

        steps.append(
            SkillStep(
                action_type=action_type,
                target=target,
                value=value,
                url=url,
            )
        )

    if not steps:
        raise ValueError(
            "AI analysis produced no usable steps."
        )

    return Skill(
        name=skill_name,
        description=description,
        variables=variables,
        steps=steps,
    )


# --------------------------------------------------
# AI GENERALIZATION
# --------------------------------------------------

def try_ai_generalization(
    workflow_ids,
    demonstrations,
):
    if not ai_client.is_available():
        print()
        print(
            "👻 AI GENERALIZER → unavailable"
        )
        print(
            "👻 Using local rule-based fallback."
        )

        return None

    ai_demonstrations = (
        build_ai_demonstrations(
            workflow_ids,
            demonstrations,
        )
    )

    print()
    print(
        "🧠 GHOST AI → analyzing demonstrations"
    )
    print(
        "-------------------------------------"
    )

    try:
        analysis = (
            ai_client.analyze_demonstrations(
                ai_demonstrations
            )
        )

    except Exception as error:
        print(
            f"⚠️ AI workflow analysis failed: "
            f"{error}"
        )

        print(
            "👻 Using local rule-based fallback."
        )

        return None

    if not analysis:
        print(
            "⚠️ AI returned no workflow analysis."
        )

        print(
            "👻 Using local rule-based fallback."
        )

        return None

    try:
        skill = skill_from_ai_analysis(
            analysis
        )

    except Exception as error:
        print(
            f"⚠️ Could not convert AI analysis "
            f"into a GHOST skill: {error}"
        )

        print(
            "👻 Using local rule-based fallback."
        )

        return None

    confidence = analysis.get(
        "confidence",
        0.0,
    )

    intent = analysis.get(
        "intent",
        "Unknown",
    )

    optional_behavior = analysis.get(
        "optional_behavior",
        [],
    )

    print(
        "✅ AI workflow pattern detected."
    )

    print()
    print(
        f"Intent: {intent}"
    )

    print(
        f"Skill: {skill.name}"
    )

    print(
        f"Confidence: {confidence:.2f}"
    )

    if skill.variables:
        print()
        print(
            "Variables detected:"
        )

        for variable in skill.variables:
            print(
                f"- {variable.name} = "
                f'"{variable.example_value}"'
            )

    if optional_behavior:
        print()
        print(
            "Optional behavior ignored:"
        )

        for behavior in optional_behavior:
            print(
                f"- {behavior}"
            )

    print()
    print(
        "Semantic steps:"
    )

    for index, step in enumerate(
        skill.steps,
        start=1,
    ):
        print(
            f"{index}. "
            f"{step.action_type} "
            f"target={step.target} "
            f"value={step.value} "
            f"url={step.url}"
        )

    return skill


# --------------------------------------------------
# LOCAL FALLBACK HELPERS
# --------------------------------------------------

def find_meaningful_input(actions):
    return next(
        (
            action
            for action in actions
            if action["action_type"] == "input"
            and action["value"]
        ),
        None,
    )


def get_domain(url):
    if not url:
        return None

    parsed = urlparse(url)

    return parsed.netloc.lower()


def find_starting_navigation(actions):
    return next(
        (
            action
            for action in actions
            if action["action_type"] == "navigate"
        ),
        None,
    )


def find_search_results_navigation(
    actions,
    input_action,
):
    if input_action is None:
        return None

    input_id = input_action["id"]

    return next(
        (
            action
            for action in actions
            if action["id"] > input_id
            and action["action_type"] == "navigate"
            and action["url"]
            and (
                "/search"
                in action["url"].lower()
                or "?q="
                in action["url"].lower()
                or "&q="
                in action["url"].lower()
            )
        ),
        None,
    )


def find_external_navigation(
    actions,
    search_results_action,
):
    if search_results_action is None:
        return None

    results_id = (
        search_results_action["id"]
    )

    search_domain = get_domain(
        search_results_action["url"]
    )

    for action in actions:
        if action["id"] <= results_id:
            continue

        if (
            action["action_type"]
            != "navigate"
        ):
            continue

        url = action["url"]

        if not url:
            continue

        domain = get_domain(
            url
        )

        if not domain:
            continue

        if domain != search_domain:
            return action

    return None


def find_result_click(
    actions,
    search_results_action,
    external_navigation,
):
    if (
        search_results_action is None
        or external_navigation is None
    ):
        return None

    start_id = (
        search_results_action["id"]
    )

    end_id = (
        external_navigation["id"]
    )

    clicks = [
        action
        for action in actions
        if action["action_type"] == "click"
        and start_id
        < action["id"]
        < end_id
        and action["target"]
    ]

    if not clicks:
        return None

    return clicks[-1]


def analyze_demonstration(
    workflow_id,
    actions,
):
    input_action = (
        find_meaningful_input(
            actions
        )
    )

    start_navigation = (
        find_starting_navigation(
            actions
        )
    )

    search_results = (
        find_search_results_navigation(
            actions,
            input_action,
        )
    )

    external_navigation = (
        find_external_navigation(
            actions,
            search_results,
        )
    )

    result_click = (
        find_result_click(
            actions,
            search_results,
            external_navigation,
        )
    )

    return {
        "workflow_id": workflow_id,
        "actions": actions,
        "input": input_action,
        "start": start_navigation,
        "search_results": search_results,
        "result_click": result_click,
        "external_navigation": (
            external_navigation
        ),
    }


# --------------------------------------------------
# LOCAL WEB SEARCH SKILL
# --------------------------------------------------

def build_web_search_skill(
    analyses,
):
    example_values = [
        analysis["input"]["value"]
        for analysis in analyses
    ]

    starting_urls = [
        analysis["start"]["url"]
        for analysis in analyses
        if analysis["start"]
    ]

    unique_starting_urls = list(
        dict.fromkeys(
            starting_urls
        )
    )

    steps = []

    if len(
        unique_starting_urls
    ) == 1:
        steps.append(
            SkillStep(
                action_type="navigate",
                url=(
                    unique_starting_urls[0]
                ),
            )
        )

    steps.append(
        SkillStep(
            action_type="input",
            target="search_input",
            value="{{query}}",
        )
    )

    steps.append(
        SkillStep(
            action_type="submit",
            target="search_input",
        )
    )

    return Skill(
        name="web_search",
        description=(
            "Search the web using a "
            "user-provided query."
        ),
        variables=[
            SkillVariable(
                name="query",
                example_value=(
                    example_values[0]
                ),
                description=(
                    "Search query identified "
                    "across demonstrations."
                ),
            )
        ],
        steps=steps,
    )


# --------------------------------------------------
# LOCAL RESEARCH SKILL
# --------------------------------------------------

def build_research_skill(
    analyses,
):
    example_values = [
        analysis["input"]["value"]
        for analysis in analyses
    ]

    starting_urls = [
        analysis["start"]["url"]
        for analysis in analyses
        if analysis["start"]
    ]

    unique_starting_urls = list(
        dict.fromkeys(
            starting_urls
        )
    )

    external_domains = []

    for analysis in analyses:
        external = analysis[
            "external_navigation"
        ]

        if external:
            external_domains.append(
                get_domain(
                    external["url"]
                )
            )

    unique_external_domains = list(
        dict.fromkeys(
            external_domains
        )
    )

    steps = []

    if len(
        unique_starting_urls
    ) == 1:
        steps.append(
            SkillStep(
                action_type="navigate",
                url=(
                    unique_starting_urls[0]
                ),
            )
        )

    steps.append(
        SkillStep(
            action_type="input",
            target="search_input",
            value="{{query}}",
        )
    )

    steps.append(
        SkillStep(
            action_type="submit",
            target="search_input",
        )
    )

    steps.append(
        SkillStep(
            action_type="select",
            target="relevant_result",
        )
    )

    steps.append(
        SkillStep(
            action_type="open",
            target="external_source",
        )
    )

    steps.append(
        SkillStep(
            action_type="extract",
            target="useful_content",
        )
    )

    print()
    print(
        "Observed external sources:"
    )

    for domain in (
        unique_external_domains
    ):
        print(
            f"- {domain}"
        )

    return Skill(
        name="research_topic",
        description=(
            "Search for a topic, open a "
            "relevant external source, "
            "and extract useful content."
        ),
        variables=[
            SkillVariable(
                name="query",
                example_value=(
                    example_values[0]
                ),
                description=(
                    "Research topic identified "
                    "across demonstrations."
                ),
            )
        ],
        steps=steps,
    )


# --------------------------------------------------
# LOCAL RULE-BASED GENERALIZER
# --------------------------------------------------

def local_generalization(
    workflow_ids,
    demonstrations,
):
    print()
    print(
        "👻 LOCAL GENERALIZER"
    )
    print(
        "--------------------"
    )

    analyses = []

    for workflow_id, actions in zip(
        workflow_ids,
        demonstrations,
    ):
        analyses.append(
            analyze_demonstration(
                workflow_id,
                actions,
            )
        )

    if any(
        analysis["input"] is None
        for analysis in analyses
    ):
        raise ValueError(
            "Not every demonstration contains "
            "meaningful input."
        )

    if any(
        analysis["search_results"] is None
        for analysis in analyses
    ):
        raise ValueError(
            "Not every demonstration produced "
            "search results."
        )

    example_values = [
        analysis["input"]["value"]
        for analysis in analyses
    ]

    print(
        "- all demonstrations contain "
        "meaningful text input"
    )

    print(
        "- all demonstrations reach "
        "search results"
    )

    print(
        "- query values differ"
    )

    print()
    print(
        "Observed queries:"
    )

    for value in example_values:
        print(
            f'- "{value}"'
        )

    all_open_external_source = all(
        analysis[
            "external_navigation"
        ]
        is not None
        for analysis in analyses
    )

    all_choose_result = all(
        analysis["result_click"]
        is not None
        for analysis in analyses
    )

    if (
        all_open_external_source
        and all_choose_result
    ):
        print()
        print(
            "👻 HIGHER-LEVEL PATTERN DETECTED"
        )

        print(
            "--------------------------------"
        )

        print(
            "- search results are inspected"
        )

        print(
            "- a result is selected"
        )

        print(
            "- workflow continues to "
            "an external information source"
        )

        print(
            "- useful content should "
            "be extracted"
        )

        print()
        print(
            "Classification: research_topic"
        )

        return build_research_skill(
            analyses
        )

    print()
    print(
        "Classification: web_search"
    )

    return build_web_search_skill(
        analyses
    )


# --------------------------------------------------
# MAIN GENERALIZATION ENTRY POINT
# --------------------------------------------------

def learn_from_demonstrations(
    workflow_ids,
):
    demonstrations = [
        meaningful_actions(
            workflow_id
        )
        for workflow_id in workflow_ids
    ]

    if not demonstrations:
        raise ValueError(
            "No demonstrations provided."
        )

    print()
    print(
        "👻 COMPARING DEMONSTRATIONS"
    )
    print(
        "---------------------------"
    )

    for workflow_id, actions in zip(
        workflow_ids,
        demonstrations,
    ):
        signature = [
            action_signature(
                action
            )
            for action in actions
        ]

        print(
            f"Workflow #{workflow_id}: "
            f"{' → '.join(signature)}"
        )

    # --------------------------------------------------
    # AI-FIRST GENERALIZATION
    # --------------------------------------------------

    ai_skill = try_ai_generalization(
        workflow_ids,
        demonstrations,
    )

    if ai_skill is not None:
        return ai_skill

    # --------------------------------------------------
    # LOCAL FALLBACK
    # --------------------------------------------------

    return local_generalization(
        workflow_ids,
        demonstrations,
    )