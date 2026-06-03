from fastapi import FastAPI

from app.schema import TABLE_NAMES

app = FastAPI(title="996 AI Asset Studio API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "996-ai-asset-studio-api"}


@app.get("/schema/tables")
def schema_tables() -> dict[str, list[str]]:
    return {"tables": TABLE_NAMES}

