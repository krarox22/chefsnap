import React from "react";
import { ScrollView, TouchableOpacity, Text, StyleSheet } from "react-native";
import type { RecipePreferences } from "../api/recipes";

const DIET_OPTIONS: RecipePreferences["diet"][] = [
  "any",
  "vegetarian",
  "vegan",
  "jain",
  "halal",
  "gluten-free",
];

interface Props {
  selected: RecipePreferences["diet"];
  onChange: (diet: RecipePreferences["diet"]) => void;
}

export function DietFilterBar({ selected, onChange }: Props) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.container}
    >
      {DIET_OPTIONS.map((d) => (
        <TouchableOpacity
          key={d}
          style={[styles.pill, d === selected && styles.pillActive]}
          onPress={() => onChange(d)}
        >
          <Text style={[styles.pillText, d === selected && styles.pillTextActive]}>
            {d.charAt(0).toUpperCase() + d.slice(1)}
          </Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { paddingHorizontal: 0, paddingVertical: 10, gap: 8 },
  pill: {
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#ccc",
    paddingHorizontal: 14,
    paddingVertical: 6,
    backgroundColor: "#fff",
  },
  pillActive: { backgroundColor: "#FF6B35", borderColor: "#FF6B35" },
  pillText: { fontSize: 13, color: "#555" },
  pillTextActive: { color: "#fff", fontWeight: "600" },
});
