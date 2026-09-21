from typing import List, Optional

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
from ghost.skills.runner import run_skill


app = FastAPI(
    title="GHOST API",
    description="API for the GHOST AI workflow-learning agent.",
    version="0.3.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
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
    result: Optional[ResearchResult] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def clean_ghost_result(ghost_result):
    if not ghost_result:
        return {
            "success": False,
            "verified": False,
            "skill": None,
            "result": None,
        }

    raw_result = ghost_result.get("result")

    clean_result = None

    if raw_result:
        clean_result = {
            "title": raw_result.get("title"),
            "url": raw_result.get("url"),
            "domain": raw_result.get("domain"),
            "summary": raw_result.get("summary"),
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


# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "ghost-api",
        "version": "0.3.0",
    }


# --------------------------------------------------
# CREATE + EXECUTE TASK
# --------------------------------------------------

@app.post(
    "/api/tasks",
    response_model=TaskResponse,
)
def create_task(
    request: ResearchTaskRequest,
):
    task_id = create_task_record(
        request.query,
        request.provider,
    )

    try:
        ghost_result = run_skill(
            "research_topic",
            {
                "query": request.query,
            },
            provider_name=request.provider,
        )

        clean_result = clean_ghost_result(
            ghost_result
        )

        success = clean_result["success"]

        update_task_record(
            task_id,
            status=(
                "completed"
                if success
                else "failed"
            ),
            success=success,
            verified=clean_result["verified"],
            skill=clean_result["skill"],
            result=clean_result["result"],
        )

    except Exception as error:
        update_task_record(
            task_id,
            status="failed",
            success=False,
            verified=False,
            error=str(error),
        )

    task = get_task_record(task_id)

    if task is None:
        raise HTTPException(
            status_code=500,
            detail="Task could not be loaded.",
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
    task = get_task_record(task_id)

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