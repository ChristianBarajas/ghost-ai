from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ghost.models.skill import Skill
from ghost.skills.learner import (
    learn_skill_candidate,
    save_learned_skill,
)


router = APIRouter(
    prefix="/api/skills",
    tags=["skill-learning"],
)


class LearnSkillRequest(BaseModel):
    demonstrations: List[
        Dict[str, Any]
    ] = Field(
        min_length=2,
    )


class LearnSkillResponse(BaseModel):
    skill: Skill
    intent: str
    optional_behavior: List[Any]
    confidence: float


class ApproveSkillRequest(BaseModel):
    skill: Skill
    overwrite: bool = False


class ApproveSkillResponse(BaseModel):
    saved: bool
    skill: Skill
    path: str


@router.post(
    "/learn",
    response_model=LearnSkillResponse,
)
def learn_skill(
    request: LearnSkillRequest,
):
    """
    Analyze several demonstrations and propose
    a reusable GHOST skill.

    This endpoint does NOT save the skill.
    """

    try:
        candidate = (
            learn_skill_candidate(
                request.demonstrations
            )
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=(
                f"GHOST could not learn "
                f"the workflow: {error}"
            ),
        )

    return LearnSkillResponse(
        skill=candidate["skill"],
        intent=candidate["intent"],
        optional_behavior=(
            candidate[
                "optional_behavior"
            ]
        ),
        confidence=(
            candidate["confidence"]
        ),
    )


@router.post(
    "/learn/approve",
    response_model=ApproveSkillResponse,
)
def approve_skill(
    request: ApproveSkillRequest,
):
    """
    Persist a learned GHOST skill after
    explicit approval.
    """

    try:
        path = save_learned_skill(
            request.skill,
            overwrite=request.overwrite,
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=(
                f"GHOST could not save "
                f"the skill: {error}"
            ),
        )

    return ApproveSkillResponse(
        saved=True,
        skill=request.skill,
        path=str(path),
    )