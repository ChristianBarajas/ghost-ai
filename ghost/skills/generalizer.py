from urllib.parse import urlparse

from ghost.memory.database import get_actions
from ghost.models.skill import Skill, SkillStep, SkillVariable
from typing import Optional


def is_noise(action) -> bool:
    action_type = action["action_type"]
    target = action["target"]
    value = action["value"]

    if action_type == "input" and (value is None or value.strip() == ""):
        return True

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


def generalize_workflow(workflow_id: int) -> Skill:
    actions = get_actions(workflow_id)

    clean_actions = [
        action
        for action in actions
        if not is_noise(action)
    ]

    steps = []
    variables = []

    seen_navigation = False

    for action in clean_actions:
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
            variable_name = "query"

            variables.append(
                SkillVariable(
                    name=variable_name,
                    example_value=value,
                    description="User-provided input learned from demonstration.",
                )
            )

            steps.append(
                SkillStep(
                    action_type="input",
                    target=target,
                    value=f"{{{{{variable_name}}}}}",
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
        description="A reusable workflow learned from user demonstration.",
        variables=variables,
        steps=steps,
    )
