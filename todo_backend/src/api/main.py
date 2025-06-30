"""
todo_backend: FastAPI backend for the Todo App.
- Exposes RESTful endpoints for creating, reading, updating, and deleting todo tasks.
- Connects to the todo_database Python module for persistent storage.
- Handles core business logic: task completion, editing, filtering, and status updates.

API Docs: /docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import sys
import os

# Attempt to import todo_database
# Assume sibling container is mounted or available as a Python module, or else use absolute import.
_DB_CONTAINER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../todo_database")
)
if _DB_CONTAINER_PATH not in sys.path:
    sys.path.insert(0, _DB_CONTAINER_PATH)
try:
    import main as todo_db
except ImportError:
    raise RuntimeError(
        "todo_database module not found. Ensure todo_database/main.py is available and importable."
    )


# --- Pydantic models for DTOs ---


class TodoTaskCreate(BaseModel):
    """Payload for creating a new todo task."""
    title: str = Field(..., description="Title of the task")
    description: Optional[str] = Field(
        None, description="Description of the task"
    )


class TodoTaskUpdate(BaseModel):
    """Payload for updating a todo task."""
    title: Optional[str] = Field(None, description="Updated title of the task")
    description: Optional[str] = Field(None, description="Updated description")
    is_completed: Optional[bool] = Field(None, description="Completion status")


class TodoTaskOut(BaseModel):
    """Response model for a todo task."""
    id: int
    title: str
    description: Optional[str]
    is_completed: bool
    created_at: str
    updated_at: str


# OpenAPI tags metadata
openapi_tags = [
    {"name": "Tasks", "description": "Manage todo tasks (CRUD, status, filtering)."}
]


app = FastAPI(
    title="Todo App Backend API",
    description=(
        "RESTful API for creating, reading, updating, and deleting todo tasks with "
        "business logic (completion, editing, filtering, status)."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open CORS for all origins; restrict in production as needed.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def initialize_database():
    """Initialize the todo database on backend start."""
    todo_db.init_db()


# --- API Endpoints ---


# PUBLIC_INTERFACE
@app.get(
    "/health",
    tags=["Tasks"],
    summary="Health check",
    description="Backend health check endpoint."
)
def health_check():
    """A basic health check endpoint to verify the backend is up."""
    return {"status": "healthy"}


# PUBLIC_INTERFACE
@app.post(
    "/tasks",
    response_model=TodoTaskOut,
    tags=["Tasks"],
    summary="Create a todo task",
    description="Create a new todo task with title and optional description."
)
def create_task(task: TodoTaskCreate):
    """Creates a new todo task."""
    db_task = todo_db.create_task(title=task.title, description=task.description)
    if not db_task:
        raise HTTPException(status_code=500, detail="Task creation failed")
    db_task["is_completed"] = bool(db_task["is_completed"])
    return db_task


# PUBLIC_INTERFACE
@app.get(
    "/tasks",
    response_model=List[TodoTaskOut],
    tags=["Tasks"],
    summary="Get todo tasks (with optional filtering)",
    description="Retrieve the list of todo tasks, optionally filtered by completion status."
)
def list_tasks(
    status: Optional[Literal["all", "completed", "active"]] = Query(
        "all", description="Filter tasks by status: all, completed, or active"
    )
):
    """Retrieve all todo tasks, filter by status if provided."""
    tasks = todo_db.get_all_tasks()
    for task in tasks:
        task["is_completed"] = bool(task["is_completed"])
    if status == "completed":
        tasks = [t for t in tasks if t["is_completed"]]
    elif status == "active":
        tasks = [t for t in tasks if not t["is_completed"]]
    return tasks


# PUBLIC_INTERFACE
@app.get(
    "/tasks/{task_id}",
    response_model=TodoTaskOut,
    tags=["Tasks"],
    summary="Get a specific todo task by ID",
    description="Retrieve a specific todo task by its ID."
)
def get_task(task_id: int):
    """Fetch a todo task by its ID."""
    task = todo_db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    task["is_completed"] = bool(task["is_completed"])
    return task


# PUBLIC_INTERFACE
@app.put(
    "/tasks/{task_id}",
    response_model=TodoTaskOut,
    tags=["Tasks"],
    summary="Update a todo task by ID",
    description="Update the title, description, or completion status of a todo task."
)
def update_task(task_id: int, update: TodoTaskUpdate):
    """Update a task's title, description, or completion status."""
    new_task = todo_db.update_task(
        task_id=task_id,
        title=update.title,
        description=update.description,
        is_completed=update.is_completed,
    )
    if not new_task:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found or update failed.",
        )
    new_task["is_completed"] = bool(new_task["is_completed"])
    return new_task


# PUBLIC_INTERFACE
@app.delete(
    "/tasks/{task_id}",
    response_model=dict,
    tags=["Tasks"],
    summary="Delete a todo task by ID",
    description="Delete a todo task by its ID."
)
def delete_task(task_id: int):
    """Delete a todo task by its ID."""
    result = todo_db.delete_task(task_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    return {"success": True, "deleted_task_id": task_id}


# PUBLIC_INTERFACE
@app.patch(
    "/tasks/{task_id}/complete",
    response_model=TodoTaskOut,
    tags=["Tasks"],
    summary="Mark task as completed/incomplete",
    description="Mark a todo task as completed or incomplete."
)
def set_task_completed(
    task_id: int,
    is_completed: bool = Field(
        ...,
        description="Set to true to complete the task; false to mark as incomplete.",
    )
):
    """Set completion status for a task."""
    task = todo_db.update_task(task_id, is_completed=is_completed)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    task["is_completed"] = bool(task["is_completed"])
    return task


# Error handler for 422 Unprocessable Entity (validation errors)
@app.exception_handler(422)
def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()},
    )


# Add a doc route for backend API usage info (for websocket/real-time, would go here)
@app.get(
    "/api-docs",
    tags=["Tasks"],
    summary="API documentation/help",
    description="API usage information (see /docs for interactive UI and OpenAPI)."
)
def api_help():
    """Project-level API usage help note."""
    return {
        "endpoints": [
            "/tasks", "/tasks/{task_id}", "/tasks/{task_id}/complete"
        ],
        "filter_usage": "/tasks?status=all|completed|active",
        "docs": "/docs",
        "description": (
            "RESTful JSON API for creating, listing, updating, and deleting todo tasks. "
            "See /docs for full details."
        ),
    }
