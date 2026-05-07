import hashlib
import json
import time
from typing import Optional
from guardrails import RecipeRequestDTO, SuggestionResponseDTO


class RecipeCache:
    """
    In-memory SHA256-keyed recipe cache with TTL.
    Keys are derived from sorted ingredients + preferences hash.
    Swap the internal dict for Redis in production.
    """

    def __init__(self, ttl_seconds: int = 3600):
        self._store: dict[str, tuple[SuggestionResponseDTO, float]] = {}
        self._ttl = ttl_seconds

    def _make_key(self, request: RecipeRequestDTO) -> str:
        """Deterministic cache key from sorted ingredients + all preferences."""
        payload = {
            "ingredients": sorted([i.lower() for i in request.ingredients]),
            "diet": request.preferences.diet,
            "spice_level": request.preferences.spice_level,
            "cuisine_preference": request.preferences.cuisine_preference,
            "max_cook_time_minutes": request.preferences.max_cook_time_minutes,
            "servings": request.preferences.servings,
        }
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, request: RecipeRequestDTO) -> Optional[SuggestionResponseDTO]:
        key = self._make_key(request)
        entry = self._store.get(key)
        if entry is None:
            return None
        result, timestamp = entry
        if time.time() - timestamp > self._ttl:
            del self._store[key]
            return None
        return result

    def set(self, request: RecipeRequestDTO, response: SuggestionResponseDTO) -> None:
        key = self._make_key(request)
        self._store[key] = (response, time.time())

    def clear(self) -> None:
        self._store.clear()


# Singleton — redis backend wired here in production
recipe_cache = RecipeCache(ttl_seconds=3600)
