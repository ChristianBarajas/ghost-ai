from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ghost.ai.router import route_request
from ghost.api.learning import router as learning_router
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
    version="0.5.1",
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
# SKILL LEARNING
# --------------------------------------------------

app.include_router(
    learning_router
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


class SkillRunRequest(BaseModel):
    variables: Dict[str, Any] = Field(
        default_factory=dict
    )

    provider: Optional[str] = None


class AgentRunRequest(BaseModel):
    request: str = Field(
        min_length=1,
        max_length=1000,
    )

    provider: str = "duckduckgo"


class AgentContinueRequest(BaseModel):
    original_request: str = Field(
        min_length=1,
        max_length=1000,
    )

    skill: str = Field(
        min_length=1,
        max_length=100,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reason: str = ""

    variables: Dict[str, Any] = Field(
        default_factory=dict
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
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class RouteResponse(BaseModel):
    skill: str
    confidence: float
    variables: Dict[str, Any]
    missing_variables: List[str]
    reason: str


class AgentRunResponse(BaseModel):
    routed: bool
    executed: bool
    route: RouteResponse
    task: Optional[TaskResponse] = None


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


def clean_saved_research_task(
    task,
):
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
            detail="Task could not be loaded.",
        )

    return task


def provider_for_skill(
    skill_name: str,
    requested_provider: str,
):
    if skill_name == "verify_project":
        return "project"

    return requested_provider


def display_query_for_skill(
    skill_name: str,
    variables: Dict[str, Any],
    original_request: str,
):
    if skill_name == "verify_project":
        return variables.get(
            "project_path",
            original_request,
        )

    if "query" in variables:
        return str(
            variables["query"]
        )

    return original_request


def get_missing_variables(
    skill_name: str,
    variables: Dict[str, Any],
):
    try:
        skill = load_skill(
            skill_name
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Skill not found.",
        )

    missing = []

    for variable in skill.variables:
        value = variables.get(
            variable.name
        )

        if value is None:
            missing.append(
                variable.name
            )

            continue

        if (
            isinstance(
                value,
                str,
            )
            and not value.strip()
        ):
            missing.append(
                variable.name
            )

    return missing


def execute_agent_skill(
    skill_name: str,
    variables: Dict[str, Any],
    original_request: str,
    requested_provider: str,
):
    provider = provider_for_skill(
        skill_name,
        requested_provider,
    )

    display_query = (
        display_query_for_skill(
            skill_name,
            variables,
            original_request,
        )
    )

    task = save_skill_execution(
        skill_name=skill_name,
        display_query=display_query,
        provider=provider,
        variables=variables,
    )

    if (
        skill_name
        in {
            "research_topic",
            "research_topic_via_web_search",
        }
    ):
        task = clean_saved_research_task(
            task
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
        "version": "0.5.1",
    }


# --------------------------------------------------
# AGENT
# --------------------------------------------------

@app.post(
    "/api/agent/run",
    response_model=AgentRunResponse,
)
def run_agent(
    request: AgentRunRequest,
):
    """
    Route a natural-language request to the
    appropriate GHOST skill and execute it.
    """

    try:
        decision = route_request(
            request.request
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"GHOST could not route "
                f"the request: {error}"
            ),
        )

    missing_variables = (
        get_missing_variables(
            decision.skill,
            decision.variables,
        )
    )

    route = RouteResponse(
        skill=decision.skill,
        confidence=decision.confidence,
        variables=decision.variables,
        missing_variables=missing_variables,
        reason=decision.reason,
    )

    if missing_variables:
        return AgentRunResponse(
            routed=True,
            executed=False,
            route=route,
            task=None,
        )

    task = execute_agent_skill(
        skill_name=decision.skill,
        variables=decision.variables,
        original_request=request.request,
        requested_provider=request.provider,
    )

    return AgentRunResponse(
        routed=True,
        executed=True,
        route=route,
        task=task,
    )


@app.post(
    "/api/agent/continue",
    response_model=AgentRunResponse,
)
def continue_agent(
    request: AgentContinueRequest,
):
    """
    Continue an already-routed GHOST request
    after the user supplies missing inputs.

    The skill is NOT routed through the LLM again.
    """

    try:
        load_skill(
            request.skill
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Skill not found.",
        )

    missing_variables = (
        get_missing_variables(
            request.skill,
            request.variables,
        )
    )

    route = RouteResponse(
        skill=request.skill,
        confidence=request.confidence,
        variables=request.variables,
        missing_variables=missing_variables,
        reason=request.reason,
    )

    if missing_variables:
        return AgentRunResponse(
            routed=True,
            executed=False,
            route=route,
            task=None,
        )

    task = execute_agent_skill(
        skill_name=request.skill,
        variables=request.variables,
        original_request=request.original_request,
        requested_provider=request.provider,
    )

    return AgentRunResponse(
        routed=True,
        executed=True,
        route=route,
        task=task,
    )


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
    Execute a GHOST skill directly and
    persist the run.
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
        project_path = (
            request.variables.get(
                "project_path"
            )
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

    return clean_saved_research_task(
        task
    )


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