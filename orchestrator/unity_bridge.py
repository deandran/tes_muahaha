"""Call Unity in headless batch mode, or fall back to the HTML5 player."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def unity_available() -> str | None:
    explicit = os.getenv("UNITY_EDITOR_PATH", "").strip()
    if explicit and Path(explicit).exists():
        return explicit
    candidates = [
        Path(r"C:\Program Files\Unity\Hub\Editor"),
        Path(r"C:\Program Files\Unity"),
    ]
    for root in candidates:
        if not root.exists():
            continue
        for exe in root.rglob("Unity.exe"):
            return str(exe)
    return None


def write_runtime_config(spec: dict[str, Any], dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    flat = {
        "genre": spec["genre"],
        "templateId": spec["template_id"],
        "heroName": spec["hero"]["name"],
        "heroColor": spec["hero"]["primary_color"],
        "heroLight": spec["hero"]["secondary_color"],
        "heroInk": spec["hero"]["accent_color"],
        "heroSilhouette": spec["hero"]["silhouette"],
        "heroExtras": ",".join(spec["hero"].get("extras") or []),
        "enemyName": spec["enemy"]["name"],
        "enemyColor": spec["enemy"]["primary_color"],
        "goalText": spec["goal"]["text"],
        "winCondition": spec["goal"]["win_condition"],
        "target": spec["goal"]["target"],
        "title": spec["ui_text"]["title"],
        "subtitle": spec["ui_text"]["subtitle"],
        "winText": spec["ui_text"]["win"],
        "loseText": spec["ui_text"]["lose"],
        "hint": spec["ui_text"]["hint"],
        "sky": spec["world"]["sky"],
        "ground": spec["world"]["ground"],
        "fog": spec["world"]["fog"],
        "obstacleColor": spec["world"]["obstacle_color"],
        "itemColor": spec["world"]["item_color"],
        "mood": spec.get("mood") or "cozy",
    }
    dest.write_text(json.dumps(flat, indent=2), encoding="utf-8")
    (dest.parent / "game_spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return dest


def pack_html5(job_id: str, spec: dict[str, Any], job_dir: Path) -> dict[str, Any]:
    delivery = ROOT / "data" / "deliveries" / job_id
    delivery.mkdir(parents=True, exist_ok=True)
    config_path = write_runtime_config(spec, delivery / "game_config.json")
    hero_src = job_dir / "hero_front.svg"
    if hero_src.exists():
        shutil.copy2(hero_src, delivery / "hero_front.svg")
    play_url = f"/play.html?job={job_id}"
    return {
        "kind": "html5",
        "path": str(delivery),
        "play_url": play_url,
        "config": str(config_path),
        "note": "Unity Editor not used. Same JSON a Unity template would read.",
    }


def build_unity(job_id: str, spec: dict[str, Any], job_dir: Path) -> dict[str, Any]:
    live = os.getenv("UNITY_BUILD_LIVE", "0") == "1"
    editor = unity_available()
    if not live or not editor:
        result = pack_html5(job_id, spec, job_dir)
        if not editor:
            result["fallback"] = "unity-missing"
            result["note"] = (
                "Unity Editor is not installed. Packed the HTML5 player that reads "
                "the same game_config.json the Unity templates use."
            )
        else:
            result["fallback"] = "unity-not-live"
            result["note"] = (
                "UNITY_BUILD_LIVE=0 so the demo never waits on a live Unity build. "
                "A pre-packed HTML5 player is ready."
            )
        return result

    project = Path(os.getenv("UNITY_PROJECT_PATH") or ROOT / "unity-templates" / "Shared")
    method = "GameLab.BatchBuild.BuildFromOrchestrator"
    log_file = job_dir / "unity_build.log"
    spec_path = write_runtime_config(spec, job_dir / "game_config.json")
    cmd = [
        editor,
        "-batchmode",
        "-nographics",
        "-quit",
        "-projectPath",
        str(project),
        "-executeMethod",
        method,
        "-logFile",
        str(log_file),
        "-buildTarget",
        os.getenv("UNITY_BUILD_TARGET", "WebGL"),
        f"-gameConfig={spec_path}",
        f"-outputDir={ROOT / 'data' / 'deliveries' / job_id / 'unity'}",
    ]
    try:
        completed = subprocess.run(cmd, check=False, timeout=900)
        if completed.returncode != 0:
            result = pack_html5(job_id, spec, job_dir)
            result["fallback"] = "unity-build-failed"
            result["unity_log"] = str(log_file)
            return result
        return {
            "kind": "unity",
            "play_url": f"/deliveries/{job_id}/unity/index.html",
            "path": str(ROOT / "data" / "deliveries" / job_id / "unity"),
            "note": "Unity batchmode build finished.",
        }
    except Exception as exc:
        result = pack_html5(job_id, spec, job_dir)
        result["fallback"] = "unity-exception"
        result["error"] = str(exc)
        return result
