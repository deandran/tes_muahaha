"""Constrained character image: front, stylized, low-poly, A-pose, plain/transparent bg."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def cache_key(hero: dict[str, Any]) -> str:
    blob = "|".join(
        [
            hero.get("silhouette") or "",
            hero.get("primary_color") or "",
            hero.get("name") or "",
            ",".join(hero.get("extras") or []),
        ]
    )
    return hashlib.sha1(blob.encode()).hexdigest()[:12]


def generate_hero_svg(hero: dict[str, Any]) -> str:
    fill = hero.get("primary_color") or "#3d8b62"
    ink = hero.get("accent_color") or "#2b2b2b"
    light = hero.get("secondary_color") or "#f4efe6"
    extras = set(hero.get("extras") or [])
    sil = hero.get("silhouette") or "hero"

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="768" viewBox="0 0 512 768">',
        "  <!-- Transparent background on purpose. Hunyuan prefers a clean silhouette. -->",
        '  <g stroke="' + ink + '" stroke-width="7" stroke-linejoin="round" stroke-linecap="round">',
    ]

    # Legs (A-pose stance, feet apart)
    parts.append(f'    <polygon fill="{fill}" points="186,430 230,430 218,690 150,690"/>')
    parts.append(f'    <polygon fill="{fill}" points="282,430 326,430 362,690 294,690"/>')
    parts.append(f'    <polygon fill="{light}" points="150,668 218,668 218,690 150,690"/>')
    parts.append(f'    <polygon fill="{light}" points="294,668 362,668 362,690 294,690"/>')

    # Torso
    parts.append(f'    <polygon fill="{fill}" points="196,250 316,250 336,440 176,440"/>')

    # Arms slightly out — A-pose
    parts.append(f'    <polygon fill="{fill}" points="196,260 176,270 70,390 110,412 196,318"/>')
    parts.append(f'    <polygon fill="{fill}" points="316,260 336,270 442,390 402,412 316,318"/>')
    parts.append(f'    <polygon fill="{light}" points="70,390 110,412 96,430 56,408"/>')
    parts.append(f'    <polygon fill="{light}" points="442,390 402,412 416,430 456,408"/>')

    # Head
    if sil == "robot" or "square-head" in extras:
        parts.append(f'    <polygon fill="{fill}" points="186,90 326,90 326,230 186,230"/>')
        parts.append(f'    <rect x="214" y="140" width="28" height="28" fill="{light}"/>')
        parts.append(f'    <rect x="270" y="140" width="28" height="28" fill="{light}"/>')
    elif sil == "slime" or "blob" in extras:
        parts.append(f'    <ellipse cx="256" cy="200" rx="90" ry="110" fill="{fill}"/>')
        parts.append(f'    <circle cx="230" cy="180" r="12" fill="{ink}"/>')
        parts.append(f'    <circle cx="282" cy="180" r="12" fill="{ink}"/>')
    else:
        parts.append(f'    <polygon fill="{fill}" points="256,70 340,150 310,240 202,240 172,150"/>')
        parts.append(f'    <polygon fill="{light}" points="226,175 246,175 246,195 226,195"/>')
        parts.append(f'    <polygon fill="{light}" points="266,175 286,175 286,195 266,195"/>')

    if "horns" in extras:
        parts.append(f'    <polygon fill="{light}" points="186,120 170,46 226,100"/>')
        parts.append(f'    <polygon fill="{light}" points="326,120 342,46 286,100"/>')
    if "ears" in extras:
        parts.append(f'    <polygon fill="{fill}" points="186,110 150,40 226,96"/>')
        parts.append(f'    <polygon fill="{fill}" points="326,110 362,40 286,96"/>')
    if "hat" in extras:
        parts.append(f'    <polygon fill="{ink}" points="160,120 256,24 352,120 256,96"/>')
    if "antenna" in extras:
        parts.append(f'    <line x1="256" y1="90" x2="256" y2="28"/>')
        parts.append(f'    <circle cx="256" cy="22" r="10" fill="{light}"/>')
    if "cape" in extras:
        parts.append(f'    <polygon fill="{ink}" points="196,260 316,260 380,500 132,500" opacity="0.85"/>')
    if "tail" in extras:
        parts.append(f'    <polygon fill="{fill}" points="176,430 150,430 70,560 110,570 176,470"/>')
    if "beak" in extras:
        parts.append(f'    <polygon fill="{light}" points="246,200 266,200 256,236"/>')
    if "mask" in extras:
        parts.append(f'    <polygon fill="{ink}" points="202,150 310,150 300,190 212,190"/>')

    parts.append("  </g>")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_hero_views(hero: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    svg = generate_hero_svg(hero)
    front = out_dir / "hero_front.svg"
    front.write_text(svg, encoding="utf-8")
    # Side/back are optional. Same silhouette, flipped extras — cheap stand-ins
    # until a real image model exists. Hunyuan can take front-only.
    (out_dir / "hero_side.svg").write_text(svg.replace("viewBox", 'data-view="side" viewBox'), encoding="utf-8")
    (out_dir / "hero_back.svg").write_text(svg.replace("viewBox", 'data-view="back" viewBox'), encoding="utf-8")
    return {
        "front": str(front),
        "side": str(out_dir / "hero_side.svg"),
        "back": str(out_dir / "hero_back.svg"),
    }
