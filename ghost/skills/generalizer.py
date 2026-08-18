from typing import Optional
from urllib.parse import urlparse

from ghost.memory.database import get_actions
from ghost.models.skill import (
    Skill,
    SkillStep,
    SkillVariable,
)


def is_noise(action) -> bool:
    action_type = action["action_type"]
    target = action["target"]
    value = action["value"]

    # Ignore empty input events.
    if action_type == "input":
        if value is None or value.strip() == "":
            return True

    # Ignore low-value browser elements.
    if action_type == "click" and target in {
        "img",
        "svg",
        "VERIFY",
    }:
        return True

    return False


def simplify_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None

    parsed = urlparse(url)

    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def detect_search_workflow(actions) -> bool:
    """
    V1 heuristic.

    If the workflow contains a text input followed by a click
    whose target looks like a search/submit control, treat it
    as a search workflow.
    """

    has_input = any(
        action["action_type"] == "input"
        and action["value"]
        for action in actions
    )

    has_search_click = any(
        action["action_type"] == "click"
        and action["target"]
        and "search" in action["target"].lower()
        for action in actions
    )

    return has_input and has_search_click


def generalize_search_workflow(actions) -> Skill:
    steps = []
    variables = []

    first_navigation = next(
        (
            action
            for action in actions
            if action["action_type"] == "navigate"
        ),
        None,
    )

    if first_navigation:
        steps.append(
            SkillStep(
                action_type="navigate",
                url=simplify_url(
                    first_navigation["url"]
                ),
            )
        )

    # Find the meaningful text input.
    input_action = next(
        (
            action
            for action in actions
            if action["action_type"] == "input"
            and action["value"]
        ),
        None,
    )

    if input_action:
        variables.append(
            SkillVariable(
                name="query",
                example_value=input_action["value"],
                description="Search query provided by the user.",
            )
        )

        steps.append(
            SkillStep(
                action_type="input",
                target=input_action["target"],
                value="{{query}}",
            )
        )

    # Find the submit/search click that happens after input.
    if input_action:
        input_id = input_action["id"]

        search_click = next(
            (
                action
                for action in actions
                if action["id"] > input_id
                and action["action_type"] == "click"
                and action["target"]
                and "search" in action["target"].lower()
            ),
            None,
        )

        if search_click:
            steps.append(
                SkillStep(
                    action_type="click",
                    target=search_click["target"],
                )
            )

    return Skill(
        name="web_search",
        description="Search the web using a user-provided query.",
        variables=variables,
        steps=steps,
    )


def generalize_generic_workflow(actions) -> Skill:
    steps = []
    variables = []

    seen_navigation = False

    for action in actions:
        action_type = action["action_type"]
        target = action["target"]
        value = action["value"]
        url = action["url"]

        if action_type == "navigate":
            if seen_navigation:
                continue

            seen_navigation = True

            steps.append(
                SkillStep(
                    action_type="navigate",
                    url=simplify_url(url),
                )
            )

        elif action_type == "input":
            variable_name = "input_value"

            variables.append(
                SkillVariable(
                    name=variable_name,
                    example_value=value,
                    description=(
                        "User-provided input learned "
                        "from demonstration."
                    ),
                )
            )

            steps.append(
                SkillStep(
                    action_type="input",
                    target=target,
                    value="{{input_value}}",
                )
            )

        elif action_type == "click":
            steps.append(
                SkillStep(
                    action_type="click",
                    target=target,
                )
            )

    return Skill(
        name="learned_workflow",
        description=(
            "A reusable workflow learned "
            "from user demonstration."
        ),
        variables=variables,
        steps=steps,
    )


def generalize_workflow(workflow_id: int) -> Skill:
    actions = get_actions(workflow_id)

    clean_actions = [
        action
        for action in actions
        if not is_noise(action)
    ]

    if detect_search_workflow(clean_actions):
        return generalize_search_workflow(
            clean_actions
        )

    return generalize_generic_workflow(
        clean_actions
    )