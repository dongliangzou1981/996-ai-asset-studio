# Provider Security

Sprint 7B can run real OpenAI image generation when a local API key environment variable is configured. Automated tests use mocks and do not access the external OpenAI API.

## OpenAI Key Setup

Store the real key in a local environment variable:

```powershell
$env:OPENAI_API_KEY="your-real-key"
```

Do not commit keys to GitHub.
Do not write keys into `.env.local`, `ai_providers.config_json`, request logs, screenshots, or documentation.

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

For OpenAI and OpenRouter, the backend rejects config fields other than `api_key_env` and removes raw input from validation error responses. For Ofox, the backend allows `api_key_env`, `base_url`, and `model` so it can call an OpenAI Compatible endpoint without storing a real key.

## Health Check

- `mock`: returns `healthy`.
- `openai`: returns `healthy` only when `api_key_env` is configured and the named environment variable exists.
- `openai`: returns `unhealthy` when `api_key_env` is missing or the environment variable is not set.
- `ofox`: returns `healthy` only when `api_key_env` is configured and the named environment variable exists.

Health responses never include the real API key.

## Create an OpenAI Provider

Create an `openai` provider with only the environment variable name in `config_json`:

```http
POST /ai_providers
```

```json
{
  "name": "OpenAI Images",
  "type": "openai",
  "enabled": true,
  "config_json": "{\"api_key_env\":\"OPENAI_API_KEY\"}"
}
```

## Create a Real Generation Job

Use the provider id from the previous response:

```http
POST /generation_jobs
```

```json
{
  "project_id": null,
  "provider_id": "openai-provider-id",
  "job_type": "ui_generation",
  "status": "pending",
  "progress": 0,
  "input_json": "{\"prompt\":\"Generate a polished mobile game shop UI\",\"device_type\":\"mobile\",\"width\":1024,\"height\":1536}",
  "output_json": "",
  "output_preview_path": "",
  "error_message": "",
  "logs": "queued"
}
```

## Run the Job

```http
POST /generation_jobs/{generation_job_id}/run
```

On success, the job moves to `completed`, creates `ai_generated` assets, writes thumbnails, and stores result paths plus asset ids in `output_json`.

On failure, the job moves to `failed`, writes a short `error_message`, appends logs, and never returns the API key.

## View Results

Use these endpoints or the frontend pages:

- `GET /generation_jobs/{generation_job_id}`
- `GET /generation_jobs/{generation_job_id}/results`
- `/job-center`
- `/assets?generation_job_id={generation_job_id}`

Generated assets use `source = ai_generated` and are linked to `generation_job_id`.

## Create an Ofox Provider

Store the real Ofox key in a local environment variable:

```powershell
$env:OFOX_API_KEY="your-real-key"
```

Create an `ofox` provider with OpenAI Compatible routing settings:

```json
{
  "name": "Ofox UI",
  "type": "ofox",
  "enabled": true,
  "config_json": "{\"api_key_env\":\"OFOX_API_KEY\",\"base_url\":\"https://your-ofox-compatible-endpoint/v1\",\"model\":\"your-ofox-image-model\"}"
}
```

On success, Ofox creates an `ai_generated` `ui_preview` asset, then automatically creates `component_processing` sliced components, Chinese `annotation.json`, `manifest.json`, and `preview.html`.
