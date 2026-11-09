from app.routers.tasks.schemas import TaskCreate, TaskPatch, TaskRead, TaskUpdate

from typing import Annotated
from fastapi import Path, Request

def read_task(request: Request, task_id: Annotated[int, Path(gt=0)]):