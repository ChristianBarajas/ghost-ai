import json

from ghost.ai.client import ai_client
from ghost.memory.database import (
    initialize_database,
    get_actions,
)


def clean_action(action):
    return {
        "action_type": action["action_type"],
        "target": action["target"],
        "value": action["value"],
        "url": action["url"],
    }


def load_demonstration(
    workflow_id,
):
    actions = get_actions(
        workflow_id
    )

    return {
        "workflow_id": workflow_id,
        "actions": [
            clean_action(action)
            for action in actions
        ],
    }


def main():
    initialize_database()

    if not ai_client.is_available():
        print(
            "❌ GHOST AI is not available."
        )
        print(
            "Make sure OPENAI_API_KEY "
            "is loaded in this Terminal."
        )
        return

    demonstrations = [
        load_demonstration(10),
        load_demonstration(11),
    ]

    print()
    print(
        "🧠 GHOST AI WORKFLOW ANALYSIS"
    )
    print(
        "-----------------------------"
    )
    print(
        "Analyzing workflows #10 and #11..."
    )
    print()

    result = (
        ai_client.analyze_demonstrations(
            demonstrations
        )
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()