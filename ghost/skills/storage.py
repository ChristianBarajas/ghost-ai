import json
from pathlib import Path
from typing import List

from ghost.models.skill import Skill


SKILLS_DIR = Path("data/skills")


def save_skill(skill: Skill):
    """
    Persist a learned skill as JSON.

    Each skill is stored independently so GHOST can
    load and execute learned workflows by name.
    """

    SKILLS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = SKILLS_DIR / f"{skill.name}.json"

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            skill.model_dump(),
            file,
            indent=2,
        )

    return path


def load_skill(skill_name: str) -> Skill:
    """
    Load one learned skill by name.
    """

    path = SKILLS_DIR / f"{skill_name}.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Skill '{skill_name}' does not exist."
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return Skill(**data)


def list_skills() -> List[Skill]:
    """
    Discover every learned skill currently stored by GHOST.

    The JSON files are validated through the Skill
    Pydantic model before being returned.
    """

    if not SKILLS_DIR.exists():
        return []

    skills: List[Skill] = []

    skill_paths = sorted(
        SKILLS_DIR.glob("*.json")
    )

    for path in skill_paths:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        skill = Skill(**data)

        skills.append(skill)

    return skills