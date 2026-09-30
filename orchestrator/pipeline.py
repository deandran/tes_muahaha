"""Ordered pipeline with plain-language captions and template fallbacks."""

from __future__ import annotations

import json
import shutil
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .character import cache_key, write_hero_views
from .hunyuan import credits_status, generate_mesh
from .llm import enrich_spec_with_llm, llm_available
from .rig import write_rig
from .slang import answers_to_spec
from .unity_bridge import build_unity, write_runtime_config

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "data" / "jobs"
CACHE = ROOT / "cache" / "characters"
BACKUPS = ROOT / "backups"


Emit = Callable[[dict[str, Any]], None]


STEPS = [
    ("understand", "Reading your answers and turning them into a game plan."),
    ("draw", "Drawing your hero from the front, simple shapes, arms a little out."),
    ("cleanup", "Clearing the background so the 3D step only sees the silhouette."),
    ("sculpt", "Turning the drawing into a chunky 3D figure. Detail will live in the colors."),
    ("skeleton", "Adding a skeleton so your character can move."),
    ("template", "Dropping the hero into a prebuilt game template and filling in the colors."),
    ("build", "Packing a playable build. This is the slow seat — we stay honest about the wait."),
    ("ready", "Your game is ready to play."),
]


def new_job_dir(job_id: str) -> Path:
    path = JOBS / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_pipeline(job_id: str, answers: dict[str, Any], emit: Emit, demo_mode: bool = True) -> dict[str, Any]:
    job_dir = new_job_dir(job_id)
    state: dict[str, Any] = {
        "id": job_id,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": [],
        "demo_mode": demo_mode,
        "llm": llm_available() or "local-slang",
        "hunyuan": credits_status(),
    }
    _save(job_dir, state)

    def step(key: str, caption: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        emit({"step": key, "status": "running", "caption": caption})
        time.sleep(0.35)
        try:
            payload = fn()
            payload.setdefault("ok", True)
            emit({"step": key, "status": "done", "caption": caption, **payload})
            state["steps"].append({"key": key, "status": "done", **payload})
            _save(job_dir, state)
            return payload
        except Exception as exc:
            fallback = _fallback_for(key, job_id, job_dir, state)
            emit(
                {
                    "step": key,
                    "status": "fallback",
                    "caption": f"{caption} (using a backup — {exc})",
                    **fallback,
                }
            )
            state["steps"].append({"key": key, "status": "fallback", "error": str(exc), **fallback})
            _save(job_dir, state)
            return fallback

    spec_hold: dict[str, Any] = {}

    def understand() -> dict[str, Any]:
        local = answers_to_spec(answers)
        spec = enrich_spec_with_llm(answers, local)
        spec["id"] = job_id
        spec_hold.update(spec)
        (job_dir / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
        write_runtime_config(spec, job_dir / "game_config.json")
        return {"preview": spec["ui_text"]["title"], "spec": spec, "parser": spec.get("parser")}

    def draw() -> dict[str, Any]:
        hero = spec_hold["hero"]
        key = cache_key(hero)
        cached = CACHE / key
        if (cached / "hero_front.svg").exists():
            shutil.copytree(cached, job_dir, dirs_exist_ok=True)
            return {
                "image_url": f"/jobs/{job_id}/hero_front.svg",
                "source": "character-cache",
                "cache_key": key,
            }
        paths = write_hero_views(hero, job_dir)
        write_hero_views(hero, cached)
        return {
            "image_url": f"/jobs/{job_id}/hero_front.svg",
            "source": "procedural-svg",
            "cache_key": key,
            "views": {k: Path(v).name for k, v in paths.items()},
        }

    def cleanup() -> dict[str, Any]:
        # SVG is already transparent. Real rembg would hook in here for raster images.
        return {
            "image_url": f"/jobs/{job_id}/hero_front.svg",
            "note": "Background already empty. Raster rembg is skipped until image-gen exists.",
        }

    def sculpt() -> dict[str, Any]:
        key = cache_key(spec_hold["hero"])
        mesh = generate_mesh(str(job_dir / "hero_front.svg"), CACHE, key, demo_mode=demo_mode)
        shutil.copy2(mesh["path"], job_dir / "hero.obj")
        return {
            "mesh_url": f"/jobs/{job_id}/hero.obj",
            "source": mesh["source"],
            "spent_credit": mesh["spent_credit"],
            "hunyuan": credits_status(),
            "preview_3d": True,
        }

    def skeleton() -> dict[str, Any]:
        rig = write_rig(str(job_dir / "hero.obj"), job_dir, spec_hold["hero"])
        return {"rig": Path(rig["rig_json"]).name, "source": rig["source"]}

    def template() -> dict[str, Any]:
        return {
            "template": spec_hold["template_id"],
            "title": spec_hold["ui_text"]["title"],
            "note": "LLM only edits JSON. No generated C#.",
        }

    def build() -> dict[str, Any]:
        emit(
            {
                "step": "build",
                "status": "running",
                "caption": "Packing the game. A Unity WebGL build would be the long wait — we are not doing that live.",
            }
        )
        time.sleep(1.2)
        result = build_unity(job_id, spec_hold, job_dir)
        return result

    def ready() -> dict[str, Any]:
        play_url = f"/play.html?job={job_id}"
        for item in reversed(state["steps"]):
            if item.get("play_url"):
                play_url = item["play_url"]
                break
        state["play_url"] = play_url
        state["spec"] = spec_hold
        return {"play_url": play_url, "title": spec_hold.get("ui_text", {}).get("title")}

    try:
        step("understand", STEPS[0][1], understand)
        step("draw", STEPS[1][1], draw)
        step("cleanup", STEPS[2][1], cleanup)
        step("sculpt", STEPS[3][1], sculpt)
        step("skeleton", STEPS[4][1], skeleton)
        step("template", STEPS[5][1], template)
        step("build", STEPS[6][1], build)
        step("ready", STEPS[7][1], ready)
        state["status"] = "ready"
        state["finished_at"] = datetime.now(timezone.utc).isoformat()
        _save(job_dir, state)
        emit({"step": "done", "status": "ready", "caption": "Ready.", "play_url": state.get("play_url")})
        return state
    except Exception as exc:
        state["status"] = "failed"
        state["error"] = str(exc)
        state["trace"] = traceback.format_exc()
        _save(job_dir, state)
        backup = load_backup_game()
        emit(
            {
                "step": "done",
                "status": "fallback",
                "caption": "Something broke. Opening a finished backup game instead.",
                "play_url": backup["play_url"],
            }
        )
        return state


def _fallback_for(key: str, job_id: str, job_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    if key == "understand":
        spec_path = BACKUPS / "characters" / "sari" / "spec.json"
        if spec_path.exists():
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["id"] = job_id
            (job_dir / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
            return {"spec": spec, "source": "backup-spec"}
    if key in {"draw", "cleanup"}:
        src = BACKUPS / "characters" / "sari"
        if src.exists():
            shutil.copytree(src, job_dir, dirs_exist_ok=True)
        return {"image_url": f"/jobs/{job_id}/hero_front.svg", "source": "backup-character"}
    if key == "build":
        return load_backup_game()
    return {"ok": False, "source": "empty-fallback"}


def load_backup_game() -> dict[str, Any]:
    return {
        "kind": "backup",
        "play_url": "/play.html?job=backup-collect",
        "note": "Pre-built collect-items game. Never wait on a live Unity build on stage.",
    }


def _save(job_dir: Path, state: dict[str, Any]) -> None:
    (job_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
