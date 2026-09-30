"""Start the Game Lab orchestrator."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
import uvicorn

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8787"))
    uvicorn.run("orchestrator.server:app", host=host, port=port, reload=False)
