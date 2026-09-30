"""Create the 3 backup characters and 1 finished backup game."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .character import write_hero_views
from .slang import answers_to_spec
from .unity_bridge import write_runtime_config

ROOT = Path(__file__).resolve().parent.parent
BACKUPS = ROOT / "backups"


CHARACTERS = {
    "sari": {
        "genre": "collect",
        "genre_text": "",
        "hero": "a small orange kid named Sari with a cape",
        "enemy": "sneaky purple bats",
        "goal": "collect 8 stars",
        "mood": "cute",
    },
    "bima": {
        "genre": "runner",
        "genre_text": "",
        "hero": "a green dragon kid named Bima with horns and a tail",
        "enemy": "brown spike rocks",
        "goal": "reach the finish line",
        "mood": "cozy",
    },
    "nuri": {
        "genre": "arena",
        "genre_text": "",
        "hero": "a purple robot named Nuri with an antenna",
        "enemy": "grumpy red blobs",
        "goal": "defeat 6 enemies",
        "mood": "chaotic",
    },
}


def seed() -> None:
    (BACKUPS / "characters").mkdir(parents=True, exist_ok=True)
    (BACKUPS / "games" / "collect").mkdir(parents=True, exist_ok=True)
    for name, answers in CHARACTERS.items():
        spec = answers_to_spec(answers)
        spec["id"] = f"backup-{name}"
        folder = BACKUPS / "characters" / name
        folder.mkdir(parents=True, exist_ok=True)
        write_hero_views(spec["hero"], folder)
        (folder / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
        write_runtime_config(spec, folder / "game_config.json")

    # Fully pre-built collect game (the on-stage panic button).
    sari = BACKUPS / "characters" / "sari"
    dest = BACKUPS / "games" / "collect"
    for fname in ("hero_front.svg", "game_config.json", "spec.json"):
        src = sari / fname
        if src.exists():
            shutil.copy2(src, dest / fname)
    note = dest / "README.txt"
    note.write_text(
        "Pre-built playable game. Open /play.html?job=backup-collect\n"
        "Keep this around so you never wait on a live Unity build on stage.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    seed()
    print("backups ready")
