"""HTTP API + static UI. Orchestrator lives here, not inside Unity."""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .hunyuan import credits_status
from .llm import llm_available
from .pipeline import JOBS, ROOT, load_backup_game, run_pipeline
from .seed import seed
from .unity_bridge import unity_available

load_dotenv(ROOT / ".env")
seed()

WEB = ROOT / "web"
DELIVERIES = ROOT / "data" / "deliveries"
BACKUPS = ROOT / "backups"

app = FastAPI(title="Game Lab", version="0.1.0")
_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}


class Answers(BaseModel):
    genre: str | None = None
    genre_text: str | None = None
    hero: str = Field(..., min_length=1)
    enemy: str = ""
    goal: str = ""
    mood: str = "cozy"


def _job(job_id: str) -> dict[str, Any]:
    with _lock:
        job = _jobs.get(job_id)
    if job:
        return job
    state_path = JOBS / job_id / "state.json"
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    raise HTTPException(404, "unknown job")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "llm": llm_available() or "local-slang (free)",
        "unity": unity_available() or None,
        "unity_build_live": os.getenv("UNITY_BUILD_LIVE", "0") == "1",
        "delivery": os.getenv("DELIVERY_TARGET", "web"),
        "hunyuan": credits_status(),
    }


@app.post("/api/jobs")
def create_job(answers: Answers) -> dict[str, Any]:
    job_id = uuid.uuid4().hex[:10]
    record: dict[str, Any] = {
        "id": job_id,
        "status": "queued",
        "events": [],
        "answers": answers.model_dump(),
    }
    with _lock:
        _jobs[job_id] = record

    def emit(event: dict[str, Any]) -> None:
        event = {"t": time.time(), **event}
        with _lock:
            record["events"].append(event)
            if event.get("status") == "ready":
                record["status"] = "ready"
            elif event.get("step") == "done" and event.get("status") == "fallback":
                record["status"] = "ready"

    def worker() -> None:
        try:
            run_pipeline(job_id, answers.model_dump(), emit, demo_mode=True)
        except Exception as exc:
            emit({"step": "done", "status": "fallback", "caption": str(exc), **load_backup_game()})

    threading.Thread(target=worker, daemon=True).start()
    return {"id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    job = _job(job_id)
    if job_id in _jobs:
        with _lock:
            snap = {
                "id": job_id,
                "status": _jobs[job_id]["status"],
                "events": list(_jobs[job_id]["events"]),
            }
        state_path = JOBS / job_id / "state.json"
        if state_path.exists():
            snap["state"] = json.loads(state_path.read_text(encoding="utf-8"))
        return snap
    return job


@app.get("/api/jobs/{job_id}/events")
def job_events(job_id: str) -> StreamingResponse:
    if job_id not in _jobs and not (JOBS / job_id / "state.json").exists():
        raise HTTPException(404, "unknown job")

    def gen():
        idx = 0
        last = time.time()
        while True:
            with _lock:
                job = _jobs.get(job_id)
                events = list(job["events"]) if job else []
                status = job["status"] if job else "ready"
            while idx < len(events):
                yield f"data: {json.dumps(events[idx])}\n\n"
                idx += 1
                last = time.time()
            if status in {"ready", "failed"} and idx >= len(events):
                yield f"data: {json.dumps({'step': 'stream-end', 'status': status})}\n\n"
                break
            if time.time() - last > 90:
                break
            time.sleep(0.2)

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/backups")
def backups() -> dict[str, Any]:
    characters = []
    for folder in sorted((BACKUPS / "characters").glob("*")):
        if folder.is_dir():
            characters.append({"id": folder.name, "image": f"/backups/characters/{folder.name}/hero_front.svg"})
    return {
        "characters": characters,
        "game": load_backup_game(),
        "note": "Use these if anything fails on stage.",
    }


@app.post("/api/demo-panic")
def demo_panic() -> dict[str, Any]:
    return load_backup_game()


def _safe_file(folder: Path, filename: str) -> FileResponse:
    if "/" in filename or "\\" in filename or filename.startswith("."):
        raise HTTPException(404)
    path = (folder / filename).resolve()
    if folder.resolve() not in path.parents and path.parent != folder.resolve():
        raise HTTPException(404)
    if not path.exists() or not path.is_file():
        raise HTTPException(404)
    return FileResponse(path)


@app.get("/jobs/{job_id}/{filename}")
def job_file(job_id: str, filename: str) -> FileResponse:
    return _safe_file(JOBS / job_id, filename)


@app.get("/deliveries/{job_id}/{filename}")
def delivery_file(job_id: str, filename: str) -> FileResponse:
    return _safe_file(DELIVERIES / job_id, filename)


if BACKUPS.exists():
    app.mount("/backups", StaticFiles(directory=BACKUPS), name="backups")

app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
