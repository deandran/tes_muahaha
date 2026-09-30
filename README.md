# Game Lab

A tiny pipeline: guided questions → structured JSON → character picture → 3D stand-in → rig map → template game → playable link.

English UI for now. Bahasa answers (including slang) already parse.

## Run

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python run.py
```

Open http://127.0.0.1:8787

## What is real today

- Guided questions, not a blank prompt
- Spec JSON the rest of the stack reads
- Stylized A-pose hero (transparent background, cached)
- Hunyuan **off** and hard-capped at 20; local low-poly OBJ instead
- No Mixamo. Animation folder is a one-time drop
- Three templates (runner / brawl / collect) customized only through JSON
- Progress captions on every step
- HTML5 player as the delivery target until Unity is installed
- 3 backup characters + 1 finished backup game (`Stage panic` button)

## What waits on hardware / keys / rules

- Cheap LLM: put `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `.env` (optional)
- Hunyuan: set `HUNYUAN_ENABLED=1` plus key/url, and never during a live demo
- Unity batchmode: install the Editor, set `UNITY_EDITOR_PATH`, flip `UNITY_BUILD_LIVE=1` only off-stage
- Delivery target: **web** (HTML5 now, Unity WebGL later). Revisit if the rules reward a native build

Copy `.env.example` to `.env`. Empty keys are fine — the local slang parser is the free path.
