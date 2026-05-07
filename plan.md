# ChefSnap — Plan

> A mobile app where you snap photos of leftover ingredients and get Indian-first recipe suggestions, powered by a vision model + a LangChain recipe-search agent.

---

## 1. Product Summary

**One-liner:** "Point your camera at your fridge. Get dinner."

**Core user journey (< 30 seconds):**

1. User opens the app and taps **Scan Ingredients**.
2. Snaps 1–5 photos (fridge shelves, pantry, counter).
3. App shows a detected ingredients list — user can edit (add/remove/correct).
4. User taps **Find Recipes**.
5. App returns 5–8 recipe suggestions, **Indian dishes first**, each with cuisine, estimated time, difficulty, and match percentage.
6. User taps a recipe → full step-by-step instructions streamed in.

**Non-goals (v1):**

- Grocery ordering / shopping list fulfillment.
- Calorie & macro tracking.
- Social features (sharing, comments, follows).
- Meal planning across days.

---

## 2. Architecture Overview

```
┌───────────────────┐        ┌──────────────────────┐        ┌────────────────────────┐
│   Mobile Client   │        │   API Gateway        │        │   Agent Service        │
│  (React Native    │──HTTPS▶│  (FastAPI + Auth)    │──────▶ │  (LangChain Agent)     │
│   / Expo)         │        │                      │        │  - Vision: GPT-4o /    │
│                   │        │  - Upload presign    │        │    Gemini Vision       │
│  - Camera         │        │  - Rate limiting     │        │  - Recipe LLM: GPT-5   │
│  - Edit list UI   │        │  - Guardrails layer  │        │  - Tool: Tavily search │
│  - Recipe view    │        │                      │        │                        │
└───────────────────┘        └──────────┬───────────┘        └───────────┬────────────┘
                                        │                                │
                                        ▼                                ▼
                             ┌──────────────────┐              ┌────────────────────┐
                             │  Object Storage  │              │  Cache (Redis)     │
                             │  (S3 / GCS)      │              │  - Recipe cache    │
                             │  - Raw photos    │              │  - Ingredient norm │
                             │  - 24h TTL       │              │                    │
                             └──────────────────┘              └────────────────────┘
```

**Request flow for "Scan → Recipes":**

1. Client requests a presigned upload URL from API.
2. Client uploads each photo directly to object storage.
3. Client calls `POST /api/v1/ingredients/detect` with the image keys.
4. API runs **guardrails** (image safety, size, format, count).
5. Vision model extracts ingredient names with confidence scores. Results normalized against a canonical ingredient dictionary (e.g., `tomaato` → `tomato`, `dhaniya` → `coriander`).
6. API returns list to client for user confirmation.
7. Client calls `POST /api/v1/recipes/suggest` with the confirmed list + preferences.
8. Agent service runs: prompt includes **"Prioritize Indian cuisine (North Indian, South Indian, Bengali, Gujarati, Maharashtrian, etc.). Return at least 70% Indian dishes unless user disabled Indian-first."**
9. Agent uses Tavily `web_search` tool scoped to recipe domains (Sanjeev Kapoor, Tarla Dalal, Hebbar's Kitchen, Indian Healthy Recipes, Archana's Kitchen, etc.).
10. Response is validated against a strict JSON schema before returning.

---

## 3. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Mobile client | **React Native + Expo** (EAS Build) | Single codebase for iOS + Android, camera & image picker built-in, easy OTA updates |
| State | Zustand + React Query | Light, good for async server state |
| Backend API | **FastAPI (Python 3.11)** | Same language as notebook; good async; easy LangChain integration |
| Agent | LangChain `create_agent` (from existing notebook) | Reuses what you already built |
| Vision | GPT-4o-mini or Gemini 1.5 Flash (configurable) | Cheap + fast ingredient detection |
| Recipe LLM | GPT-5-nano (as per notebook) or swappable | Existing agent choice |
| Search tool | Tavily | Already in notebook |
| Storage | S3 (or any S3-compatible: Cloudflare R2, GCS) | Cheap, presigned uploads |
| Cache | Redis | Recipe cache keyed on sorted ingredient hash |
| Auth | Firebase Auth or Clerk | Social login out of the box |
| Observability | Sentry + OpenTelemetry | Crash reports + LLM tracing |
| CI/CD | GitHub Actions + EAS Build | Standard |

---

## 4. Key Features (v1)

### Must-have
- **Photo capture**: multi-shot (up to 5 photos per session).
- **Ingredient detection** with editable list (add/remove/correct).
- **Indian-first recipe suggestions** (at least 70% Indian by default).
- **Recipe detail view**: ingredients, time, difficulty, steps.
- **Dietary filters**: vegetarian, vegan, Jain (no onion/garlic/root veg), halal, gluten-free.
- **Offline fallback**: last 10 recipes cached locally.

### Nice-to-have (v1.1+)
- **Spice level slider** (mild → extra hot).
- **Regional preference**: Punjabi, South Indian, Bengali, etc.
- **Save favorites**.
- **Voice input** for ingredients ("I also have methi and paneer").
- **Serving scaler** (recipe for 2 → 6).

---

## 5. Data Contracts

### `POST /api/v1/ingredients/detect`
**Request:**
```json
{
  "image_keys": ["uploads/abc123.jpg", "uploads/def456.jpg"],
  "locale": "en-IN"
}
```

**Response:**
```json
{
  "ingredients": [
    {"name": "tomato", "display_name": "Tomato", "confidence": 0.94, "quantity_hint": "4-5 pieces"},
    {"name": "paneer",  "display_name": "Paneer",  "confidence": 0.87, "quantity_hint": "~200g block"},
    {"name": "coriander", "display_name": "Coriander (Dhaniya)", "confidence": 0.78, "quantity_hint": "small bunch"}
  ],
  "unrecognized_regions": 1,
  "request_id": "req_01HXYZ..."
}
```

### `POST /api/v1/recipes/suggest`
**Request:**
```json
{
  "ingredients": ["tomato", "paneer", "coriander", "onion", "ginger", "garlic"],
  "preferences": {
    "cuisine_preference": "indian_first",
    "diet": "vegetarian",
    "spice_level": "medium",
    "max_cook_time_minutes": 45,
    "servings": 2
  }
}
```

**Response:**
```json
{
  "recipes": [
    {
      "id": "rec_001",
      "name": "Paneer Butter Masala",
      "cuisine": "North Indian",
      "is_indian": true,
      "match_percent": 92,
      "missing_ingredients": ["butter", "cream"],
      "cook_time_minutes": 30,
      "difficulty": "easy",
      "source_url": "https://www.indianhealthyrecipes.com/...",
      "summary": "Rich, creamy paneer in a spiced tomato gravy."
    }
  ],
  "indian_count": 6,
  "total_count": 8,
  "request_id": "req_01HXYZ..."
}
```

---

## 6. "Indian-first" Logic

A simple, deterministic policy on top of the LLM:

1. System prompt explicitly instructs: *"First, generate Indian recipes (North Indian, South Indian, Bengali, Gujarati, Maharashtrian, Indo-Chinese). If fewer than 5 Indian options are reasonable, fill remaining slots with international recipes."*
2. Post-processing re-sorts the final list so `is_indian == true` recipes come first.
3. If `preferences.cuisine_preference == "indian_first"` (default) and Indian count < 70% of results, the agent is re-invoked once with a stronger instruction to add more Indian dishes.
4. User can toggle this off with `cuisine_preference: "any"`.

A curated Indian-recipe domain allowlist is passed to Tavily search: `sanjeevkapoor.com`, `tarladalal.com`, `indianhealthyrecipes.com`, `hebbarskitchen.com`, `archanaskitchen.com`, `vegrecipesofindia.com`, `cookwithmanali.com`, `spiceupthecurry.com`.

---

## 7. Guardrails (summary — details in `guardrails.py`)

Four categories, each implemented and unit-tested:

1. **Input guardrails** — image count, MIME type, size, resolution, NSFW check.
2. **Ingredient guardrails** — allowlist / alias normalization, block non-food items, block unsafe items (raw chicken + cross-contamination warnings, alcohol for minors if age is known, known allergens surfaced).
3. **Output guardrails** — JSON schema validation, recipe source URL must be reachable & on an allowed domain, hard block of anything suggesting raw/undercooked meat, eggs, seafood without warnings, no medical claims, no weight-loss promises.
4. **Abuse guardrails** — per-user rate limits (10 detections/hour on free tier), per-IP limits, prompt-injection sanitization on the editable ingredient list.

---

## 8. Privacy & Safety

- Photos deleted from object storage after **24 hours** (lifecycle rule).
- No photos used for model training without explicit opt-in.
- No PII in logs; request IDs only.
- Age-gate on alcohol-containing recipe suggestions.
- Allergy warning banner if user has declared allergies and a recipe contains them.
- Region-aware: in India we surface paneer/ghee/curd prominently; in vegetarian-majority regions we default `diet = vegetarian` on first launch (user can change).

---

## 9. Milestones

| Week | Deliverable |
|---|---|
| 1 | Backend scaffolding, `/detect` endpoint wired to vision model, guardrails module, unit tests green. |
| 2 | Agent wired to `/suggest`, Indian-first logic, schema validation, recipe cache. |
| 3 | React Native app: camera flow, ingredient edit screen, recipe list + detail. |
| 4 | Auth, rate limiting, Sentry, Firebase/Clerk integration. |
| 5 | Closed beta (TestFlight + Play Internal), gather 50 users of feedback. |
| 6 | Public launch v1. |

---

## 10. Success Metrics

- **Activation:** % of installs that complete at least one scan → recipe view within 24h. Target: **50%**.
- **Quality:** Median ingredient-detection precision ≥ **85%** (human-labeled sample of 200 photos).
- **Relevance:** At least **60%** of v1 sessions result in user tapping into a recipe detail.
- **Retention:** D7 retention ≥ **25%**.
- **Latency:** p95 end-to-end (shutter → recipe list) ≤ **8 seconds**.
