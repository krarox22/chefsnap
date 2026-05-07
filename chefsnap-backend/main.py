"""
main.py — ChefSnap FastAPI gateway (Phase 1–6)
Endpoints:
  GET  /health                      — liveness probe
  POST /api/v1/ingredients/detect   — multi-image upload → Gemini Vision
  POST /api/v1/recipes/suggest      — ingredient list → Indian-first recipe agent
  POST /api/v1/feedback             — beta / post-launch user feedback
  GET  /api/v1/metrics              — server-side KPI snapshot (plan.md §10)
"""

import base64
import io
import os
import logging
import time
from typing import List, Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from config import APP_TITLE, APP_DESCRIPTION, APP_VERSION

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from PIL import Image
from starlette.middleware.base import BaseHTTPMiddleware

from auth import get_optional_user_id
from guardrails import (
    InputGuardrails, IngredientGuardrails, AbuseGuardrails, RateLimitError,
    OutputGuardrails, RecipeRequestDTO,
)
from vision import vision_service
from agent import recipe_agent_service
from cache import recipe_cache
from tracing import configure_tracing
from metrics import metrics

logger = logging.getLogger(__name__)

# ── Sentry ────────────────────────────────────────────────────────────────────
_sentry_dsn = os.getenv("SENTRY_DSN", "")
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[StarletteIntegration(), FastApiIntegration()],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.2")),
        send_default_pii=False,
    )
    logger.info("Sentry initialised")

app = FastAPI(title=APP_TITLE, description=APP_DESCRIPTION, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── OpenTelemetry ─────────────────────────────────────────────────────────────
configure_tracing(app)


# ── Latency middleware (feeds metrics collector) ──────────────────────────────
class _MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        error = False
        try:
            response = await call_next(request)
            if response.status_code >= 500:
                error = True
            return response
        except Exception:
            error = True
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            key = f"{request.method} {request.url.path}"
            metrics.record(key, elapsed_ms, error)


app.add_middleware(_MetricsMiddleware)


# ── Rate-limit helper ─────────────────────────────────────────────────────────
def _rate_limit(user_id: Optional[str], request: Request, limit: int) -> None:
    identity = user_id or (request.client.host if request.client else "unknown")
    try:
        AbuseGuardrails.check_rate_limit(identity, limit=limit)
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def test_ui():
    return FileResponse("test_ui.html")


@app.get("/health")
async def health():
    """Liveness probe for load-balancer / ECS health checks."""
    return {"status": "ok", "version": APP_VERSION}


@app.post("/api/v1/ingredients/detect")
async def detect_ingredients(
    request: Request,
    files: List[UploadFile] = File(...),
    locale: str = Query(default="en-IN"),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """
    Accepts 1–5 images. Returns detected ingredients with confidence scores.
    Plan.md §5 data contract. `locale` biases ingredient display names.
    """
    _rate_limit(user_id, request, limit=AbuseGuardrails.DETECT_LIMIT)

    try:
        InputGuardrails.validate_image_count(len(files))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    base64_images: List[str] = []
    for upload in files:
        content = await upload.read()
        try:
            InputGuardrails.validate_image_upload(
                mime_type=upload.content_type or "unknown",
                file_size=len(content),
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        try:
            img = Image.open(io.BytesIO(content))
            InputGuardrails.validate_image_resolution(img.width, img.height)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            pass

        base64_images.append(base64.b64encode(content).decode("utf-8"))

    try:
        result = vision_service.detect_ingredients(base64_images, locale=locale)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision API error: {e}")

    result.ingredients, allergen_warnings = IngredientGuardrails.process_ingredients(
        result.ingredients, diet="any"
    )
    response = result.model_dump()
    if allergen_warnings:
        response["allergen_warnings"] = allergen_warnings
    return response


@app.post("/api/v1/recipes/suggest")
async def suggest_recipes(
    request: Request,
    body: RecipeRequestDTO,
    user_age: Optional[int] = Query(default=None),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """
    Returns 5–8 Indian-first recipe suggestions for the given ingredient list.
    Plan.md §5 data contract.
    """
    _rate_limit(user_id, request, limit=AbuseGuardrails.SUGGEST_LIMIT)

    cached = recipe_cache.get(body)
    if cached:
        return cached

    try:
        result = recipe_agent_service.suggest_recipes(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    result.recipes, alcohol_warnings = OutputGuardrails.flag_alcohol_recipes(
        result.recipes, user_age=user_age
    )
    result.indian_count = sum(1 for r in result.recipes if r.is_indian)
    result.total_count = len(result.recipes)
    recipe_cache.set(body, result)

    response = result.model_dump()
    if alcohol_warnings:
        response["alcohol_warnings"] = alcohol_warnings
    return response


class FeedbackDTO(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="1–5 star rating")
    comment: str = Field(default="", max_length=2000)


@app.post("/api/v1/feedback")
async def submit_feedback(
    body: FeedbackDTO,
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Accepts beta / post-launch feedback. Logged + forwarded to Sentry."""
    logger.info(
        "user_feedback",
        extra={"rating": body.rating, "comment": body.comment[:200], "user_id": user_id or "guest"},
    )
    if _sentry_dsn:
        sentry_sdk.capture_message(
            f"Feedback {body.rating}/5: {body.comment[:200]}",
            level="info",
        )
    return {"status": "received"}


@app.get("/api/v1/metrics")
async def get_metrics():
    """Server-side KPI snapshot (plan.md §10). Restricted to internal use."""
    return JSONResponse(metrics.summary())
