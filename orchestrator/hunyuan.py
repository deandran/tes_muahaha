"""Hunyuan 3D adapter.

Hard-capped. Cached. Never spends a credit unless explicitly enabled.
Image/prompt steps must succeed first — the pipeline calls this last.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CREDIT_FILE = ROOT / "data" / "hunyuan_credits.json"


def _load_credits() -> dict[str, Any]:
    CREDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if CREDIT_FILE.exists():
        return json.loads(CREDIT_FILE.read_text(encoding="utf-8"))
    data = {"used": 0, "max": int(os.getenv("HUNYUAN_MAX_GENERATIONS", "20")), "log": []}
    CREDIT_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def credits_status() -> dict[str, Any]:
    data = _load_credits()
    return {
        "used": data["used"],
        "max": data.get("max", 20),
        "remaining": max(0, data.get("max", 20) - data["used"]),
        "enabled": os.getenv("HUNYUAN_ENABLED", "0") == "1" and bool(os.getenv("HUNYUAN_API_KEY")),
    }


def generate_mesh(image_path: str, cache_dir: Path, cache_id: str, demo_mode: bool = True) -> dict[str, Any]:
    """Return a mesh path. Prefers cache. Falls back to a local low-poly OBJ.

    Real Hunyuan is only called when HUNYUAN_ENABLED=1, a key exists, credits remain,
    and demo_mode is False.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{cache_id}.obj"
    if cached.exists():
        return {"path": str(cached), "source": "cache", "spent_credit": False}

    status = credits_status()
    can_call = (
        status["enabled"]
        and status["remaining"] > 0
        and not demo_mode
        and os.getenv("HUNYUAN_API_URL")
    )
    if can_call:
        # Intentionally unimplemented until a key + endpoint exist.
        # Do not invent a spend. Fall through to local mesh.
        pass

    obj = _procedural_obj(image_path)
    cached.write_text(obj, encoding="utf-8")
    reason = "demo-safe local mesh"
    if not status["enabled"]:
        reason = "Hunyuan off — local low-poly mesh (texture, not geometry)"
    elif status["remaining"] <= 0:
        reason = "Hunyuan credit cap reached — using local mesh"
    return {"path": str(cached), "source": reason, "spent_credit": False}


def _procedural_obj(_image_path: str) -> str:
    # Very low-poly A-pose humanoid. Detail is meant to come from textures later.
    verts = [
        (0, 1.7, 0),
        (0.22, 1.55, 0.12),
        (-0.22, 1.55, 0.12),
        (0.22, 1.55, -0.12),
        (-0.22, 1.55, -0.12),
        (0.18, 1.35, 0.1),
        (-0.18, 1.35, 0.1),
        (0.28, 0.95, 0.12),
        (-0.28, 0.95, 0.12),
        (0.28, 0.95, -0.12),
        (-0.28, 0.95, -0.12),
        (0.7, 1.25, 0),
        (-0.7, 1.25, 0),
        (0.95, 0.85, 0),
        (-0.95, 0.85, 0),
        (0.16, 0.0, 0.08),
        (-0.16, 0.0, 0.08),
        (0.22, 0.55, 0.08),
        (-0.22, 0.55, 0.08),
    ]
    faces = [
        (1, 2, 3),
        (1, 3, 4),
        (1, 4, 5),
        (1, 5, 2),
        (6, 7, 8),
        (7, 11, 9),
        (6, 8, 10),
        (12, 6, 14),
        (13, 15, 7),
        (8, 18, 16),
        (9, 19, 17),
    ]
    lines = ["# local low-poly stand-in for Hunyuan", "o Hero"]
    for x, y, z in verts:
        lines.append(f"v {x:.3f} {y:.3f} {z:.3f}")
    for a, b, c in faces:
        lines.append(f"f {a} {b} {c}")
    return "\n".join(lines) + "\n"
