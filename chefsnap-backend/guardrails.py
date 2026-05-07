"""
guardrails.py — ChefSnap safety layer
Four guard categories (plan.md §7):
  1. Input        — MIME, size, file count, resolution
  2. Ingredient   — normalization, alias, allergen, diet-filtering, prompt-injection
  3. Output       — field-range checks, domain allowlist, unsafe-phrase rejection,
                    alcohol age-gate (plan.md §8)
  4. Abuse        — rate limiting (pass-through stub → Redis in production)
"""

import re
from typing import List, Optional
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# DATA CONTRACTS
# ─────────────────────────────────────────────────────────────────────────────

class IngredientDTO(BaseModel):
    name: str = Field(description="Normalized internal name (e.g. 'tomato', 'coriander')")
    display_name: str = Field(description="Display name for UI (e.g. 'Tomato', 'Coriander (Dhaniya)')")
    confidence: float = Field(description="Vision confidence score between 0.0 and 1.0")
    quantity_hint: str = Field(description="Rough visual estimate, e.g. '4-5 pieces'")

class DetectionRequestDTO(BaseModel):
    """Request body for POST /api/v1/ingredients/detect (plan.md §5)."""
    image_keys: List[str] = Field(
        description="Object-storage keys for pre-uploaded images, e.g. 'uploads/abc.jpg'."
    )
    locale: str = Field(
        default="en-IN",
        description="BCP-47 locale tag — used to bias ingredient display names."
    )

class DetectionResponseDTO(BaseModel):
    ingredients: List[IngredientDTO]
    unrecognized_regions: int = Field(default=0)
    request_id: str

class SearchPreferencesDTO(BaseModel):
    cuisine_preference: str = Field(default="indian_first")
    diet: str = Field(default="any", description="'any', 'vegetarian', 'vegan', 'jain', 'halal', 'gluten-free'")
    spice_level: str = Field(default="medium")
    max_cook_time_minutes: int = Field(default=60)
    servings: int = Field(default=2)

class RecipeRequestDTO(BaseModel):
    ingredients: List[str]
    preferences: SearchPreferencesDTO = SearchPreferencesDTO()

DIFFICULTY_ENUM = {"easy", "medium", "hard"}

class RecipeDTO(BaseModel):
    id: str
    name: str
    cuisine: str
    is_indian: bool
    match_percent: int
    missing_ingredients: List[str]
    cook_time_minutes: int
    difficulty: str
    source_url: str
    summary: str

class SuggestionResponseDTO(BaseModel):
    recipes: List[RecipeDTO]
    indian_count: int
    total_count: int
    request_id: str


# ─────────────────────────────────────────────────────────────────────────────
# 1. INPUT GUARDRAILS
# ─────────────────────────────────────────────────────────────────────────────

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_IMAGES_PER_SESSION = 5


# Minimum acceptable image dimensions (§7 — resolution guardrail)
MIN_IMAGE_WIDTH_PX = 200
MIN_IMAGE_HEIGHT_PX = 200


class InputGuardrails:
    @staticmethod
    def validate_image_upload(mime_type: str, file_size: int) -> None:
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError(f"MIME type '{mime_type}' not permitted. Allowed: {ALLOWED_MIME_TYPES}")
        if file_size > MAX_IMAGE_SIZE_BYTES:
            raise ValueError(f"File size {file_size / 1_048_576:.1f} MB exceeds 10 MB limit.")

    @staticmethod
    def validate_image_count(count: int) -> None:
        if count < 1:
            raise ValueError("At least one image must be provided.")
        if count > MAX_IMAGES_PER_SESSION:
            raise ValueError(f"Maximum {MAX_IMAGES_PER_SESSION} images per session; received {count}.")

    @staticmethod
    def validate_image_resolution(width_px: int, height_px: int) -> None:
        """
        Reject images that are too small to yield useful ingredient detections.
        Full resolution check (using Pillow) is done in main.py after decoding.
        Stub: in production, also cap max resolution to prevent extremely large
        tensors being sent to the vision model.
        """
        if width_px < MIN_IMAGE_WIDTH_PX or height_px < MIN_IMAGE_HEIGHT_PX:
            raise ValueError(
                f"Image resolution {width_px}×{height_px}px is below the minimum "
                f"{MIN_IMAGE_WIDTH_PX}×{MIN_IMAGE_HEIGHT_PX}px required for detection."
            )


# ─────────────────────────────────────────────────────────────────────────────
# 2. INGREDIENT GUARDRAILS
# ─────────────────────────────────────────────────────────────────────────────

# Alias normalization dictionary (expandable toward thousands of entries)
CANONICAL_MAP: dict[str, str] = {
    # Hindi transliterations
    "dhaniya": "coriander", "cilantro": "coriander",
    "pyaz": "onion", "kanda": "onion",
    "adrak": "ginger", "adrakh": "ginger",
    "lasun": "garlic", "lehsun": "garlic",
    "mirchi": "chili", "hari mirch": "green chili", "lal mirch": "red chili",
    "haldi": "turmeric", "jeera": "cumin",
    "dhania": "coriander", "methi": "fenugreek",
    "palak": "spinach", "saag": "mustard greens",
    "alu": "potato", "aloo": "potato",
    "gobi": "cauliflower", "phool gobi": "cauliflower",
    "baingan": "eggplant", "brinjal": "eggplant",
    "matar": "peas", "shimla mirch": "bell pepper",
    "lauki": "bottle gourd", "tori": "ridge gourd",
    "kaddu": "pumpkin", "karela": "bitter melon",
    "bhindi": "okra", "tinda": "apple gourd",
    # Typos
    "tomaato": "tomato", "tomatoe": "tomato", "patato": "potato",
    "capsicum": "bell pepper",
}

# Items the vision model may detect that are clearly non-food
BLOCKED_ITEMS = frozenset([
    "cleaning spray", "bleach", "detergent", "container", "tupperware",
    "shelf", "glass", "bottle cap", "label", "packaging", "plastic bag",
    "cardboard", "paper bag", "rubber band",
])

# Common allergens — surfaced as warnings, not blocked
KNOWN_ALLERGENS = frozenset([
    "peanut", "peanuts", "tree nut", "milk", "egg", "wheat", "gluten",
    "soy", "fish", "shellfish", "sesame",
])

# Jain diet exclusions (no root vegetables, onion, garlic)
JAIN_EXCLUSIONS = frozenset([
    "onion", "garlic", "potato", "ginger", "carrot", "radish",
    "beet", "beetroot", "leek", "spring onion", "scallion", "shallot",
])

# Prompt injection patterns — applied to any free-text ingredient string
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"disregard\s+(all\s+)?instructions?",
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(if\s+you\s+are\s+)?",
    r"forget\s+(everything|all|the\s+above)",
    r"system\s*:\s*",
    r"<\|im_start\|>",
    r"<\|endoftext\|>",
]
_INJECTION_RE = re.compile(
    "|".join(INJECTION_PATTERNS), re.IGNORECASE
)


class IngredientGuardrails:
    @classmethod
    def check_prompt_injection(cls, ingredient: str) -> None:
        """Raise if the ingredient string contains a prompt-injection attempt."""
        if _INJECTION_RE.search(ingredient):
            raise ValueError(f"Rejected ingredient '{ingredient}': prompt injection detected.")

    @classmethod
    def process_ingredients(
        cls,
        detected: List[IngredientDTO],
        diet: str = "any",
    ) -> tuple[List[IngredientDTO], List[str]]:
        """
        Returns (clean_ingredients, allergen_warnings).
        Applies: non-food removal → normalization → diet filtering.
        """
        clean: List[IngredientDTO] = []
        allergen_warnings: List[str] = []

        for item in detected:
            lower = item.name.lower().strip()

            # Non-food block
            if any(blocked in lower for blocked in BLOCKED_ITEMS):
                continue

            # Normalize via alias map
            item.name = CANONICAL_MAP.get(lower, lower)
            lower_normalized = item.name.lower()

            # Allergen surfacing
            if lower_normalized in KNOWN_ALLERGENS:
                allergen_warnings.append(item.display_name)

            # Diet filtering — strip incompatible ingredients before LLM
            if diet == "jain" and lower_normalized in JAIN_EXCLUSIONS:
                continue
            if diet == "vegan" and lower_normalized in {"milk", "egg", "paneer", "ghee", "butter", "cream", "yogurt", "curd"}:
                continue

            clean.append(item)

        return clean, allergen_warnings

    @classmethod
    def sanitize_free_text_list(cls, ingredients: List[str]) -> List[str]:
        """Sanitize a user-supplied free-text ingredient list for injection risk."""
        sanitized = []
        for ing in ingredients:
            cls.check_prompt_injection(ing)
            sanitized.append(ing.strip())
        return sanitized


# ─────────────────────────────────────────────────────────────────────────────
# 3. OUTPUT GUARDRAILS
# ─────────────────────────────────────────────────────────────────────────────

ALLOWED_SOURCE_DOMAINS = frozenset([
    # Indian-first domains (plan.md §6 + §7 allowlist)
    "sanjeevkapoor.com", "tarladalal.com", "indianhealthyrecipes.com",
    "hebbarskitchen.com", "archanaskitchen.com", "vegrecipesofindia.com",
    "cookwithmanali.com", "spiceupthecurry.com", "ndtv.com",
    "food.ndtv.com", "pinkvilla.com", "nishkitchen.com",
    "indiaphile.info", "whiskaffair.com", "ticklingpalates.com",
    # International fallback domains (non-Indian slots, plan.md §6.1)
    "allrecipes.com", "bbc.co.uk", "bbcgoodfood.com",
])

UNSAFE_OUTPUT_PHRASES = [
    "raw chicken", "raw egg", "raw meat", "raw seafood",
    "cures cancer", "cures diabetes", "guaranteed weight loss",
    "medical treatment", "prevents covid",
]
_UNSAFE_RE = re.compile(
    "|".join(re.escape(p) for p in UNSAFE_OUTPUT_PHRASES), re.IGNORECASE
)

# Alcohol keywords used for the age-gate (plan.md §8)
_ALCOHOL_RE = re.compile(
    r"\b(beer|wine|whiskey|whisky|vodka|rum|gin|brandy|liqueur|cocktail|"
    r"champagne|sake|mead|cider|ale|lager|stout|tequila|bourbon|scotch|"
    r"alcohol|spirits|booze)\b",
    re.IGNORECASE,
)


class OutputGuardrails:
    @classmethod
    def validate_schema(cls, response: SuggestionResponseDTO) -> list[str]:
        """
        Returns a list of error strings. Empty list means response is valid.
        Checks: field ranges, difficulty enum, source URL domain allowlist,
        unsafe phrases, and alcohol flagging (plan.md §8).
        """
        errors: list[str] = []

        for recipe in response.recipes:
            # match_percent must be 0–100
            if not (0 <= recipe.match_percent <= 100):
                errors.append(
                    f"Recipe '{recipe.name}': match_percent {recipe.match_percent} out of range 0–100."
                )
                recipe.match_percent = max(0, min(100, recipe.match_percent))

            # difficulty must be in enum
            if recipe.difficulty.lower() not in DIFFICULTY_ENUM:
                errors.append(
                    f"Recipe '{recipe.name}': difficulty '{recipe.difficulty}' not in {DIFFICULTY_ENUM}."
                )
                recipe.difficulty = "medium"  # safe default

            # cook_time_minutes must be positive
            if recipe.cook_time_minutes <= 0:
                errors.append(
                    f"Recipe '{recipe.name}': cook_time_minutes must be > 0."
                )
                recipe.cook_time_minutes = 30

            # source URL domain allowlist
            from urllib.parse import urlparse
            try:
                domain = urlparse(recipe.source_url).netloc.lstrip("www.")
                if not any(domain.endswith(allowed) for allowed in ALLOWED_SOURCE_DOMAINS):
                    errors.append(
                        f"Recipe '{recipe.name}': source_url domain '{domain}' not in allowlist."
                    )
                    recipe.source_url = ""
            except Exception:
                errors.append(f"Recipe '{recipe.name}': invalid source_url.")
                recipe.source_url = ""

            # Unsafe phrase check on summary
            if _UNSAFE_RE.search(recipe.summary):
                errors.append(
                    f"Recipe '{recipe.name}': summary contains unsafe phrase."
                )
                recipe.summary = "[Content removed by safety filter]"

        return errors

    @classmethod
    def flag_alcohol_recipes(
        cls,
        recipes: List["RecipeDTO"],
        user_age: Optional[int] = None,
    ) -> tuple[List["RecipeDTO"], List[str]]:
        """
        Applies the plan.md §8 alcohol age-gate.
        - If user_age is known and < 21, alcohol-containing recipes are removed.
        - Otherwise, alcohol-containing recipes carry a warning flag.
        Returns (filtered_recipes, alcohol_warnings).
        """
        filtered: List["RecipeDTO"] = []
        warnings: List[str] = []

        for recipe in recipes:
            text = f"{recipe.name} {recipe.summary}"
            if _ALCOHOL_RE.search(text):
                if user_age is not None and user_age < 21:
                    # Hard block for verified minors
                    warnings.append(
                        f"Recipe '{recipe.name}' removed: contains alcohol (age restriction)."
                    )
                    continue
                # Surface a warning for unverified / adult users
                warnings.append(
                    f"Recipe '{recipe.name}' contains alcohol — please consume responsibly."
                )
            filtered.append(recipe)

        return filtered, warnings


# ─────────────────────────────────────────────────────────────────────────────
# 4. ABUSE GUARDRAILS
# ─────────────────────────────────────────────────────────────────────────────

import os
import time as _time

try:
    import redis as _redis_lib
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

_redis_client = None
_redis_init_attempted = False
_in_memory_buckets: dict[str, list[float]] = {}


def _get_redis():
    global _redis_client, _redis_init_attempted
    if _redis_init_attempted:
        return _redis_client
    _redis_init_attempted = True
    if not _REDIS_AVAILABLE:
        return None
    try:
        client = _redis_lib.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            decode_responses=True,
            socket_connect_timeout=2,
        )
        client.ping()
        _redis_client = client
    except Exception:
        _redis_client = None
    return _redis_client


class RateLimitError(Exception):
    """Raised when a client exceeds their request quota."""


class AbuseGuardrails:
    DETECT_LIMIT = 10   # detections per hour on free tier (plan.md §7)
    SUGGEST_LIMIT = 20  # recipe suggestions per hour
    WINDOW_SECONDS = 3600

    @classmethod
    def check_rate_limit(
        cls,
        user_id: str,
        limit: int = DETECT_LIMIT,
        window_seconds: int = WINDOW_SECONDS,
    ) -> None:
        """Raises RateLimitError if user_id exceeds limit within the window."""
        key = f"rate:{user_id}"
        r = _get_redis()

        if r is not None:
            try:
                count = r.incr(key)
                if count == 1:
                    r.expire(key, window_seconds)
                if count > limit:
                    raise RateLimitError(
                        f"Rate limit exceeded: {limit} requests/hour. Try again later."
                    )
                return
            except RateLimitError:
                raise
            except Exception:
                pass  # Redis error → fall through to in-memory

        # In-memory fallback (single-process, suitable for dev)
        now = _time.time()
        bucket = _in_memory_buckets.setdefault(key, [])
        bucket[:] = [t for t in bucket if now - t < window_seconds]
        if len(bucket) >= limit:
            raise RateLimitError(
                f"Rate limit exceeded: {limit} requests/hour. Try again later."
            )
        bucket.append(now)
