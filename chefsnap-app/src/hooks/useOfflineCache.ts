import AsyncStorage from "@react-native-async-storage/async-storage";
import type { RecipeDTO } from "../api/recipes";

const CACHE_KEY = "chefsnap_recent_recipes";
const MAX_CACHED = 10;

export async function cacheRecipes(recipes: RecipeDTO[]): Promise<void> {
  try {
    const existing = await loadCachedRecipes();
    const merged = [...recipes, ...existing]
      .filter((r, i, arr) => arr.findIndex((x) => x.id === r.id) === i)
      .slice(0, MAX_CACHED);
    await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(merged));
  } catch {
    // non-fatal
  }
}

export async function loadCachedRecipes(): Promise<RecipeDTO[]> {
  try {
    const raw = await AsyncStorage.getItem(CACHE_KEY);
    return raw ? (JSON.parse(raw) as RecipeDTO[]) : [];
  } catch {
    return [];
  }
}
