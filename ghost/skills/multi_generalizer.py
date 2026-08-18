from collections import Counter

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

        if action_type == "input":
            if value is None or value.strip() == "":
                continue

        if action_type == "click":
            if target in {"img", "svg", "VERIFY"}:
                continue

        clean.append(action)

    return clean


def action_signature(action):
    return action["action_type"]


def learn_from_demonstrations(workflow_ids):
    demonstrations = [
        meaningful_actions(workflow_id)
        for workflow_id in workflow_ids
    ]

    if not demonstrations:
        raise ValueError(
            "No demonstrations provided."
        )

    print()
    print("👻 COMPARING DEMONSTRATIONS")
    print("---------------------------")

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

    input_actions = []

    for actions in demonstrations:
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
            input_actions.append(
                input_action
            )

    if len(input_actions) != len(demonstrations):
        raise ValueError(
            "Not every demonstration contains meaningful input."
        )

    search_clicks = []

    for actions in demonstrations:
        click = next(
            (
                action
                for action in actions
                if action["action_type"] == "click"
                and action["target"]
                and "search" in action["target"].lower()
            ),
            None,
        )

        if click:
            search_clicks.append(
                click
            )

    if len(search_clicks) != len(demonstrations):
        raise ValueError(
            "Not every demonstration looks like a search workflow."
        )

    # Find the most common input target.
    input_targets = [
        action["target"]
        for action in input_actions
    ]

    common_target = Counter(
        input_targets
    ).most_common(1)[0][0]

    example_values = [
        action["value"]
        for action in input_actions
    ]

    print()
    print("👻 PATTERN FOUND")
    print("----------------")
    print("All demonstrations:")
    print("- contain user text input")
    print("- contain a search submission")
    print("- differ in input value")

    print()
    print("Observed values:")

    for value in example_values:
        print(
            f'- "{value}"'
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
                    "Variable search query "
                    "identified across demonstrations."
                ),
            )
        ],
        steps=[
            SkillStep(
                action_type="input",
                target=common_target,
                value="{{query}}",
            ),
            SkillStep(
                action_type="click",
                target="Search",
            ),
        ],
    )
