import { create } from "zustand";
import type { DetectedIngredient } from "../api/ingredients";
import type { RecipeDTO, RecipePreferences } from "../api/recipes";

interface AppState {
  photoUris: string[];
  addPhoto: (uri: string) => void;
  removePhoto: (uri: string) => void;
  clearPhotos: () => void;

  ingredients: DetectedIngredient[];
  setIngredients: (items: DetectedIngredient[]) => void;
  addIngredient: (name: string) => void;
  removeIngredient: (name: string) => void;

  allergenWarnings: string[];
  setAllergenWarnings: (warnings: string[]) => void;

  preferences: RecipePreferences;
  setPreferences: (prefs: Partial<RecipePreferences>) => void;

  userAge: number | null;
  setUserAge: (age: number | null) => void;

  recipes: RecipeDTO[];
  setRecipes: (recipes: RecipeDTO[]) => void;
}

const DEFAULT_PREFS: RecipePreferences = {
  cuisine_preference: "indian_first",
  diet: "any",
  spice_level: "medium",
  max_cook_time_minutes: 60,
  servings: 2,
};

export const useAppStore = create<AppState>((set) => ({
  photoUris: [],
  addPhoto: (uri) =>
    set((s) => ({
      photoUris: s.photoUris.length < 5 ? [...s.photoUris, uri] : s.photoUris,
    })),
  removePhoto: (uri) =>
    set((s) => ({ photoUris: s.photoUris.filter((u) => u !== uri) })),
  clearPhotos: () => set({ photoUris: [] }),

  ingredients: [],
  setIngredients: (items) => set({ ingredients: items }),
  addIngredient: (name) =>
    set((s) => ({
      ingredients: s.ingredients.some((i) => i.name === name)
        ? s.ingredients
        : [...s.ingredients, { name, display_name: name, confidence: 1, quantity_hint: "" }],
    })),
  removeIngredient: (name) =>
    set((s) => ({ ingredients: s.ingredients.filter((i) => i.name !== name) })),

  allergenWarnings: [],
  setAllergenWarnings: (warnings) => set({ allergenWarnings: warnings }),

  preferences: DEFAULT_PREFS,
  setPreferences: (prefs) =>
    set((s) => ({ preferences: { ...s.preferences, ...prefs } })),

  userAge: null,
  setUserAge: (age) => set({ userAge: age }),

  recipes: [],
  setRecipes: (recipes) => set({ recipes }),
}));
