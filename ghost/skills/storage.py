import json
from pathlib import Path

from ghost.models.skill import Skill


SKILLS_DIR = Path("data/skills")


def save_skill(skill: Skill):
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    path = SKILLS_DIR / f"{skill.name}.json"

    with open(path, "w") as file:
        json.dump(
            skill.model_dump(),
            file,
            indent=2,
        )

    return path


def load_skill(skill_name: str) -> Skill:
    path = SKILLS_DIR / f"{skill_name}.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Skill '{skill_name}' does not exist."
        )

    with open(path, "r") as file:
        data = json.load(file)

    return Skill(**data)
