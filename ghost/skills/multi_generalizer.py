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


def has_search_submission(actions, input_action):
    if input_action is None:
        return False

    input_id = input_action["id"]

    # Search can be submitted by clicking a search control.
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
        return True

    # Or by pressing ENTER, which usually causes navigation.
    later_navigation = next(
        (
            action
            for action in actions
            if action["id"] > input_id
            and action["action_type"] == "navigate"
        ),
        None,
    )

    if later_navigation:
        return True

    return False


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

    # ------------------------------------------
    # FIND INPUTS
    # ------------------------------------------

    input_actions = [
        find_meaningful_input(actions)
        for actions in demonstrations
    ]

    if any(
        action is None
        for action in input_actions
    ):
        raise ValueError(
            "Not every demonstration contains meaningful input."
        )

    # ------------------------------------------
    # CONFIRM COMMON SEARCH BEHAVIOR
    # ------------------------------------------

    search_submissions = [
        has_search_submission(
            actions,
            input_action,
        )
        for actions, input_action in zip(
            demonstrations,
            input_actions,
        )
    ]

    if not all(search_submissions):
        raise ValueError(
            "Not every demonstration appears to complete a search."
        )

    # ------------------------------------------
    # VARIABLE VALUES
    # ------------------------------------------

    example_values = [
        action["value"]
        for action in input_actions
    ]

    # ------------------------------------------
    # STARTING LOCATIONS
    # ------------------------------------------

    starting_urls = []

    for actions in demonstrations:
        navigation = next(
            (
                action
                for action in actions
                if action["action_type"] == "navigate"
            ),
            None,
        )

        if navigation:
            starting_urls.append(
                navigation["url"]
            )

    unique_starting_urls = list(
        dict.fromkeys(starting_urls)
    )

    # ------------------------------------------
    # REPORT PATTERN
    # ------------------------------------------

    print()
    print("👻 PATTERN FOUND")
    print("----------------")
    print("All demonstrations:")
    print("- contain meaningful text input")
    print("- produce search results")
    print("- differ in query value")

    if len(unique_starting_urls) > 1:
        print("- use different search engines")

    print()
    print("Observed queries:")

    for value in example_values:
        print(
            f'- "{value}"'
        )

    print()
    print("Observed starting locations:")

    for url in unique_starting_urls:
        print(
            f"- {url}"
        )

    # ------------------------------------------
    # BUILD SEMANTIC SKILL
    # ------------------------------------------

    steps = []

    # If every demonstration started in the same
    # environment, preserve that location.
    #
    # If multiple environments were demonstrated,
    # don't hardcode one search engine.
    if len(unique_starting_urls) == 1:
        steps.append(
            SkillStep(
                action_type="navigate",
                url=unique_starting_urls[0],
            )
        )

    # Semantic target instead of a
    # website-specific DOM label.
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
                    "Variable search query identified "
                    "across demonstrations."
                ),
            )
        ],
        steps=steps,
    )