PROVIDERS = {
    "web_search": {
        "duckduckgo": {
            "start_url": "https://duckduckgo.com/",
            "submit_strategy": "enter",
        },
        "bing": {
            "start_url": "https://www.bing.com/",
            "submit_strategy": "form",
        },
    }
}


DEFAULT_PROVIDERS = {
    "web_search": "duckduckgo",
}


def get_provider(
    skill_name: str,
    provider_name=None,
):
    """
    Return provider configuration for a skill.

    If no provider is explicitly requested,
    use the default provider for that skill.
    """

    skill_providers = PROVIDERS.get(
        skill_name,
        {}
    )

    if not skill_providers:
        return None

    if provider_name is None:
        provider_name = DEFAULT_PROVIDERS.get(
            skill_name
        )

    provider = skill_providers.get(
        provider_name
    )

    if provider is None:
        available = ", ".join(
            skill_providers.keys()
        )

        raise ValueError(
            f"Unknown provider '{provider_name}' "
            f"for skill '{skill_name}'. "
            f"Available providers: {available}"
        )

    return {
        "name": provider_name,
        **provider,
    }