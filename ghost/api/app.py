from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ghost.memory.database import (
    create_task_record,
    get_task_record,
    initialize_database,
    list_task_records,
    update_task_record,
)
from ghost.models.skill import Skill
from ghost.skills.executor import (
    run_skill as run_ghost_skill,
)
from ghost.skills.storage import (
    list_skills,
    load_skill,
)


app = FastAPI(
    title="GHOST API",
    description="API for the GHOST AI workflow-learning agent.",
    version="0.4.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"^https?://"
        r"(localhost|127\.0\.0\.1)"
        r"(:\d+)?$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

initialize_database()


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class ResearchTaskRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=500,
    )

    provider: str = "duckduckgo"


class SkillRunRequest(BaseModel):
    variables: Dict[str, Any] = Field(
        default_factory=dict
    )

    provider: Optional[str] = None


# --------------------------------------------------
# RESPONSE MODELS
# --------------------------------------------------

class ResearchResult(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    domain: Optional[str] = None
    summary: Optional[str] = None
    key_terms: List[str] = []
    summary_source: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: int
    status: str
    query: str
    provider: str
    success: Optional[bool] = None
    verified: Optional[bool] = None
    skill: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def clean_research_result(
    ghost_result,
):
    if not ghost_result:
        return {
            "success": False,
            "verified": False,
            "skill": None,
            "result": None,
        }

    raw_result = ghost_result.get(
        "result"
    )

    clean_result = None

    if raw_result:
        clean_result = {
            "title": raw_result.get(
                "title"
            ),
            "url": raw_result.get(
                "url"
            ),
            "domain": raw_result.get(
                "domain"
            ),
            "summary": raw_result.get(
                "summary"
            ),
            "key_terms": raw_result.get(
                "key_terms",
                [],
            ),
            "summary_source": raw_result.get(
                "summary_source"
            ),
        }

    return {
        "success": ghost_result.get(
            "success",
            False,
        ),
        "verified": ghost_result.get(
            "verified"
        ),
        "skill": ghost_result.get(
            "skill"
        ),
        "result": clean_result,
    }


def save_skill_execution(
    skill_name: str,
    display_query: str,
    provider: str,
    variables: Dict[str, Any],
):
    task_id = create_task_record(
        display_query,
        provider,
    )

    try:
        ghost_result = run_ghost_skill(
            skill_name,
            variables,
            provider_name=(
                None
                if provider == "project"
                else provider
            ),
        )

        success = bool(
            ghost_result.get(
                "success",
                False,
            )
        )

        verified = ghost_result.get(
            "verified"
        )

        result = ghost_result.get(
            "result"
        )

        update_task_record(
            task_id,
            status=(
                "completed"
                if success
                else "failed"
            ),
            success=success,
            verified=verified,
            skill=skill_name,
            result=result,
        )

    except Exception as error:
        update_task_record(
            task_id,
            status="failed",
            success=False,
            verified=False,
            skill=skill_name,
            error=str(error),
        )

    task = get_task_record(
        task_id
    )

    if task is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Task could not be loaded."
            ),
        )

    return task


# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "ghost-api",
        "version": "0.4.0",
    }


# --------------------------------------------------
# SKILLS
# --------------------------------------------------

@app.get(
    "/api/skills",
    response_model=List[Skill],
)
def get_skills():
    return list_skills()


@app.get(
    "/api/skills/{skill_name}",
    response_model=Skill,
)
def get_skill(
    skill_name: str,
):
    try:
        return load_skill(
            skill_name
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Skill not found.",
        )


@app.post(
    "/api/skills/{skill_name}/run",
    response_model=TaskResponse,
)
def run_skill_endpoint(
    skill_name: str,
    request: SkillRunRequest,
):
    """
    Execute a GHOST skill and persist the run.
    """

    try:
        load_skill(
            skill_name
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Skill not found.",
        )

    if skill_name == "verify_project":
        project_path = request.variables.get(
            "project_path"
        )

        if not project_path:
            raise HTTPException(
                status_code=400,
                detail=(
                    "verify_project requires "
                    "'project_path'."
                ),
            )

        return save_skill_execution(
            skill_name="verify_project",
            display_query=project_path,
            provider="project",
            variables={
                "project_path": project_path,
            },
        )

    raise HTTPException(
        status_code=400,
        detail=(
            f"Skill '{skill_name}' is not "
            f"supported by this endpoint yet."
        ),
    )


# --------------------------------------------------
# CREATE + EXECUTE RESEARCH TASK
# --------------------------------------------------

@app.post(
    "/api/tasks",
    response_model=TaskResponse,
)
def create_task(
    request: ResearchTaskRequest,
):
    task = save_skill_execution(
        skill_name="research_topic",
        display_query=request.query,
        provider=request.provider,
        variables={
            "query": request.query,
        },
    )

    if (
        task.get("result")
        is not None
    ):
        task["result"] = (
            clean_research_result({
                "success": task.get(
                    "success"
                ),
                "verified": task.get(
                    "verified"
                ),
                "skill": task.get(
                    "skill"
                ),
                "result": task.get(
                    "result"
                ),
            })["result"]
        )

    return task


# --------------------------------------------------
# GET TASK
# --------------------------------------------------

@app.get(
    "/api/tasks/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int,
):
    task = get_task_record(
        task_id
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found.",
        )

    return task


# --------------------------------------------------
# LIST TASKS
# --------------------------------------------------

@app.get(
    "/api/tasks",
    response_model=List[TaskResponse],
)
def list_tasks():
    return list_task_records()