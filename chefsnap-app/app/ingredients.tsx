import React, { useState } from "react";
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, Alert, ActivityIndicator, ScrollView,
} from "react-native";
import { useRouter } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { useAppStore } from "../src/store/useAppStore";
import { IngredientChip } from "../src/components/IngredientChip";
import { DietFilterBar } from "../src/components/DietFilterBar";
import { AllergyBanner } from "../src/components/AllergyBanner";
import { suggestRecipes } from "../src/api/recipes";
import { cacheRecipes, loadCachedRecipes } from "../src/hooks/useOfflineCache";
import { trackEvent } from "../src/hooks/useAnalytics";
import type { RecipePreferences } from "../src/api/recipes";

export default function IngredientsScreen() {
  const router = useRouter();
  const [newItem, setNewItem] = useState("");

  const ingredients = useAppStore((s) => s.ingredients);
  const addIngredient = useAppStore((s) => s.addIngredient);
  const removeIngredient = useAppStore((s) => s.removeIngredient);
  const preferences = useAppStore((s) => s.preferences);
  const setPreferences = useAppStore((s) => s.setPreferences);
  const setRecipes = useAppStore((s) => s.setRecipes);
  const allergenWarnings = useAppStore((s) => s.allergenWarnings);
  const userAge = useAppStore((s) => s.userAge);

  const suggestMutation = useMutation({
    mutationFn: () =>
      suggestRecipes(
        { ingredients: ingredients.map((i) => i.name), preferences },
        userAge,
      ),
    onSuccess: async (data) => {
      setRecipes(data.recipes);
      await cacheRecipes(data.recipes);
      trackEvent("recipes_viewed", { total: data.total_count, indian: data.indian_count });
      router.push("/recipes");
    },
    onError: async () => {
      Alert.alert("Error", "Could not fetch recipes. Showing cached results.");
      const cached = await loadCachedRecipes();
      setRecipes(cached);
      router.push("/recipes");
    },
  });

  function addNewIngredient() {
    const trimmed = newItem.trim().toLowerCase();
    if (trimmed) {
      addIngredient(trimmed);
      setNewItem("");
    }
  }

  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <AllergyBanner warnings={allergenWarnings} />

      <Text style={styles.sectionTitle}>Detected Ingredients</Text>
      <Text style={styles.hint}>Tap any chip to remove it.</Text>

      <View style={styles.chipWrap}>
        {ingredients.map((i) => (
          <IngredientChip
            key={i.name}
            label={i.display_name}
            onRemove={() => removeIngredient(i.name)}
          />
        ))}
      </View>

      <View style={styles.addRow}>
        <TextInput
          style={styles.input}
          value={newItem}
          onChangeText={setNewItem}
          placeholder="Add an ingredient..."
          onSubmitEditing={addNewIngredient}
          returnKeyType="done"
        />
        <TouchableOpacity style={styles.addBtn} onPress={addNewIngredient}>
          <Text style={styles.addBtnText}>+</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.sectionTitle}>Dietary Filter</Text>
      <DietFilterBar
        selected={preferences.diet}
        onChange={(diet: RecipePreferences["diet"]) => setPreferences({ diet })}
      />

      <TouchableOpacity
        style={[
          styles.findBtn,
          (ingredients.length === 0 || suggestMutation.isPending) && styles.btnDisabled,
        ]}
        onPress={() => suggestMutation.mutate()}
        disabled={ingredients.length === 0 || suggestMutation.isPending}
      >
        {suggestMutation.isPending ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.findBtnText}>Find Recipes →</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { flex: 1, backgroundColor: "#F9F5F1" },
  container: { padding: 20, paddingBottom: 40 },
  sectionTitle: { fontSize: 16, fontWeight: "700", color: "#333", marginTop: 20, marginBottom: 4 },
  hint: { fontSize: 13, color: "#aaa", marginBottom: 10 },
  chipWrap: { flexDirection: "row", flexWrap: "wrap" },
  addRow: { flexDirection: "row", marginTop: 12, gap: 10, alignItems: "center" },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: "#fff",
    fontSize: 15,
  },
  addBtn: {
    width: 44,
    height: 44,
    borderRadius: 10,
    backgroundColor: "#FF6B35",
    alignItems: "center",
    justifyContent: "center",
  },
  addBtnText: { color: "#fff", fontSize: 22, lineHeight: 26 },
  findBtn: {
    backgroundColor: "#FF6B35",
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 24,
  },
  findBtnText: { color: "#fff", fontWeight: "700", fontSize: 16 },
  btnDisabled: { opacity: 0.4 },
});
