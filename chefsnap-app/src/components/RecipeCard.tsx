import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import type { RecipeDTO } from "../api/recipes";

interface Props {
  recipe: RecipeDTO;
  onPress: () => void;
}

export function RecipeCard({ recipe, onPress }: Props) {
  return (
    <TouchableOpacity style={styles.card} onPress={onPress}>
      {recipe.is_indian && (
        <View style={styles.badge}>
          <Text style={styles.badgeText}>Indian</Text>
        </View>
      )}
      <Text style={styles.name}>{recipe.name}</Text>
      <Text style={styles.cuisine}>{recipe.cuisine}</Text>
      <Text style={styles.summary} numberOfLines={2}>{recipe.summary}</Text>
      <View style={styles.meta}>
        <Text style={styles.metaItem}>{recipe.cook_time_minutes} min</Text>
        <Text style={styles.metaItem}>{recipe.difficulty}</Text>
        <Text style={[styles.metaItem, styles.match]}>{recipe.match_percent}% match</Text>
      </View>
      {recipe.missing_ingredients.length > 0 && (
        <Text style={styles.missing}>
          Missing: {recipe.missing_ingredients.join(", ")}
        </Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 3,
  },
  badge: {
    alignSelf: "flex-start",
    backgroundColor: "#FF6B35",
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginBottom: 8,
  },
  badgeText: { color: "#fff", fontSize: 11, fontWeight: "600" },
  name: { fontSize: 17, fontWeight: "700", color: "#1a1a1a", marginBottom: 2 },
  cuisine: { fontSize: 13, color: "#888", marginBottom: 6 },
  summary: { fontSize: 14, color: "#555", marginBottom: 10 },
  meta: { flexDirection: "row", gap: 12 },
  metaItem: { fontSize: 13, color: "#666" },
  match: { color: "#2e9e5b", fontWeight: "600" },
  missing: { fontSize: 12, color: "#e07b00", marginTop: 8 },
});
