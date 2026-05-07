"""
config.py — Centralised configuration for ChefSnap backend.
All magic numbers, model names, and domain lists live here.
Values fall back to sensible defaults when env vars are absent.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from project root ──────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=True)

# Disable tracing by default in the backend server
os.environ.setdefault("LANGSMITH_TRACING", "false")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")


# ─────────────────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────────────────
APP_TITLE = "ChefSnap API"
APP_DESCRIPTION = "Snap your fridge. Get Indian recipes."
APP_VERSION = "0.2.0"


# ─────────────────────────────────────────────────────────────────────────────
# VISION MODEL
# ─────────────────────────────────────────────────────────────────────────────
VISION_MODEL = os.getenv("CHEFSNAP_VISION_MODEL", "gemini-1.5-flash")
VISION_TEMPERATURE = float(os.getenv("CHEFSNAP_VISION_TEMPERATURE", "0.0"))


# ─────────────────────────────────────────────────────────────────────────────
# RECIPE AGENT MODEL
# ─────────────────────────────────────────────────────────────────────────────
AGENT_MODEL = os.getenv("CHEFSNAP_AGENT_MODEL", "gemini-1.5-flash")
AGENT_TEMPERATURE = float(os.getenv("CHEFSNAP_AGENT_TEMPERATURE", "0.7"))
AGENT_MAX_SEARCH_RESULTS = int(os.getenv("CHEFSNAP_AGENT_MAX_SEARCH_RESULTS", "3"))
AGENT_TIMEOUT_SECONDS = int(os.getenv("CHEFSNAP_AGENT_TIMEOUT", "30"))


# ─────────────────────────────────────────────────────────────────────────────
# INDIAN-FIRST RECIPE DOMAINS (plan.md §6)
# ─────────────────────────────────────────────────────────────────────────────
INDIAN_RECIPE_DOMAINS = [
    "sanjeevkapoor.com",
    "tarladalal.com",
    "indianhealthyrecipes.com",
    "hebbarskitchen.com",
    "archanaskitchen.com",
    "cookwithmanali.com",
    "vegrecipesofindia.com",   # plan.md §6 allowlist
    "spiceupthecurry.com",     # plan.md §6 allowlist
]

INDIAN_DOMAINS_SEARCH_QUERY = " OR ".join(INDIAN_RECIPE_DOMAINS)


# ─────────────────────────────────────────────────────────────────────────────
# CACHE
# ─────────────────────────────────────────────────────────────────────────────
CACHE_TTL_SECONDS = int(os.getenv("CHEFSNAP_CACHE_TTL", "3600"))
