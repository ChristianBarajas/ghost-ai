from typing import Any, Dict

from ghost.skills.project_verifier import (
    verify_project,
)
from ghost.skills.runner import (
    run_skill as run_browser_skill,
)
from ghost.skills.storage import load_skill


PROJECT_SKILLS = {
    "verify_project",
}


def run_project_skill(
    skill_name: str,
    variables: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute a project/developer-oriented GHOST skill.
    """

    skill = load_skill(
        skill_name
    )

    if skill.name != "verify_project":
        raise ValueError(
            f"Unsupported project skill: "
            f"{skill.name}"
        )

    project_path = variables.get(
        "project_path"
    )

    if not project_path:
        raise ValueError(
            "verify_project requires "
            "'project_path'."
        )

    result = verify_project(
        project_path
    )

    verified = result[
        "summary"
    ][
        "success"
    ]

    return {
        "success": verified,
        "verified": verified,
        "skill": skill.name,
        "provider": None,
        "variables": variables,
        "result": result,
    }


def run_skill(
    skill_name: str,
    variables: Dict[str, Any],
    provider_name=None,
) -> Dict[str, Any]:
    """
    Main GHOST skill dispatcher.

    Chooses the correct execution engine
    based on the requested skill.
    """

    skill = load_skill(
        skill_name
    )

    print()
    print(
        "👻 GHOST EXECUTOR"
    )
    print(
        "-----------------"
    )

    print(
        f"Skill: {skill.name}"
    )

    if skill.name in PROJECT_SKILLS:
        print(
            "Executor: project"
        )

        return run_project_skill(
            skill.name,
            variables,
        )

    print(
        "Executor: browser"
    )

    return run_browser_skill(
        skill.name,
        variables,
        provider_name=provider_name,
    )