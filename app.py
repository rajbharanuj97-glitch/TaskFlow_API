
from fastapi import Body, FastAPI, HTTPException, Query

from database import run_query

app = FastAPI(
    title="TaskFlow API",
    description="A FastAPI and PostgreSQL project for managing tasks.",
    version="1.0.0",
)


def clean_title(title): 
    title = title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Title cannot be blank.")
    return title


@app.get("/", tags=["Health"])
def home():
    # This checks the API process, not the database connection.
    return {"message": "TaskFlow API is running. Open /docs to try it."}


@app.post("/tasks", status_code=201, tags=["Tasks"])
def create_task(
    title: str = Body(min_length=1, max_length=120),
    description: str = Body(default="", max_length=2000),
    status: str = Body(default="todo", pattern="^(todo|in progress|done)$"),
):
    return run_query(
        """INSERT INTO tasks (title, description, status)
           VALUES (%s, %s, %s) RETURNING *""",
        (clean_title(title), description.strip(), status),
        fetch="one",
    )


@app.get("/tasks", tags=["Tasks"])
def list_tasks(status: str = Query(default=None, pattern="^(todo|in progress|done)$")):
    if status is not None:
        return run_query("SELECT * FROM tasks WHERE status = %s ORDER BY id", (status,))
    return run_query("SELECT * FROM tasks ORDER BY id")


@app.get("/tasks/{task_id}", tags=["Tasks"])
def get_task(task_id: int):
    task = run_query("SELECT * FROM tasks WHERE id = %s", (task_id,), fetch="one")
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


@app.put("/tasks/{task_id}", tags=["Tasks"])
def update_task(
    task_id: int,
    title: str = Body(min_length=1, max_length=120),
    description: str = Body(default="", max_length=2000),
    status: str = Body(default="todo", pattern="^(todo|in progress|done)$"),
):
    # PUT replaces all editable fields. Send the full task body.
    updated_task = run_query(
        """UPDATE tasks SET title = %s, description = %s, status = %s,
           updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *""",
        (clean_title(title), description.strip(), status, task_id),
        fetch="one",
    )
    if updated_task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return updated_task


@app.delete("/tasks/{task_id}", tags=["Tasks"])
def delete_task(task_id: int):
    deleted_task = run_query("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,), fetch="one")
    if deleted_task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"message": "Task deleted.", "id": deleted_task["id"]}
