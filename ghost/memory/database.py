import sqlite3
from pathlib import Path

from ghost.models.action import Action


DB_PATH = Path("data/ghost.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

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

    connection.commit()
    connection.close()


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
