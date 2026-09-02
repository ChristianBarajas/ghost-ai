from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ghost.skills.runner import run_skill


app = FastAPI(
    title="GHOST API",
    description="API for the GHOST AI workflow-learning agent.",
    version="0.2.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# --------------------------------------------------
# TEMPORARY IN-MEMORY TASK STORE
# --------------------------------------------------

tasks: Dict[int, Dict[str, Any]] = {}

next_task_id = 1


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def clean_ghost_result(
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


# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "ghost-api",
        "version": "0.2.0",
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
    global next_task_id

    task_id = next_task_id
    next_task_id += 1

    task = {
        "task_id": task_id,
        "status": "running",
        "query": request.query,
        "provider": request.provider,
        "success": None,
        "verified": None,
        "skill": None,
        "result": None,
        "error": None,
    }

    tasks[task_id] = task

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

        task["success"] = clean_result[
            "success"
        ]

        task["verified"] = clean_result[
            "verified"
        ]

        task["skill"] = clean_result[
            "skill"
        ]

        task["result"] = clean_result[
            "result"
        ]

        if task["success"]:
            task["status"] = "completed"
        else:
            task["status"] = "failed"

    except Exception as error:
        task["status"] = "failed"
        task["success"] = False
        task["verified"] = False
        task["error"] = str(
            error
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
    task = tasks.get(
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
    return list(
        tasks.values()
    )