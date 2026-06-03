# Provider Security

Sprint 7A does not run real OpenAI generation. It only prepares safe provider configuration and health checks.

## OpenAI Key Setup

Store the real key in a local environment variable:

```powershell
$env:OPENAI_API_KEY="your-real-key"
```

Do not commit keys to GitHub.

## Allowed config_json

`ai_providers.config_json` must not contain real keys. Store only the environment variable name:

```json
{
  "api_key_env": "OPENAI_API_KEY"
}
```

Forbidden examples:

```json
{
  "api_key": "sk-..."
}
```

```json
{
  "secret": "..."
}
```

The backend rejects config fields other than `api_key_env` and removes raw input from validation error responses.

## Health Check

- `mock`: returns `healthy`.
- `openai`: returns `healthy` only when `api_key_env` is configured and the named environment variable exists.
- `openai`: returns `unhealthy` when `api_key_env` is missing or the environment variable is not set.

Health responses never include the real API key.
