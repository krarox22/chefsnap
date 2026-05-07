"""
conftest.py — Shared fixtures for ChefSnap tests.
All LLM / Tavily calls are mocked so tests run offline, fast, and free.
"""

import sys
from pathlib import Path
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

# Make the backend module importable from the tests directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardrails import (
    IngredientDTO, DetectionResponseDTO,
    RecipeDTO, SuggestionResponseDTO,
    RecipeRequestDTO, SearchPreferencesDTO,
)


# ─────────────────────────────────────────────────────────────────────────────
# SAMPLE DATA FACTORIES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_ingredient():
    """A single valid IngredientDTO."""
    return IngredientDTO(
        name="tomato",
        display_name="Tomato",
        confidence=0.94,
        quantity_hint="4-5 pieces",
    )


@pytest.fixture
def sample_detection_response(sample_ingredient):
    """A valid DetectionResponseDTO with one ingredient."""
    return DetectionResponseDTO(
        ingredients=[sample_ingredient],
        unrecognized_regions=0,
        request_id="req_test1234",
    )


@pytest.fixture
def sample_recipe():
    """A single valid RecipeDTO."""
    return RecipeDTO(
        id="rec_001",
        name="Paneer Butter Masala",
        cuisine="North Indian",
        is_indian=True,
        match_percent=92,
        missing_ingredients=["butter", "cream"],
        cook_time_minutes=30,
        difficulty="easy",
        source_url="https://www.indianhealthyrecipes.com/paneer-butter-masala/",
        summary="Rich, creamy paneer in a spiced tomato gravy.",
    )


@pytest.fixture
def sample_suggestion_response(sample_recipe):
    """A valid SuggestionResponseDTO with one recipe."""
    return SuggestionResponseDTO(
        recipes=[sample_recipe],
        indian_count=1,
        total_count=1,
        request_id="req_test5678",
    )


@pytest.fixture
def sample_recipe_request():
    """A valid RecipeRequestDTO."""
    return RecipeRequestDTO(
        ingredients=["tomato", "paneer", "onion"],
        preferences=SearchPreferencesDTO(
            cuisine_preference="indian_first",
            diet="vegetarian",
            spice_level="medium",
            max_cook_time_minutes=45,
            servings=2,
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# WEB CLIENT FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def fake_jpeg_bytes():
    """A real 10×10 JPEG image in bytes — parseable by Pillow and passes resolution guardrail."""
    from PIL import Image
    import io
    img = Image.new("RGB", (400, 400), color=(100, 149, 237))  # cornflower blue
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def client(monkeypatch, sample_detection_response, sample_suggestion_response):
    """
    FastAPI TestClient with vision and agent services fully mocked.
    No real LLM calls are made.
    """
    # Patch VisionService.detect_ingredients
    from vision import VisionService
    monkeypatch.setattr(
        VisionService,
        "detect_ingredients",
        lambda self, images, **kwargs: sample_detection_response,
    )

    # Patch RecipeAgentService.suggest_recipes
    from agent import RecipeAgentService
    monkeypatch.setattr(
        RecipeAgentService,
        "suggest_recipes",
        lambda self, req: sample_suggestion_response,
    )

    from main import app
    return TestClient(app)
