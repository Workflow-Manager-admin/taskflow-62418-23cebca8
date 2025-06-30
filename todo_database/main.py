"""
todo_database: Persistent storage for todo tasks.
- Provides SQL database schema and basic CRUD operations for tasks.
- Intended for use by the todo_backend via direct DB access or as a database service.

Database: SQLite (for easy containerization and portability).
Location: ./todo_db.sqlite3
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import List, Optional, Dict

DB_FILENAME = os.environ.get("TODO_DB_FILENAME", "./todo_db.sqlite3")

def _get_db_conn():
    conn = sqlite3.connect(DB_FILENAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the todo tasks table if it doesn't exist."""
    with _get_db_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todo_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                is_completed INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

# PUBLIC_INTERFACE
def create_task(title: str, description: Optional[str] = None) -> Dict:
    """Create a new todo task."""
    conn = _get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO todo_tasks (title, description) VALUES (?, ?)",
        (title, description)
    )
    conn.commit()
    task_id = cur.lastrowid
    cur.execute("SELECT * FROM todo_tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else {}

# PUBLIC_INTERFACE
def get_task(task_id: int) -> Optional[Dict]:
    """Retrieve a todo task by its id."""
    conn = _get_db_conn()
    row = conn.execute("SELECT * FROM todo_tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

# PUBLIC_INTERFACE
def get_all_tasks() -> List[Dict]:
    """Retrieve all todo tasks."""
    conn = _get_db_conn()
    rows = conn.execute("SELECT * FROM todo_tasks ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

# PUBLIC_INTERFACE
def update_task(task_id: int, title: Optional[str] = None, description: Optional[str] = None, is_completed: Optional[bool] = None) -> Optional[Dict]:
    """
    Update a todo task's fields.
    """
    conn = _get_db_conn()
    fields = []
    values = []
    if title is not None:
        fields.append('title = ?')
        values.append(title)
    if description is not None:
        fields.append('description = ?')
        values.append(description)
    if is_completed is not None:
        fields.append('is_completed = ?')
        values.append(1 if is_completed else 0)

    if not fields:
        conn.close()
        return get_task(task_id)

    fields.append('updated_at = CURRENT_TIMESTAMP')
    set_clause = ', '.join(fields)
    values.append(task_id)
    conn.execute(f"UPDATE todo_tasks SET {set_clause} WHERE id = ?", values)
    conn.commit()
    row = conn.execute("SELECT * FROM todo_tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

# PUBLIC_INTERFACE
def delete_task(task_id: int) -> bool:
    """
    Delete a todo task by its id. Returns True if deleted, False otherwise.
    """
    conn = _get_db_conn()
    cur = conn.execute("DELETE FROM todo_tasks WHERE id = ?", (task_id,))
    conn.commit()
    rows_deleted = cur.rowcount
    conn.close()
    return rows_deleted > 0

# Optionally: Run DB initialization if module executed directly.
if __name__ == "__main__":
    print("Initializing todo_database ...")
    init_db()
    print("Database initialized.")

