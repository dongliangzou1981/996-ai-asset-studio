import json
import os

from app.schemas import AiProvider


def provider_health(provider: AiProvider) -> dict[str, str | bool]:
    if provider.type == "mock":
        return {
            "id": provider.id,
            "name": provider.name,
            "type": provider.type,
            "enabled": provider.enabled,
            "status": "healthy",
            "message": "Mock provider is available locally",
        }

    if provider.type == "openai":
        try:
            config = json.loads(provider.config_json or "{}")
        except json.JSONDecodeError:
            return unhealthy(provider, "config_json must be valid JSON")

        api_key_env = config.get("api_key_env")
        if not api_key_env:
            return unhealthy(provider, "OpenAI provider requires config_json.api_key_env")
        if not isinstance(api_key_env, str):
            return unhealthy(provider, "config_json.api_key_env must be a string")
        if not os.getenv(api_key_env):
            return unhealthy(provider, f"Environment variable {api_key_env} is not set")
        return {
            "id": provider.id,
            "name": provider.name,
            "type": provider.type,
            "enabled": provider.enabled,
            "status": "healthy",
            "message": f"Environment variable {api_key_env} is configured",
        }

    if provider.type == "custom":
        return {
            "id": provider.id,
            "name": provider.name,
            "type": provider.type,
            "enabled": provider.enabled,
            "status": "healthy",
            "message": "Custom provider config is accepted",
        }

    return unhealthy(provider, "Unknown provider type")


def unhealthy(provider: AiProvider, message: str) -> dict[str, str | bool]:
    return {
        "id": provider.id,
        "name": provider.name,
        "type": provider.type,
        "enabled": provider.enabled,
        "status": "unhealthy",
        "message": message,
    }
