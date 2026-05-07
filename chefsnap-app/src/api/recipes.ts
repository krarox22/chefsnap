import { apiClient } from "./client";

export interface RecipeDTO {
  id: string;
  name: string;
  cuisine: string;
  is_indian: boolean;
  match_percent: number;
  missing_ingredients: string[];
  cook_time_minutes: number;
  difficulty: "easy" | "medium" | "hard";
  source_url: string;
  summary: string;
}

export interface RecipePreferences {
  cuisine_preference: "indian_first" | "any";
  diet: "any" | "vegetarian" | "vegan" | "jain" | "halal" | "gluten-free";
  spice_level: "mild" | "medium" | "hot" | "extra_hot";
  max_cook_time_minutes: number;
  servings: number;
}

export interface SuggestRequest {
  ingredients: string[];
  preferences: RecipePreferences;
}

export interface SuggestResponse {
  recipes: RecipeDTO[];
  indian_count: number;
  total_count: number;
  request_id: string;
  alcohol_warnings?: string[];
}

export async function suggestRecipes(
  body: SuggestRequest,
  userAge?: number | null,
): Promise<SuggestResponse> {
  const params = userAge != null ? `?user_age=${userAge}` : "";
  const { data } = await apiClient.post<SuggestResponse>(
    `/api/v1/recipes/suggest${params}`,
    body,
  );
  return data;
}
