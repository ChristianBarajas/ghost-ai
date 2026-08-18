from typing import List, Optional

from pydantic import BaseModel


class SkillStep(BaseModel):
    action_type: str
    target: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None


class SkillVariable(BaseModel):
    name: str
    example_value: str
    description: Optional[str] = None


class Skill(BaseModel):
    name: str
    description: str
    variables: List[SkillVariable] = []
    steps: List[SkillStep] = []