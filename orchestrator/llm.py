"""Optional thin LLM adapter. Cheap/free local parser is the default."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .slang import answers_to_spec


SYSTEM = """You turn messy game-idea answers (English or Indonesian slang) into JSON.
Return ONLY JSON with this shape:
{
  "genre": "runner" | "arena" | "collect",
  "hero": {"name": str, "description": str, "primary_color": "#rrggbb", "silhouette": str, "extras": [str]},
  "enemy": {"name": str, "description": str, "primary_color": "#rrggbb"},
  "goal": {"text": str, "win_condition": "distance"|"kills"|"items", "target": number},
  "mood": "cozy"|"chaotic"|"cute"|"night",
  "ui_text": {"title": str, "subtitle": str, "win": str, "lose": str, "hint": str}
}
Keep it simple. No extra keys. Colors must be hex.
"""


def llm_available() -> str | None:
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return None


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    spec = answers_to_spec(base.get("raw_answers") or {})
    # overlay only safe fields
    if overlay.get("genre") in {"runner", "arena", "collect"}:
        spec["genre"] = overlay["genre"]
        spec["template_id"] = overlay["genre"]
    for key in ("hero", "enemy", "goal", "ui_text"):
        if isinstance(overlay.get(key), dict):
            spec[key] = {**spec[key], **overlay[key]}
    if overlay.get("mood"):
        spec["mood"] = overlay["mood"]
    spec["parser"] = overlay.get("_parser", "llm+local")
    return spec


def enrich_spec_with_llm(answers: dict[str, Any], local_spec: dict[str, Any]) -> dict[str, Any]:
    provider = llm_available()
    if not provider:
        return local_spec
    prompt = json.dumps(answers, ensure_ascii=False)
    try:
        if provider == "openai":
            overlay = _openai(prompt)
        else:
            overlay = _anthropic(prompt)
        overlay["_parser"] = provider
        return _merge({"raw_answers": answers}, overlay)
    except Exception:
        local_spec["parser"] = f"local-slang (llm {provider} failed)"
        return local_spec


def _openai(user_text: str) -> dict[str, Any]:
    body = json.dumps(
        {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_text},
            ],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
    return json.loads(data["choices"][0]["message"]["content"])


def _anthropic(user_text: str) -> dict[str, Any]:
    body = json.dumps(
        {
            "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
            "max_tokens": 800,
            "system": SYSTEM,
            "messages": [{"role": "user", "content": user_text}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": os.getenv("ANTHROPIC_API_KEY", ""),
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
    text = data["content"][0]["text"]
    return json.loads(text)
