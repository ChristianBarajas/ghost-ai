import re
from typing import Any, Dict, List

from ghost.ai.client import ai_client
from ghost.models.skill import (
    Skill,
    SkillStep,
    SkillVariable,
)
from ghost.skills.storage import (
    load_skill,
    save_skill,
)


ALLOWED_ACTION_TYPES = {
    "navigate",
    "input",
    "submit",
    "select",
    "open",
    "extract",
    "verify",
    "click",
}


SKILL_NAME_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*$"
)


VARIABLE_NAME_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*$"
)


VARIABLE_REFERENCE_PATTERN = re.compile(
    r"\{\{([a-zA-Z0-9_]+)\}\}"
)


def _validate_demonstrations(
    demonstrations: List[Dict[str, Any]],
):
    if len(demonstrations) < 2:
        raise ValueError(
            "GHOST needs at least two demonstrations "
            "to infer a reusable workflow."
        )

    for index, demonstration in enumerate(
        demonstrations,
        start=1,
    ):
        if not isinstance(
            demonstration,
            dict,
        ):
            raise ValueError(
                f"Demonstration {index} must be an object."
            )

        if not demonstration:
            raise ValueError(
                f"Demonstration {index} is empty."
            )


def _build_variables(
    raw_variables,
):
    if not isinstance(
        raw_variables,
        list,
    ):
        raise ValueError(
            "Learned workflow variables must be a list."
        )

    variables: List[SkillVariable] = []

    seen_names = set()

    for raw_variable in raw_variables:
        if not isinstance(
            raw_variable,
            dict,
        ):
            raise ValueError(
                "Each learned variable must be an object."
            )

        name = raw_variable.get(
            "name"
        )

        example_value = raw_variable.get(
            "example_value"
        )

        description = raw_variable.get(
            "description"
        )

        if not isinstance(
            name,
            str,
        ):
            raise ValueError(
                "Learned variable is missing a valid name."
            )

        if not VARIABLE_NAME_PATTERN.fullmatch(
            name
        ):
            raise ValueError(
                f"Invalid variable name: {name}"
            )

        if name in seen_names:
            raise ValueError(
                f"Duplicate variable: {name}"
            )

        if not isinstance(
            example_value,
            str,
        ):
            raise ValueError(
                f"Variable '{name}' requires "
                "a string example_value."
            )

        seen_names.add(
            name
        )

        variables.append(
            SkillVariable(
                name=name,
                example_value=example_value,
                description=description,
            )
        )

    return variables


def _build_steps(
    raw_steps,
    variables: List[SkillVariable],
):
    if not isinstance(
        raw_steps,
        list,
    ):
        raise ValueError(
            "Learned workflow steps must be a list."
        )

    if not raw_steps:
        raise ValueError(
            "Learned workflow contains no steps."
        )

    variable_names = {
        variable.name
        for variable in variables
    }

    steps: List[SkillStep] = []

    for index, raw_step in enumerate(
        raw_steps,
        start=1,
    ):
        if not isinstance(
            raw_step,
            dict,
        ):
            raise ValueError(
                f"Step {index} must be an object."
            )

        action_type = raw_step.get(
            "action_type"
        )

        if action_type not in (
            ALLOWED_ACTION_TYPES
        ):
            raise ValueError(
                f"Unsupported action type "
                f"'{action_type}' in step {index}."
            )

        target = raw_step.get(
            "target"
        )

        value = raw_step.get(
            "value"
        )

        url = raw_step.get(
            "url"
        )

        strings_to_check = [
            item
            for item in [
                target,
                value,
                url,
            ]
            if isinstance(
                item,
                str,
            )
        ]

        for text in strings_to_check:
            references = (
                VARIABLE_REFERENCE_PATTERN.findall(
                    text
                )
            )

            for reference in references:
                if (
                    reference
                    not in variable_names
                ):
                    raise ValueError(
                        f"Step {index} references "
                        f"undeclared variable "
                        f"'{{{{{reference}}}}}'."
                    )

        steps.append(
            SkillStep(
                action_type=action_type,
                target=target,
                value=value,
                url=url,
            )
        )

    return steps


def learn_skill_candidate(
    demonstrations: List[
        Dict[str, Any]
    ],
):
    """
    Ask GHOST's AI to generalize several
    demonstrations into a reusable Skill.

    This does NOT save the skill.

    The returned candidate must be explicitly
    approved before persistence.
    """

    _validate_demonstrations(
        demonstrations
    )

    if not ai_client.is_available():
        raise RuntimeError(
            "GHOST AI is unavailable."
        )

    analysis = (
        ai_client.analyze_demonstrations(
            demonstrations
        )
    )

    if not analysis:
        raise RuntimeError(
            "GHOST AI returned no workflow analysis."
        )

    skill_name = analysis.get(
        "skill_name"
    )

    description = analysis.get(
        "description"
    )

    intent = analysis.get(
        "intent"
    )

    optional_behavior = analysis.get(
        "optional_behavior",
        [],
    )

    confidence = analysis.get(
        "confidence"
    )

    if not isinstance(
        skill_name,
        str,
    ):
        raise ValueError(
            "Learned workflow has no skill name."
        )

    if not SKILL_NAME_PATTERN.fullmatch(
        skill_name
    ):
        raise ValueError(
            f"Invalid learned skill name: "
            f"{skill_name}"
        )

    if not isinstance(
        description,
        str,
    ) or not description.strip():
        raise ValueError(
            "Learned workflow has no description."
        )

    if not isinstance(
        intent,
        str,
    ) or not intent.strip():
        raise ValueError(
            "Learned workflow has no intent."
        )

    if not isinstance(
        confidence,
        (int, float),
    ):
        raise ValueError(
            "Learned workflow confidence "
            "must be numeric."
        )

    if not (
        0.0
        <= confidence
        <= 1.0
    ):
        raise ValueError(
            "Learned workflow confidence "
            "must be between 0.0 and 1.0."
        )

    if not isinstance(
        optional_behavior,
        list,
    ):
        raise ValueError(
            "optional_behavior must be a list."
        )

    variables = _build_variables(
        analysis.get(
            "variables",
            [],
        )
    )

    steps = _build_steps(
        analysis.get(
            "steps",
            [],
        ),
        variables,
    )

    skill = Skill(
        name=skill_name,
        description=description,
        variables=variables,
        steps=steps,
    )

    return {
        "skill": skill,
        "intent": intent,
        "optional_behavior": (
            optional_behavior
        ),
        "confidence": float(
            confidence
        ),
    }


def save_learned_skill(
    skill: Skill,
    overwrite: bool = False,
):
    """
    Persist an explicitly approved learned skill.

    Existing skills are protected unless the
    caller deliberately allows replacement.
    """

    if not overwrite:
        try:
            load_skill(
                skill.name
            )

        except FileNotFoundError:
            pass

        else:
            raise ValueError(
                f"Skill '{skill.name}' already exists. "
                "Explicit overwrite approval is required."
            )

    path = save_skill(
        skill
    )

    return path