# ChefSnap

**A mobile prototype that turns ingredient photos into recipe suggestions, with an emphasis on Indian cuisine.**

ChefSnap combines a React Native / Expo interface with a FastAPI backend. A vision model extracts ingredients, users can review the ingredient list, and a search-enabled language-model agent produces structured recipe suggestions.

## Implemented features

- **Photo-to-ingredient extraction:** Gemini returns structured names, quantity hints, and model-generated confidence values from uploaded images.
- **Ingredient review:** the mobile interface supports reviewing ingredients before requesting recipes.
- **Recipe search:** a LangChain agent uses Tavily web search to gather recipe information.
- **Structured responses:** a separate model call extracts recipes into Pydantic models, including missing ingredients, cooking time, and source URLs.
- **Preferences:** cuisine, diet, spice level, cooking time, and servings enter the request. Indian-first requests trigger a retry when the returned Indian-recipe share falls below the configured rule.
- **Validation and fallback:** image checks, ingredient normalization, pattern-based injection checks, output checks, rate limiting, and predefined fallback recipes handle selected failure cases.
- **Supporting infrastructure:** in-memory recipe caching, optional backend authentication, feedback endpoints, and optional tracing/error monitoring. The mobile app integrates Clerk sign-in.

## Architecture

```text
Ingredient photos
      |
      v
FastAPI upload checks -> Gemini structured ingredient extraction
      |
      v
Ingredient normalization + user review
      |
      v
LangChain agent + Tavily recipe search
      |
      v
Structured recipe extraction -> validation / retry / fallback
      |
      v
Recipe cards in the Expo app
```

Search and structured extraction are separate stages. The agent gathers recipe information; a second call converts it into `SuggestionResponseDTO`. Failed agent calls or repeated extraction failures can return predefined fallback recipes.

## Run the backend

Use Python 3.10 or newer and a virtual environment.

```bash
git clone https://github.com/krarox22/chefsnap.git
cd chefsnap
python -m venv .venv
source .venv/bin/activate
python -m pip install -r chefsnap-backend/requirements.txt
python -m pip install langchain-tavily
```

`langchain-tavily` is required by `agent.py` but is not currently listed in the backend requirements file.

Create `.env` in the repository root. Replace the model placeholders with Gemini model IDs supported by your account; defaults in `config.py` reference `gemini-1.5-flash` and may need updating.

```dotenv
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
CHEFSNAP_VISION_MODEL=your_supported_gemini_vision_model
CHEFSNAP_AGENT_MODEL=your_supported_gemini_agent_model
```

Keep credentials out of version control. Model and search calls use external services and may incur charges.

```bash
cd chefsnap-backend
uvicorn main:app --reload --port 8000
```

The backend serves a test interface at `http://localhost:8000/` and API documentation at `http://localhost:8000/docs`.

## Run the mobile app

From the repository root:

```bash
cd chefsnap-app
npm install
npm start
```

Configure the app's Expo environment:

```dotenv
EXPO_PUBLIC_API_BASE=http://your_backend_host:8000
EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
```

On a physical device, `localhost` points to the device rather than your computer. Use a backend address reachable from the device and configure the server's bind address as needed. The app mounts a Clerk provider; configure a Clerk application for sign-in. Backend token verification uses `CLERK_JWKS_URL` when configured.

## API surface

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Liveness and version |
| `POST /api/v1/ingredients/detect` | Upload ingredient images |
| `POST /api/v1/recipes/suggest` | Request recipes from ingredients and preferences |
| `POST /api/v1/feedback` | Submit a rating and comment |
| `GET /api/v1/metrics` | Inspect collected request metrics |

## Tests and evaluation

```bash
cd chefsnap-backend
python -m pytest tests -v
```

The suite includes tests for image/ingredient validation, aliases and diet filtering, recipe output checks, prompt construction, retry/fallback behavior, caching, and API responses. Model and search interactions are mocked in the relevant fixtures and tests.

Mocked tests verify software behavior; they do not measure ingredient-detection accuracy, recipe factuality, or allergy safety. Model-generated confidence and recipe match percentages are output fields rather than calibrated performance measurements. No model-quality benchmark or controlled user study is reported here.

## Code guide

| Path | Role |
| --- | --- |
| [`chefsnap-app/`](chefsnap-app/) | Expo screens, API client, and application state |
| [`chefsnap-backend/main.py`](chefsnap-backend/main.py) | FastAPI endpoints and request processing |
| [`chefsnap-backend/vision.py`](chefsnap-backend/vision.py) | Structured Gemini ingredient extraction |
| [`chefsnap-backend/agent.py`](chefsnap-backend/agent.py) | Search, extraction, retries, and fallback recipes |
| [`chefsnap-backend/guardrails.py`](chefsnap-backend/guardrails.py) | Data models and validation rules |
| [`chefsnap-backend/cache.py`](chefsnap-backend/cache.py) | In-memory recipe cache with TTL |
| [`chefsnap-backend/tests/`](chefsnap-backend/tests/) | Backend test suite |

## Technical scope and limitations

This project demonstrates pretrained vision/language model integration, tool use, structured extraction, API design, and a mobile interface. It does not train a new model.

Schema validation checks structure and selected field rules, not factual correctness. Pattern-based injection checks and ingredient filters have limited coverage. Some invalid outputs are corrected or retained after retry; these controls do not guarantee every suggestion satisfies every preference. Users should review ingredients and recipe details, especially for allergies.

The recipe cache is in memory. Redis is used optionally for rate limiting, with an in-memory fallback. Some deployment features in `plan.md` describe intended work rather than current implementation.
