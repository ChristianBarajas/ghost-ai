import os

from ghost.ai.providers.openai_provider import (
    OpenAIProvider,
)


class AIClient:
    def __init__(self):
        self.provider = None

        self._connect_from_environment()

    def _connect_from_environment(self):
        """
        Automatically enable OpenAI when an
        OPENAI_API_KEY exists in the environment.
        """

        api_key = os.environ.get(
            "OPENAI_API_KEY"
        )

        if not api_key:
            return

        try:
            self.provider = OpenAIProvider()

        except Exception as error:
            print(
                f"⚠️ Could not initialize "
                f"GHOST AI: {error}"
            )

            self.provider = None

    def is_available(self):
        return self.provider is not None

    def summarize(
        self,
        query,
        title,
        content,
    ):
        if not self.is_available():
            return None

        return self.provider.summarize(
            query=query,
            title=title,
            content=content,
        )

    def analyze_demonstrations(
        self,
        demonstrations,
    ):
        if not self.is_available():
            return None

        return self.provider.analyze_demonstrations(
            demonstrations
        )


ai_client = AIClient()