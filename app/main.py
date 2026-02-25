from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from celery.result import AsyncResult
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.celery_app import celery_app
from app.db import fetch_picks, init_db, latest_run, latest_runs
from app.jobs import shutdown_scheduler, start_scheduler
from app.tasks import export_latest_to_sheet_task, run_sctr_pipeline_task


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="Dreamlist SCTR", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/picks/latest")
def api_latest_picks(
    q: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    run = latest_run()
    if not run:
        return {"status": "empty", "data": [], "total": 0, "page": page, "page_size": page_size}

    offset = (page - 1) * page_size
    total, rows = fetch_picks(int(run["id"]), q=q, offset=offset, limit=page_size)
    return {
        "status": "ok",
        "run": dict(run),
        "data": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@app.get("/api/runs/latest")
def api_latest_runs(limit: int = Query(default=10, ge=1, le=100)):
    rows = latest_runs(limit=limit)
    return {"status": "ok", "data": [dict(r) for r in rows]}


@app.post("/api/jobs/run")
def api_run_job():
    task = run_sctr_pipeline_task.delay(source="manual")
    return {"status": "queued", "task_id": task.id}


@app.post("/api/jobs/export-latest")
def api_export_latest():
    task = export_latest_to_sheet_task.delay()
    return {"status": "queued", "task_id": task.id}


@app.get("/api/jobs/status/{task_id}")
def api_job_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    payload = {
        "task_id": task_id,
        "state": result.state,
        "result": result.result if result.successful() else None,
    }
    if result.failed():
        payload["error"] = str(result.result)
    return payload
