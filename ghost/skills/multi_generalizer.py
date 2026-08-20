from urllib.parse import urlparse

from ghost.memory.database import get_actions
from ghost.models.skill import (
    Skill,
    SkillStep,
    SkillVariable,
)


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

        # Ignore low-value click noise.
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
                "/search" in action["url"].lower()
                or "?q=" in action["url"].lower()
                or "&q=" in action["url"].lower()
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

    results_id = search_results_action["id"]
    search_domain = get_domain(
        search_results_action["url"]
    )

    for action in actions:
        if action["id"] <= results_id:
            continue

        if action["action_type"] != "navigate":
            continue

        url = action["url"]

        if not url:
            continue

        domain = get_domain(url)

        if not domain:
            continue

        # Different domain means the workflow
        # continued beyond the search engine.
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

    start_id = search_results_action["id"]
    end_id = external_navigation["id"]

    clicks = [
        action
        for action in actions
        if action["action_type"] == "click"
        and start_id < action["id"] < end_id
        and action["target"]
    ]

    if not clicks:
        return None

    # Usually the final meaningful click before
    # leaving the search engine is the chosen result.
    return clicks[-1]


def analyze_demonstration(
    workflow_id,
    actions,
):
    input_action = find_meaningful_input(
        actions
    )

    start_navigation = find_starting_navigation(
        actions
    )

    search_results = find_search_results_navigation(
        actions,
        input_action,
    )

    external_navigation = find_external_navigation(
        actions,
        search_results,
    )

    result_click = find_result_click(
        actions,
        search_results,
        external_navigation,
    )

    return {
        "workflow_id": workflow_id,
        "actions": actions,
        "input": input_action,
        "start": start_navigation,
        "search_results": search_results,
        "result_click": result_click,
        "external_navigation": external_navigation,
    }


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
        dict.fromkeys(starting_urls)
    )

    steps = []

    if len(unique_starting_urls) == 1:
        steps.append(
            SkillStep(
                action_type="navigate",
                url=unique_starting_urls[0],
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
                example_value=example_values[0],
                description=(
                    "Search query identified "
                    "across demonstrations."
                ),
            )
        ],
        steps=steps,
    )


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
        dict.fromkeys(starting_urls)
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
        dict.fromkeys(external_domains)
    )

    steps = []

    if len(unique_starting_urls) == 1:
        steps.append(
            SkillStep(
                action_type="navigate",
                url=unique_starting_urls[0],
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

    print()
    print(
        "Observed external sources:"
    )

    for domain in unique_external_domains:
        print(
            f"- {domain}"
        )

    return Skill(
        name="research_topic",
        description=(
            "Search for a topic and open "
            "a relevant external source."
        ),
        variables=[
            SkillVariable(
                name="query",
                example_value=example_values[0],
                description=(
                    "Research topic identified "
                    "across demonstrations."
                ),
            )
        ],
        steps=steps,
    )


def learn_from_demonstrations(
    workflow_ids,
):
    demonstrations = [
        meaningful_actions(workflow_id)
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

    analyses = []

    for workflow_id, actions in zip(
        workflow_ids,
        demonstrations,
    ):
        signature = [
            action_signature(action)
            for action in actions
        ]

        print(
            f"Workflow #{workflow_id}: "
            f"{' → '.join(signature)}"
        )

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

    print()
    print("👻 PATTERN FOUND")
    print("----------------")
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
    print("Observed queries:")

    for value in example_values:
        print(
            f'- "{value}"'
        )

    # --------------------------------------------------
    # RESEARCH DETECTION
    # --------------------------------------------------

    all_open_external_source = all(
        analysis["external_navigation"]
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
        print()
        print(
            "Classification: research_topic"
        )

        return build_research_skill(
            analyses
        )

    # --------------------------------------------------
    # BASIC SEARCH
    # --------------------------------------------------

    print()
    print(
        "Classification: web_search"
    )

    return build_web_search_skill(
        analyses
    )