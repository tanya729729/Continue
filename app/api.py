from app.core.config import load_settings
from app.main import build_service
from typing import Annotated
from fastapi import HTTPException, Path, Request,Query,FastAPI,status
from app.errors import TaskNotFoundError
from app.routers.tasks.schemas import TaskCreate, TaskRead
from fastapi import Response
from app.routers.tasks import router as tasks_router
from app.routers.tasks.router import router as tasks_router

settings = load_settings()
app = FastAPI(title=settings.app_name)
app.state.settings = settings
app.state.planner = build_service(settings=settings)
app.include_router(tasks_router)

def _task_read_data(task):
    return {
        "id": task.id,
        "title": task.title,
        "priority": task.priority,
        "is_done": task.is_done,
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/stats")
def read_stats(request: Request):
    statistics = request.app.state.planner.get_statistics()
    return {
        "total": statistics["all"],
        "open": statistics["open"],
        "done": statistics["done"],
    }


@app.get("/tasks", response_model=list[TaskRead])
def read_tasks(
    is_done: bool | None = None,
    sort_desc: bool = False,
    limit: int = Query(default=10, ge=1, le=50),
):
    tasks = app.state.planner.select_tasks(
        is_done=is_done,
        sort_desc=sort_desc,
        limit=limit,
    )
    return [
        {
            "id": task.id,
            "title": task.title,
            "priority": task.priority,
            "is_done": task.is_done,
        }
        for task in tasks
    ]


@app.get("/tasks/{task_id}", response_model=TaskRead)
def read_task(task_id: int):
    try:
        task = app.state.planner.get_task(task_id)
    except TaskNotFoundError as error:
        raise HTTPException(status_code=404, detail="Task not found") from error
    return {
        "id": task.id,
        "title": task.title,
        "priority": task.priority,
        "is_done": task.is_done,
    }


@app.post(
    "/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task(payload: TaskCreate):
    try:
        task = app.state.planner.add_task(
            payload.title,
            priority=payload.priority,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    return {
        "id": task.id,
        "title": task.title,
        "priority": task.priority,
        "is_done": task.is_done,
    }

@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: Annotated[int, Path(gt=0)],
    payload: TaskUpdate,
    request: Request,
):
    return _call_with_task_not_found_as_404(
        request.app.state.planner.replace_task,
        task_id,
        title=payload.title,
        priority=payload.priority,
        is_done=payload.is_done,
    )


@app.patch("/tasks/{task_id}", response_model=TaskRead)
def patch_task_endpoint(
    request: Request,
    task_id: Annotated[int, Path(gt=0)],
    payload: TaskPatch,
):
    changes = payload.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )
    task = _call_with_task_not_found_as_404(
        request.app.state.planner.patch_task,
        task_id,
        **changes,
    )
    return _task_read_data(task)



@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(request: Request, task_id: Annotated[int, Path(gt=0)]) -> Response:
    _call_with_task_not_found_as_404(
        request.app.state.planner.delete_task,
        task_id,
    )
    return Response(status_code=204)


