# todo_database

Persistent data layer for todo tasks for the fullstack todo application.

## Features

- SQLite-based persistent storage for todo tasks
- Schema: `todo_tasks` table with columns id, title, description, is_completed, created_at, updated_at
- Python module exposing basic CRUD operations for use by the backend

## Usage

- Import and call CRUD functions (create_task, get_task, get_all_tasks, update_task, delete_task)
- Database file location for persistent storage defaults to `todo_db.sqlite3` (can be overridden with `TODO_DB_FILENAME` env var)
- To initialize database: run `python main.py` in this folder
- To use from the backend, import and invoke the functions, or extend for direct API/db access as needed.

## Extending

- Switch to PostgreSQL or another RDBMS by replacing sqlite3 connection logic (if you prefer containerized database).
- This module is flexible for upgrade to separate DB engine.

