# ChefSnap — Work Tracker

_Last updated: 2026-04-19 (Weeks 1–6 complete — v1 shipped)_

---

## Week 1 — Backend Scaffolding

- [x] FastAPI project structure (`main.py`, `config.py`, `__init__.py`)
- [x] `/api/v1/ingredients/detect` endpoint wired to vision model (`vision.py`)
- [x] Guardrails module (`guardrails.py`) — input, ingredient, output, abuse categories
- [x] Unit tests for guardrails (`tests/test_guardrails.py`)
- [x] Unit tests for vision (`tests/test_vision.py`)
- [x] Unit tests for API (`tests/test_api.py`)

## Week 2 — Agent + Recipe Logic

- [x] LangChain agent wired to `/api/v1/recipes/suggest` (`agent.py`)
- [x] Indian-first logic (system prompt + post-processing re-sort + re-invoke if < 70%)
- [x] JSON schema validation on recipe response
- [x] Recipe cache (`cache.py`) — keyed on sorted ingredient hash
- [x] Unit tests for agent (`tests/test_agent.py`)
- [x] Unit tests for cache (`tests/test_cache.py`)

## Week 3 — React Native App (`chefsnap-app/`)

- [x] Expo project scaffold — `package.json`, `app.json`, `tsconfig.json`, `babel.config.js`
- [x] Camera / multi-photo capture screen (up to 5 photos) — `app/index.tsx`
- [x] Ingredient edit screen (add / remove / correct) — `app/ingredients.tsx`
- [x] Recipe list screen with Indian-first ordering — `app/recipes.tsx`
- [x] Recipe detail screen (time, difficulty, match %, source link) — `app/recipe/[id].tsx`
- [x] Zustand store + React Query wiring to backend API — `src/store/useAppStore.ts`, `src/api/`
- [x] Dietary filter UI (vegetarian, vegan, Jain, halal, gluten-free) — `src/components/DietFilterBar.tsx`
- [x] Offline fallback — last 10 recipes cached locally via AsyncStorage — `src/hooks/useOfflineCache.ts`

## Week 4 — Auth, Rate Limiting, Observability

- [x] Clerk social login (Google + Apple OAuth) — `app/(auth)/sign-in.tsx`, `ClerkProvider` in `_layout.tsx`
- [x] Per-user rate limiting — Redis INCR/EXPIRE with in-memory fallback (`guardrails.py` `AbuseGuardrails`)
- [x] Per-IP rate limiting — falls back to `request.client.host` when no auth token present
- [x] Sentry crash reporting — backend: `sentry-sdk[fastapi]` in `main.py`; client: `@sentry/react-native` in `_layout.tsx`
- [x] OpenTelemetry LLM tracing — `tracing.py` (`configure_tracing` + `llm_span` helper), wired into `main.py`
- [x] Age-gate — `userAge` in Zustand store, passed as `?user_age=` query param to `/suggest`
- [x] Allergy warning banner — `AllergyBanner.tsx`, shown on ingredients screen from detect response

## Week 5 — Closed Beta

- [x] EAS build profiles (development / preview / production) — `chefsnap-app/eas.json`
- [x] TestFlight + Play Internal CI — `.github/workflows/eas-preview.yml` (auto on push to main)
- [x] Beta feedback screen — `app/feedback.tsx` (star rating + comment → POST /api/v1/feedback)
- [x] `/health` liveness endpoint — `main.py` (used by ECS / load-balancer health checks)
- [x] `/api/v1/feedback` backend endpoint — structured log + Sentry capture
- [ ] Onboard 50 beta users — requires TestFlight / Play Internal invite links (infra ready)

## Week 6 — Public Launch v1

- [x] Production CI — `.github/workflows/eas-production.yml` (manual `workflow_dispatch`)
- [x] App Store / Play Store submission — `eas submit` wired in production workflow
- [x] Server-side KPI metrics — `chefsnap-backend/metrics.py` + `GET /api/v1/metrics`
  - p50/p95/p99 latency per endpoint, error rates, uptime
  - targets: detect p95 ≤ 3 s, suggest p95 ≤ 8 s, error_rate ≤ 1 %
- [x] Client-side KPI analytics — `src/hooks/useAnalytics.ts` (Sentry breadcrumbs)
  - `session_start` → activation; `recipes_viewed` → relevance; `recipe_detail_opened` → 60 % target
- [x] Settings screen — `app/settings.tsx` (Indian-first toggle, age input, feedback nav, sign-out)
- [x] `SessionTracker` component in `_layout.tsx` fires `session_start` on sign-in

---

## Required env vars (not committed)

| Variable | Where | Purpose |
|---|---|---|
| `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` | client | Clerk OAuth |
| `CLERK_JWKS_URL` | backend | JWT verification |
| `EXPO_PUBLIC_SENTRY_DSN` | client | Sentry crashes |
| `SENTRY_DSN` | backend | Sentry errors |
| `REDIS_URL` | backend | Rate limiting |
| `OTEL_ENABLED=true` | backend | OTel tracing |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | backend | Collector URL |
| `EXPO_TOKEN` | CI secret | EAS builds |
| `APPLE_ID`, `ASC_APP_ID`, `APPLE_TEAM_ID` | CI secret | TestFlight / App Store |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | CI secret | Play Internal / Store |

---

## Blocked / Notes

- Object storage (S3/R2/GCS) presigned upload flow not yet implemented — needed before Week 3 camera flow can hit a real backend.
- Redis connection config needs to be verified for dev environment before cache tests run against a live instance.
