"""agent.py — ChefSnap recipe suggestion agent
Two-step pipeline:
  Step A) LangChain agent (create_agent) gathers recipe research via Tavily
  Step B) Structured LLM extracts the strict SuggestionResponseDTO schema

Indian-first re-sorting applied post extraction (plan.md §6.2).
Output schema validated with OutputGuardrails; retries once on failure.
Falls back to a curated offline index if Tavily or LLM is unavailable.
"""

import concurrent.futures
import os
import uuid
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from config import (
    AGENT_MODEL, AGENT_TEMPERATURE, AGENT_MAX_SEARCH_RESULTS,
    AGENT_TIMEOUT_SECONDS, INDIAN_DOMAINS_SEARCH_QUERY,
)
from guardrails import (
    RecipeRequestDTO, SuggestionResponseDTO, RecipeDTO, OutputGuardrails,
    IngredientGuardrails,
)


# ─────────────────────────────────────────────────────────────────────────────
# CURATED OFFLINE FALLBACK — returned when Tavily / LLM is unavailable
# ─────────────────────────────────────────────────────────────────────────────

OFFLINE_RECIPES: List[dict] = [
    {
        "id": "offline_001", "name": "Dal Tadka", "cuisine": "North Indian",
        "is_indian": True, "match_percent": 70, "missing_ingredients": ["dal"],
        "cook_time_minutes": 30, "difficulty": "easy",
        "source_url": "https://www.indianhealthyrecipes.com/dal-tadka/",
        "summary": "Creamy yellow lentils tempered with cumin, garlic and ghee.",
    },
    {
        "id": "offline_002", "name": "Jeera Rice", "cuisine": "North Indian",
        "is_indian": True, "match_percent": 85, "missing_ingredients": [],
        "cook_time_minutes": 20, "difficulty": "easy",
        "source_url": "https://www.indianhealthyrecipes.com/jeera-rice/",
        "summary": "Fragrant cumin-scented basmati rice, a classic accompaniment.",
    },
    {
        "id": "offline_003", "name": "Paneer Butter Masala", "cuisine": "North Indian",
        "is_indian": True, "match_percent": 60, "missing_ingredients": ["cream", "butter"],
        "cook_time_minutes": 35, "difficulty": "medium",
        "source_url": "https://www.indianhealthyrecipes.com/paneer-butter-masala/",
        "summary": "Rich tomato-cream gravy with tender paneer cubes.",
    },
    {
        "id": "offline_004", "name": "Masala Chai", "cuisine": "Indian",
        "is_indian": True, "match_percent": 90, "missing_ingredients": [],
        "cook_time_minutes": 10, "difficulty": "easy",
        "source_url": "https://www.indianhealthyrecipes.com/masala-chai/",
        "summary": "Spiced milky Indian tea with cardamom, ginger and cloves.",
    },
    {
        "id": "offline_005", "name": "Aloo Paratha", "cuisine": "Punjabi",
        "is_indian": True, "match_percent": 65, "missing_ingredients": ["wheat flour"],
        "cook_time_minutes": 40, "difficulty": "medium",
        "source_url": "https://www.indianhealthyrecipes.com/aloo-paratha/",
        "summary": "Spiced potato-stuffed whole wheat flatbread, best served with curd.",
    },
]


def _offline_response(request: RecipeRequestDTO) -> SuggestionResponseDTO:
    recipes = [RecipeDTO(**r) for r in OFFLINE_RECIPES]
    return SuggestionResponseDTO(
        recipes=recipes,
        indian_count=len(recipes),
        total_count=len(recipes),
        request_id=f"req_offline_{uuid.uuid4().hex[:6]}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# AGENT SERVICE
# ─────────────────────────────────────────────────────────────────────────────

class RecipeAgentService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=AGENT_MODEL, temperature=AGENT_TEMPERATURE
        )
        self.structured_llm = self.llm.with_structured_output(SuggestionResponseDTO)
        self.search_tool = TavilySearch(max_results=AGENT_MAX_SEARCH_RESULTS)
        self.tools = [self.search_tool]

    def _build_system_prompt(self, request: RecipeRequestDTO) -> str:
        prefs = request.preferences
        ing_str = ", ".join(request.ingredients)

        cuisine_rule = (
            f"CRITICAL: Prioritize Indian cuisine (North/South Indian, Bengali, Gujarati, "
            f"Maharashtrian, Indo-Chinese). At least 70% of results MUST be Indian. "
            f"Search on: {INDIAN_DOMAINS_SEARCH_QUERY}."
            if prefs.cuisine_preference == "indian_first"
            else "Suggest a diverse range of global recipes."
        )

        diet_rule = (
            f"Strictly enforce '{prefs.diet}' diet. Do not include any incompatible ingredients."
            if prefs.diet != "any"
            else ""
        )

        return (
            f"You are an expert personal chef. The user has: {ing_str}.\n"
            f"Preferences: spice={prefs.spice_level}, max_time={prefs.max_cook_time_minutes}min, "
            f"servings={prefs.servings}.\n\n"
            f"{cuisine_rule}\n{diet_rule}\n\n"
            "Use the web search tool to find 5–8 well-reviewed recipes. "
            "For each recipe compute: missing ingredients vs what the user has, "
            "match_percent (0–100), precise cook_time_minutes, difficulty (easy/medium/hard), "
            "and a source_url from a reputable recipe domain."
        )

    def _extract_structured(self, raw_text: str, ingredients: List[str]) -> SuggestionResponseDTO:
        """Call the structured LLM to parse agent's research text into the schema."""
        prompt = (
            f"Extract recipes from the chef's research below into the strict JSON schema. "
            f"Set is_indian=true for all Indian dishes. "
            f"User has: {', '.join(ingredients)}. "
            f"match_percent MUST be 0–100. difficulty MUST be 'easy', 'medium', or 'hard'.\n\n"
            f"Research:\n{raw_text}"
        )
        return self.structured_llm.invoke(prompt)

    def _run_agent(self, system_prompt: str) -> str:
        """
        Run the LangChain agent with Tavily search and return its final text output.
        Uses the new create_agent API (LangChain >= 1.2).
        """
        agent_graph = create_agent(
            self.llm,
            self.tools,
            system_prompt=system_prompt,
        )
        result = agent_graph.invoke({
            "messages": [HumanMessage(content="Find me recipes using my available ingredients!")]
        })
        # The graph returns AgentState; final message is the AI response
        messages = result.get("messages", [])
        if messages:
            return messages[-1].content
        return ""

    def suggest_recipes(self, request: RecipeRequestDTO) -> SuggestionResponseDTO:
        # ── Step A: Prompt-injection sanitization on free-text ingredients ──
        try:
            request.ingredients = IngredientGuardrails.sanitize_free_text_list(request.ingredients)
        except ValueError as e:
            raise ValueError(f"Ingredient validation failed: {e}")

        # ── Step B: Agent researches recipes via Tavily ──
        system_prompt = self._build_system_prompt(request)
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self._run_agent, system_prompt)
                raw_output = future.result(timeout=AGENT_TIMEOUT_SECONDS)
        except Exception:
            return _offline_response(request)

        # ── Step C: Structured extraction with one retry loop ──
        for attempt in range(2):
            try:
                response = self._extract_structured(raw_output, request.ingredients)
            except Exception:
                if attempt == 0:
                    continue
                return _offline_response(request)

            errors = OutputGuardrails.validate_schema(response)
            if not errors or attempt == 1:
                break  # accept (errors clamped in-place by validate_schema)

        # ── Step D: Indian-first re-sort (plan.md §6.2) ──
        indian = [r for r in response.recipes if r.is_indian]
        non_indian = [r for r in response.recipes if not r.is_indian]

        # ── Step E: 70% re-invocation (plan.md §6.3) ──
        # If Indian-first is requested AND fewer than 70% of recipes are Indian,
        # re-invoke the agent once with a stronger instruction.
        if (
            request.preferences.cuisine_preference == "indian_first"
            and response.recipes
            and len(indian) / len(response.recipes) < 0.70
        ):
            stronger_prompt = (
                self._build_system_prompt(request)
                + "\n\nPREVIOUS RESPONSE DID NOT MEET THE 70% INDIAN REQUIREMENT. "
                "You MUST now suggest MORE Indian dishes. "
                "Replace non-Indian recipes with additional Indian options."
            )
            try:
                raw_output2 = self._run_agent(stronger_prompt)
                response2 = self._extract_structured(raw_output2, request.ingredients)
                OutputGuardrails.validate_schema(response2)
                indian2 = [r for r in response2.recipes if r.is_indian]
                # Only accept the retry if it actually improved the Indian ratio
                if response2.recipes and len(indian2) / len(response2.recipes) >= 0.70:
                    response = response2
                    indian = indian2
                    non_indian = [r for r in response2.recipes if not r.is_indian]
            except Exception:
                pass  # keep original response if retry fails

        response.recipes = indian + non_indian
        response.indian_count = len(indian)
        response.total_count = len(response.recipes)
        response.request_id = f"req_{uuid.uuid4().hex[:8]}"

        return response



recipe_agent_service = RecipeAgentService()
