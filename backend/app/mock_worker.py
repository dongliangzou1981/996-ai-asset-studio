from pathlib import Path

from app.db import StudioDatabase
from app.job_runner import JobRunnerService
from app.schemas import GenerationJob


def run_mock_generation(
    database: StudioDatabase,
    upload_root: Path,
    generation_job_id: str,
) -> GenerationJob | None:
    return JobRunnerService(database, upload_root).run(generation_job_id)
