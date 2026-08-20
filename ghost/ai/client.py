class AIClient:
    """
    Central AI interface for GHOST.

    GHOST code should talk to this class instead of
    directly depending on a specific AI provider.
    """

    def __init__(self):
        self.enabled = False
        self.provider = None

    def is_available(self):
        return (
            self.enabled
            and self.provider is not None
        )

    def summarize(
        self,
        query,
        title,
        content,
    ):
        """
        Return an AI-generated research result.

        Expected future format:

        {
            "summary": "...",
            "key_terms": [...]
        }
        """

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
        """
        Eventually use an LLM to infer:

        - user intent
        - skill name
        - variables
        - semantic steps
        - required vs optional behavior
        """

        if not self.is_available():
            return None

        return self.provider.analyze_demonstrations(
            demonstrations
        )

    def connect_provider(
        self,
        provider,
    ):
        self.provider = provider
        self.enabled = True

    def disconnect_provider(self):
        self.provider = None
        self.enabled = False


ai_client = AIClient()