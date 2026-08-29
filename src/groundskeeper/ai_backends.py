"""Picks which AIClient backend this project actually uses.

Prefers `GroqClient` (free, no card, see groq_client.py) if `GROQ_API_KEY`
is set; otherwise falls back to `training_data_bot.ai.build_ai_client()`
(Anthropic/OpenAI, per its own Settings). This indirection exists in
`groundskeeper`, not in `training_data_bot`, on purpose — the underlying
library stays exactly as general-purpose as it was before this project
needed a free backend.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from training_data_bot.ai import AIClient, build_ai_client

from .groq_client import GroqClient

# GROQ_API_KEY isn't a training_data_bot Settings field, so pydantic-settings'
# own .env handling never surfaces it — load .env into the process
# environment directly so `os.environ.get("GROQ_API_KEY")` below actually
# sees it.
load_dotenv()


def get_ai_client() -> AIClient:
    if os.environ.get("GROQ_API_KEY"):
        return GroqClient()
    return build_ai_client()
