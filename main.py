import argparse

from ghost.executor.browser import replay_workflow
from ghost.memory.database import (
    initialize_database,
    create_workflow,
    get_actions,
)
from ghost.observer.browser import observe_browser
from ghost.skills.generalizer import generalize_workflow
from ghost.skills.storage import save_skill
from ghost.skills.runner import run_skill
from ghost.skills.multi_generalizer import learn_from_demonstrations


def main():
    initialize_database()

    parser = argparse.ArgumentParser(
        description="GHOST — Learn workflows by observation."
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    # OBSERVE
    observe_parser = subparsers.add_parser(
        "observe",
        help="Observe and record a workflow.",
    )

    observe_parser.add_argument(
        "name",
        nargs="?",
        default="Unnamed Workflow",
    )

    # REPLAY
    replay_parser = subparsers.add_parser(
        "replay",
        help="Replay a recorded workflow.",
    )

    replay_parser.add_argument(
        "workflow_id",
        type=int,
    )

    # SHOW
    show_parser = subparsers.add_parser(
        "show",
        help="Show actions from a workflow.",
    )

    show_parser.add_argument(
        "workflow_id",
        type=int,
    )

    # GENERALIZE
    generalize_parser = subparsers.add_parser(
        "generalize",
        help="Convert a recorded workflow into a reusable skill.",
    )

    generalize_parser.add_argument(
        "workflow_id",
        type=int,
    )

    # LEARN
    learn_parser = subparsers.add_parser(
        "learn",
        help="Generalize and save a workflow as a reusable skill.",
    )

    learn_parser.add_argument(
        "workflow_id",
        type=int,
    )

    # RUN SKILL
    run_skill_parser = subparsers.add_parser(
        "run-skill",
        help="Run a saved GHOST skill.",
    )

    run_skill_parser.add_argument(
        "skill_name",
    )

    run_skill_parser.add_argument(
        "--query",
    )

    # COMPARE
    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare multiple workflow demonstrations.",
    )

    compare_parser.add_argument(
        "workflow_ids",
        nargs="+",
        type=int,
    )

    args = parser.parse_args()

    # ------------------------------------------
    # COMMAND HANDLING
    # ------------------------------------------

    if args.command == "observe":
        workflow_id = create_workflow(
            args.name
        )

        print(
            f"\n👻 Created workflow #{workflow_id}: {args.name}"
        )

        observe_browser(
            workflow_id
        )

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
        print(
            f"Description: {skill.description}"
        )

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

    elif args.command == "learn":
        skill = generalize_workflow(
            args.workflow_id
        )

        path = save_skill(
            skill
        )

        print()
        print(
            f"👻 Learned skill: {skill.name}"
        )
        print(
            f"💾 Saved to: {path}"
        )

    elif args.command == "run-skill":
        variables = {}

        if args.query:
            variables["query"] = args.query

        run_skill(
            args.skill_name,
            variables,
        )

    elif args.command == "compare":
        skill = learn_from_demonstrations(
            args.workflow_ids
        )

        print()
        print("👻 MULTI-DEMO SKILL")
        print("-------------------")
        print(f"Name: {skill.name}")
        print(
            f"Description: {skill.description}"
        )

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