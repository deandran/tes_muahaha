"""Map messy English + Indonesian slang onto a structured game spec.

This is the cheap/free path. A paid LLM is optional and only used if a key exists.
"""

from __future__ import annotations

import re
from typing import Any

GENRE_RUNNER = "runner"
GENRE_ARENA = "arena"
GENRE_COLLECT = "collect"

GENRE_KEYWORDS = {
    GENRE_RUNNER: [
        "runner",
        "run",
        "dash",
        "endless",
        "parkour",
        "lari",
        "balapan",
        "kejar",
        "ngebut",
        "subway",
        "temple",
        "loncat",
        "jump",
        "ngelari",
        "lari-lari",
        "endless runner",
    ],
    GENRE_ARENA: [
        "arena",
        "brawler",
        "brawl",
        "fight",
        "fighter",
        "pukul",
        "gebuk",
        "gebukin",
        "tonjok",
        "bertarung",
        "tarung",
        "duel",
        "1v1",
        "versus",
        "vs",
        "pukulan",
        "kelahi",
        "hack and slash",
        "beat em up",
        "beatemup",
    ],
    GENRE_COLLECT: [
        "collect",
        "collector",
        "kumpul",
        "kumpulin",
        "ngumpulin",
        "koin",
        "coin",
        "item",
        "harta",
        "treasure",
        "cari",
        "nyari",
        "pickup",
        "star",
        "bintang",
        "buah",
        "fruit",
        "pac-man",
        "pacman",
    ],
}

COLOR_KEYWORDS = [
    ("merah", "#e24b4b", "red"),
    ("red", "#e24b4b", "red"),
    ("pink", "#ef7aa3", "pink"),
    ("ungu", "#7b5ea7", "purple"),
    ("purple", "#7b5ea7", "purple"),
    ("violet", "#7b5ea7", "purple"),
    ("biru", "#3d7ea6", "blue"),
    ("blue", "#3d7ea6", "blue"),
    ("cyan", "#3aa7b8", "cyan"),
    ("toska", "#3aa7b8", "cyan"),
    ("hijau", "#3d8b62", "green"),
    ("green", "#3d8b62", "green"),
    ("kuning", "#e0b33a", "yellow"),
    ("yellow", "#e0b33a", "yellow"),
    ("emas", "#d4a017", "gold"),
    ("gold", "#d4a017", "gold"),
    ("oranye", "#e07a3d", "orange"),
    ("orange", "#e07a3d", "orange"),
    ("oren", "#e07a3d", "orange"),
    ("hitam", "#2b2b2b", "black"),
    ("black", "#2b2b2b", "black"),
    ("putih", "#f4efe6", "white"),
    ("white", "#f4efe6", "white"),
    ("coklat", "#8b5a2b", "brown"),
    ("brown", "#8b5a2b", "brown"),
    ("abu", "#7a7a7a", "gray"),
    ("grey", "#7a7a7a", "gray"),
    ("gray", "#7a7a7a", "gray"),
]

SILHOUETTE_KEYWORDS = [
    ("naga", "dragon", ["horns", "tail", "snout"]),
    ("dragon", "dragon", ["horns", "tail", "snout"]),
    ("kucing", "cat", ["ears", "tail"]),
    ("cat", "cat", ["ears", "tail"]),
    ("meong", "cat", ["ears", "tail"]),
    ("anjing", "dog", ["ears", "snout", "tail"]),
    ("dog", "dog", ["ears", "snout", "tail"]),
    ("robot", "robot", ["antenna", "square-head"]),
    ("mecha", "robot", ["antenna", "square-head"]),
    ("penyihir", "mage", ["hat", "cape"]),
    ("witch", "mage", ["hat", "cape"]),
    ("wizard", "mage", ["hat", "cape"]),
    ("mage", "mage", ["hat", "cape"]),
    ("ksatria", "knight", ["helmet", "cape"]),
    ("knight", "knight", ["helmet", "cape"]),
    ("pahlawan", "hero", ["cape"]),
    ("hero", "hero", ["cape"]),
    ("ninja", "ninja", ["mask", "scarf"]),
    ("penguin", "penguin", ["beak", "belly"]),
    ("burung", "bird", ["beak", "wings"]),
    ("bird", "bird", ["beak", "wings"]),
    ("alien", "alien", ["antenna", "big-eyes"]),
    ("hantu", "ghost", ["wavy"]),
    ("ghost", "ghost", ["wavy"]),
    ("slime", "slime", ["blob"]),
    ("kodok", "frog", ["wide-mouth"]),
    ("frog", "frog", ["wide-mouth"]),
    ("ikan", "fish", ["fins"]),
    ("fish", "fish", ["fins"]),
    ("chef", "chef", ["hat"]),
    ("koki", "chef", ["hat"]),
    ("anak", "kid", []),
    ("kid", "kid", []),
    ("bocah", "kid", []),
]

ENEMY_FALLBACKS = {
    GENRE_RUNNER: ("Spike rocks", "spiky rocks on the path", "#6b5344"),
    GENRE_ARENA: ("Grumpy blobs", "round grumpy enemies", "#7a4c7a"),
    GENRE_COLLECT: ("Sneaky bats", "bats that steal your items", "#4a4a62"),
}

GOAL_FALLBACKS = {
    GENRE_RUNNER: ("Reach the finish line", "distance", 350),
    GENRE_ARENA: ("Defeat every enemy", "kills", 6),
    GENRE_COLLECT: ("Collect every star", "items", 8),
}


def _norm(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("’", "'")
    text = re.sub(r"[^a-z0-9\s\-+]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_genre(raw: str, picked: str | None = None) -> str:
    if picked in {GENRE_RUNNER, GENRE_ARENA, GENRE_COLLECT}:
        return picked
    blob = _norm(f"{picked or ''} {raw}")
    scores = {g: 0 for g in GENRE_KEYWORDS}
    for genre, words in GENRE_KEYWORDS.items():
        for word in words:
            if word in blob:
                scores[genre] += 2 if " " in word else 1
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return GENRE_COLLECT
    return best


def detect_color(text: str, fallback: str) -> tuple[str, str | None]:
    blob = _norm(text)
    for word, hex_color, name in COLOR_KEYWORDS:
        if re.search(rf"\b{re.escape(word)}\b", blob):
            return hex_color, name
    return fallback, None


EXTRA_WORDS = [
    ("cape", "cape"),
    ("jubah", "cape"),
    ("ekor", "tail"),
    ("tail", "tail"),
    ("tanduk", "horns"),
    ("horns", "horns"),
    ("hat", "hat"),
    ("topi", "hat"),
    ("antenna", "antenna"),
    ("antena", "antenna"),
    ("ears", "ears"),
    ("telinga", "ears"),
]


def extra_bits(text: str, existing: list[str]) -> list[str]:
    blob = _norm(text)
    extras = list(existing)
    for word, extra in EXTRA_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", blob) and extra not in extras:
            extras.append(extra)
    return extras


def detect_silhouette(text: str) -> tuple[str, list[str]]:
    blob = _norm(text)
    for word, name, extras in SILHOUETTE_KEYWORDS:
        if re.search(rf"\b{re.escape(word)}\b", blob):
            return name, extras
    return "hero", []


def guess_name(text: str, fallback: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return fallback
    # Quoted name: "his name is Kiki" / "namanya Budi"
    quoted = re.search(r'["“](.+?)["”]', raw)
    if quoted and 1 < len(quoted.group(1).strip()) < 24:
        return quoted.group(1).strip().title()
    named = re.search(
        r"(?:named|name is|namanya|dipanggil|panggilannya)\s+([A-Za-z][A-Za-z0-9']{1,20})",
        raw,
        re.I,
    )
    if named:
        return named.group(1).title()
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9']{2,20}", raw)
    skip = {
        "the",
        "and",
        "yang",
        "seorang",
        "seekor",
        "hero",
        "musuh",
        "enemy",
        "small",
        "little",
        "cute",
        "red",
        "blue",
        "green",
        "kecil",
        "lucu",
        "ganteng",
        "keren",
        "banget",
        "bangettt",
        "si",
        "sebuah",
        "player",
        "character",
        "karakter",
    }
    for token in tokens:
        if token.lower() not in skip and token[0].isupper():
            return token.title()
    if tokens:
        return tokens[0].title()
    return fallback


def detect_goal(text: str, genre: str) -> tuple[str, str, int]:
    blob = _norm(text)
    label, kind, target = GOAL_FALLBACKS[genre]
    if any(w in blob for w in ["koin", "coin", "bintang", "star", "item", "kumpul"]):
        kind, target = "items", 8
        label = text.strip() or "Collect the items"
    if any(w in blob for w in ["kalahin", "kalahkan", "defeat", "bunuh", "gebuk", "pukul"]):
        kind, target = "kills", 6
        label = text.strip() or "Defeat the enemies"
    if any(w in blob for w in ["finish", "garis", "sampai", "survive", "selamat"]):
        kind, target = "distance", 350
        label = text.strip() or "Reach the finish"
    numbers = re.findall(r"\b(\d{1,3})\b", blob)
    if numbers:
        target = max(3, min(20, int(numbers[0])))
        if kind == "distance":
            target = max(120, min(800, int(numbers[0]) * 10 if int(numbers[0]) < 80 else int(numbers[0])))
    return (text.strip() or label), kind, target


def build_ui_text(hero_name: str, genre: str, goal_text: str) -> dict[str, str]:
    titles = {
        GENRE_RUNNER: f"{hero_name} Dash",
        GENRE_ARENA: f"{hero_name} Brawl",
        GENRE_COLLECT: f"{hero_name}'s Hunt",
    }
    subs = {
        GENRE_RUNNER: "Jump. Don't trip. Keep going.",
        GENRE_ARENA: "Move in, land a hit, stay standing.",
        GENRE_COLLECT: "Grab the shiny things. Watch the clock.",
    }
    return {
        "title": titles[genre],
        "subtitle": goal_text[:80] or subs[genre],
        "win": "You did it!",
        "lose": "Almost. Try again.",
        "hint": {
            GENRE_RUNNER: "Tap / Space to jump",
            GENRE_ARENA: "WASD move · Space / tap to attack",
            GENRE_COLLECT: "WASD or arrows to move",
        }[genre],
    }


def answers_to_spec(answers: dict[str, Any]) -> dict[str, Any]:
    genre = detect_genre(answers.get("genre_text") or "", answers.get("genre"))
    hero_raw = answers.get("hero") or "a small brave kid"
    enemy_raw = answers.get("enemy") or ""
    goal_raw = answers.get("goal") or ""
    mood = (answers.get("mood") or "cozy").lower()

    hero_color, color_name = detect_color(hero_raw, "#3d8b62")
    sil, extras = detect_silhouette(hero_raw)
    extras = extra_bits(hero_raw, extras)
    hero_name = guess_name(hero_raw, "Hero")

    enemy_color, _ = detect_color(enemy_raw, ENEMY_FALLBACKS[genre][2])
    enemy_name = guess_name(enemy_raw, ENEMY_FALLBACKS[genre][0])
    if not enemy_raw.strip():
        enemy_raw = ENEMY_FALLBACKS[genre][1]

    goal_text, win_kind, target = detect_goal(goal_raw, genre)
    ui = build_ui_text(hero_name, genre, goal_text)

    palettes = {
        "cozy": {"sky": "#f0d9b5", "ground": "#7b8f4a", "fog": "#efe3cd"},
        "chaotic": {"sky": "#e07a3d", "ground": "#4a2c23", "fog": "#f3c9a3"},
        "cute": {"sky": "#f4c6d4", "ground": "#8fbf9a", "fog": "#ffe8f0"},
        "night": {"sky": "#24344d", "ground": "#1b2838", "fog": "#31445f"},
    }
    world = palettes.get(mood, palettes["cozy"])

    return {
        "genre": genre,
        "template_id": genre,
        "mood": mood,
        "hero": {
            "name": hero_name,
            "description": hero_raw.strip(),
            "primary_color": hero_color,
            "secondary_color": "#f4efe6",
            "accent_color": "#2b2b2b",
            "silhouette": sil,
            "extras": extras,
            "color_name": color_name,
        },
        "enemy": {
            "name": enemy_name,
            "description": enemy_raw.strip(),
            "primary_color": enemy_color,
        },
        "goal": {
            "text": goal_text,
            "win_condition": win_kind,
            "target": target,
        },
        "ui_text": ui,
        "world": {
            **world,
            "obstacle_color": enemy_color,
            "item_color": "#e0b33a",
        },
        "raw_answers": {
            "genre": answers.get("genre"),
            "genre_text": answers.get("genre_text"),
            "hero": hero_raw,
            "enemy": enemy_raw,
            "goal": goal_raw,
            "mood": mood,
        },
        "parser": "local-slang",
    }
