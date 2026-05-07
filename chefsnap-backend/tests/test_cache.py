"""
test_cache.py — Unit tests for the recipe cache
Run: pytest chefsnap-backend/tests/test_cache.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import pytest
from cache import RecipeCache
from guardrails import RecipeRequestDTO, SuggestionResponseDTO, SearchPreferencesDTO


def _make_request(ingredients, diet="any") -> RecipeRequestDTO:
    return RecipeRequestDTO(
        ingredients=ingredients,
        preferences=SearchPreferencesDTO(diet=diet)
    )


def _make_response() -> SuggestionResponseDTO:
    return SuggestionResponseDTO(
        recipes=[], indian_count=0, total_count=0, request_id="req_test"
    )


class TestRecipeCache:
    def test_cache_miss_returns_none(self):
        cache = RecipeCache()
        assert cache.get(_make_request(["tomato"])) is None

    def test_cache_hit_returns_stored(self):
        cache = RecipeCache()
        req = _make_request(["tomato", "paneer"])
        resp = _make_response()
        cache.set(req, resp)
        result = cache.get(req)
        assert result is not None
        assert result.request_id == "req_test"

    def test_key_is_ingredient_order_independent(self):
        cache = RecipeCache()
        req1 = _make_request(["tomato", "paneer"])
        req2 = _make_request(["paneer", "tomato"])
        resp = _make_response()
        cache.set(req1, resp)
        assert cache.get(req2) is not None  # Same key regardless of order

    def test_different_diet_different_key(self):
        cache = RecipeCache()
        req_any = _make_request(["tomato"], diet="any")
        req_jain = _make_request(["tomato"], diet="jain")
        resp = _make_response()
        cache.set(req_any, resp)
        assert cache.get(req_jain) is None

    def test_ttl_expiry(self):
        cache = RecipeCache(ttl_seconds=1)
        req = _make_request(["tomato"])
        cache.set(req, _make_response())
        time.sleep(1.1)
        assert cache.get(req) is None

    def test_clear_empties_cache(self):
        cache = RecipeCache()
        req = _make_request(["tomato"])
        cache.set(req, _make_response())
        cache.clear()
        assert cache.get(req) is None
