import argparse

from ghost.executor.browser import replay_workflow
from ghost.memory.database import (
    initialize_database,
    create_workflow,
    get_actions,
)
from ghost.observer.browser import observe_browser
from ghost.skills.generalizer import generalize_workflow


def main():
    initialize_database()

    parser = argparse.ArgumentParser(
        description="GHOST — Learn workflows by observation."
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    # --------------------------------------------------
    # OBSERVE
    # --------------------------------------------------

    observe_parser = subparsers.add_parser(
        "observe",
        help="Observe and record a workflow.",
    )

    observe_parser.add_argument(
        "name",
        nargs="?",
        default="Unnamed Workflow",
    )

    # --------------------------------------------------
    # REPLAY
    # --------------------------------------------------

    replay_parser = subparsers.add_parser(
        "replay",
        help="Replay a recorded workflow.",
    )

    replay_parser.add_argument(
        "workflow_id",
        type=int,
    )

    # --------------------------------------------------
    # SHOW
    # --------------------------------------------------

    show_parser = subparsers.add_parser(
        "show",
        help="Show actions from a workflow.",
    )

    show_parser.add_argument(
        "workflow_id",
        type=int,
    )

    # --------------------------------------------------
    # GENERALIZE
    # --------------------------------------------------

    generalize_parser = subparsers.add_parser(
        "generalize",
        help="Convert a recorded workflow into a reusable skill.",
    )

    generalize_parser.add_argument(
        "workflow_id",
        type=int,
    )

    args = parser.parse_args()

    # --------------------------------------------------
    # COMMAND HANDLING
    # --------------------------------------------------

    if args.command == "observe":
        workflow_id = create_workflow(args.name)

        print(
            f"\n👻 Created workflow #{workflow_id}: {args.name}"
        )

        observe_browser(workflow_id)

        print(
            f"\n✅ Workflow #{workflow_id} saved."
        )

    elif args.command == "replay":
        replay_workflow(
            args.workflow_id
        )

    elif args.command == "show":
        actions = get_actions(
            args.workflow_id
        )

        print()

        for action in actions:
            print(
                f"[{action['action_type']}] "
                f"target={action['target']} "
                f"value={action['value']} "
                f"url={action['url']}"
            )

    elif args.command == "generalize":
        skill = generalize_workflow(
            args.workflow_id
        )

        print()
        print("👻 GHOST SKILL")
        print("----------------")
        print(f"Name: {skill.name}")
        print(f"Description: {skill.description}")

        print()
        print("VARIABLES")

        if not skill.variables:
            print("None")

        for variable in skill.variables:
            print(
                f"- {variable.name} = "
                f'"{variable.example_value}"'
            )

        print()
        print("STEPS")

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

    else:
        parser.print_help()


if __name__ == "__main__":
    main()