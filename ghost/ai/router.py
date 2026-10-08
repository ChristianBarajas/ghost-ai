from typing import (
    Any,
    Dict,
    List,
)

from pydantic import BaseModel

from ghost.ai.client import (
    ai_client,
)
from ghost.memory.database import (
    get_skill_experience,
)
from ghost.skills.storage import (
    list_skills,
)


class RouteDecision(BaseModel):
    skill: str
    confidence: float
    variables: Dict[
        str,
        Any,
    ]
    missing_variables: List[str]
    reason: str


def build_skill_catalog():
    """
    Build the capability catalog shown to the
    AI router.

    In addition to each skill's definition,
    GHOST now includes historical execution
    experience for that capability.
    """

    skills = list_skills()

    catalog = []

    for skill in skills:
        experience = (
            get_skill_experience(
                skill.name
            )
        )

        catalog.append({
            "name": skill.name,
            "description": (
                skill.description
            ),
            "variables": [
                {
                    "name": (
                        variable.name
                    ),
                    "description": (
                        variable.description
                    ),
                    "example_value": (
                        variable.example_value
                    ),
                }
                for variable
                in skill.variables
            ],
            "experience": experience,
        })

    return catalog


def route_request(
    user_request: str,
) -> RouteDecision:
    if not user_request.strip():
        raise ValueError(
            "User request cannot be empty."
        )

    if not ai_client.is_available():
        raise RuntimeError(
            "GHOST AI is unavailable."
        )

    skills = build_skill_catalog()

    if not skills:
        raise RuntimeError(
            "GHOST has no available skills."
        )

    raw_decision = (
        ai_client.route_request(
            user_request=user_request,
            skills=skills,
        )
    )

    if not raw_decision:
        raise RuntimeError(
            "GHOST AI returned no routing decision."
        )

    skill_name = raw_decision.get(
        "skill"
    )

    available_skills = {
        skill["name"]
        for skill in skills
    }

    if (
        skill_name
        not in available_skills
    ):
        raise ValueError(
            f"GHOST AI selected unknown skill: "
            f"{skill_name}"
        )

    confidence = raw_decision.get(
        "confidence",
        0.0,
    )

    if not isinstance(
        confidence,
        (int, float),
    ):
        raise ValueError(
            "Routing confidence must be numeric."
        )

    if not (
        0.0
        <= confidence
        <= 1.0
    ):
        raise ValueError(
            "Routing confidence must be between "
            "0.0 and 1.0."
        )

    selected_skill = next(
        skill
        for skill in skills
        if (
            skill["name"]
            == skill_name
        )
    )

    valid_variable_names = {
        variable["name"]
        for variable
        in selected_skill[
            "variables"
        ]
    }

    raw_variables = (
        raw_decision.get(
            "variables",
            {},
        )
    )

    if not isinstance(
        raw_variables,
        dict,
    ):
        raise ValueError(
            "Routing variables must "
            "be an object."
        )

    variables = {
        name: value
        for name, value
        in raw_variables.items()
        if name
        in valid_variable_names
    }

    # Informational research requests can
    # safely use the complete user request
    # as the query when the model does not
    # explicitly return one.
    if (
        "query"
        in valid_variable_names
        and "query"
        not in variables
    ):
        variables["query"] = (
            user_request.strip()
        )

    required_variables = {
        variable["name"]
        for variable
        in selected_skill[
            "variables"
        ]
    }

    missing_variables = [
        name
        for name
        in required_variables
        if (
            name not in variables
            or variables[
                name
            ] is None
            or (
                isinstance(
                    variables[
                        name
                    ],
                    str,
                )
                and not variables[
                    name
                ].strip()
            )
        )
    ]

    reason = raw_decision.get(
        "reason",
        "",
    )

    return RouteDecision(
        skill=skill_name,
        confidence=float(
            confidence
        ),
        variables=variables,
        missing_variables=(
            missing_variables
        ),
        reason=reason,
    )