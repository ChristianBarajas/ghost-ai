import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from ghost.models.action import Action


DB_PATH = Path("data/ghost.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()

    # Existing observed workflows.
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Existing recorded workflow actions.
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            target TEXT,
            value TEXT,
            url TEXT,
            timestamp TEXT NOT NULL,

            FOREIGN KEY(workflow_id)
                REFERENCES workflows(id)
        )
        """
    )

    # GHOST v0.3 persistent task execution history.
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            provider TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'running',
            success INTEGER,
            verified INTEGER,
            skill TEXT,
            result_json TEXT,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


# --------------------------------------------------
# OBSERVED WORKFLOWS
# --------------------------------------------------

def create_workflow(name: str) -> int:
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO workflows (name)
        VALUES (?)
        """,
        (name,),
    )

    workflow_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return workflow_id


def save_action(workflow_id: int, action: Action):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO actions (
            workflow_id,
            action_type,
            target,
            value,
            url,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            workflow_id,
            action.action_type,
            action.target,
            action.value,
            action.url,
            action.timestamp.isoformat(),
        ),
    )

    connection.commit()
    connection.close()


def get_actions(workflow_id: int):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM actions
        WHERE workflow_id = ?
        ORDER BY id ASC
        """,
        (workflow_id,),
    ).fetchall()

    connection.close()

    return rows


# --------------------------------------------------
# TASK EXECUTION HISTORY
# --------------------------------------------------

def create_task_record(
    query: str,
    provider: str,
) -> int:
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO tasks (
            query,
            provider,
            status
        )
        VALUES (?, ?, 'running')
        """,
        (
            query,
            provider,
        ),
    )

    task_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return task_id


def update_task_record(
    task_id: int,
    *,
    status: str,
    success: Optional[bool] = None,
    verified: Optional[bool] = None,
    skill: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
):
    connection = get_connection()

    result_json = (
        json.dumps(result)
        if result is not None
        else None
    )

    connection.execute(
        """
        UPDATE tasks
        SET
            status = ?,
            success = ?,
            verified = ?,
            skill = ?,
            result_json = ?,
            error = ?,
            completed_at = CASE
                WHEN ? IN ('completed', 'failed')
                THEN CURRENT_TIMESTAMP
                ELSE completed_at
            END
        WHERE id = ?
        """,
        (
            status,
            int(success) if success is not None else None,
            int(verified) if verified is not None else None,
            skill,
            result_json,
            error,
            status,
            task_id,
        ),
    )

    connection.commit()
    connection.close()


def _task_row_to_dict(row):
    if row is None:
        return None

    result = None

    if row["result_json"]:
        try:
            result = json.loads(row["result_json"])
        except json.JSONDecodeError:
            result = None

    return {
        "task_id": row["id"],
        "status": row["status"],
        "query": row["query"],
        "provider": row["provider"],
        "success": (
            bool(row["success"])
            if row["success"] is not None
            else None
        ),
        "verified": (
            bool(row["verified"])
            if row["verified"] is not None
            else None
        ),
        "skill": row["skill"],
        "result": result,
        "error": row["error"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
    }


def get_task_record(task_id: int):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    ).fetchone()

    connection.close()

    return _task_row_to_dict(row)


def list_task_records(limit: int = 50):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM tasks
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    connection.close()

    return [
        _task_row_to_dict(row)
        for row in rows
    ]