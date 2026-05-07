import React, { useEffect } from "react";
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, Linking,
} from "react-native";
import { useLocalSearchParams, useNavigation } from "expo-router";
import { useAppStore } from "../../src/store/useAppStore";
import { trackEvent } from "../../src/hooks/useAnalytics";

export default function RecipeDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const navigation = useNavigation();
  const recipes = useAppStore((s) => s.recipes);
  const recipe = recipes.find((r) => r.id === id);

  useEffect(() => {
    if (recipe) {
      navigation.setOptions({ title: recipe.name });
      trackEvent("recipe_detail_opened", { recipe_id: recipe.id, is_indian: recipe.is_indian });
    }
  }, [recipe, navigation]);

  if (!recipe) {
    return (
      <View style={styles.center}>
        <Text style={styles.notFound}>Recipe not found.</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {recipe.is_indian && (
        <View style={styles.badge}>
          <Text style={styles.badgeText}>Indian</Text>
        </View>
      )}

      <Text style={styles.name}>{recipe.name}</Text>
      <Text style={styles.cuisine}>{recipe.cuisine}</Text>

      <View style={styles.metaRow}>
        <View style={styles.metaBox}>
          <Text style={styles.metaValue}>{recipe.cook_time_minutes}</Text>
          <Text style={styles.metaLabel}>minutes</Text>
        </View>
        <View style={styles.metaBox}>
          <Text style={styles.metaValue}>{recipe.difficulty}</Text>
          <Text style={styles.metaLabel}>difficulty</Text>
        </View>
        <View style={styles.metaBox}>
          <Text style={[styles.metaValue, styles.matchValue]}>{recipe.match_percent}%</Text>
          <Text style={styles.metaLabel}>match</Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Summary</Text>
      <Text style={styles.body}>{recipe.summary}</Text>

      {recipe.missing_ingredients.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>You'll also need</Text>
          {recipe.missing_ingredients.map((m) => (
            <Text key={m} style={styles.missingItem}>• {m}</Text>
          ))}
        </>
      )}

      <TouchableOpacity
        style={styles.sourceBtn}
        onPress={() => Linking.openURL(recipe.source_url)}
      >
        <Text style={styles.sourceBtnText}>Full Recipe →</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F9F5F1" },
  content: { padding: 20, paddingBottom: 40 },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  notFound: { color: "#aaa", fontSize: 16 },
  badge: {
    alignSelf: "flex-start",
    backgroundColor: "#FF6B35",
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 3,
    marginBottom: 10,
  },
  badgeText: { color: "#fff", fontSize: 12, fontWeight: "600" },
  name: { fontSize: 26, fontWeight: "800", color: "#1a1a1a", marginBottom: 4 },
  cuisine: { fontSize: 15, color: "#888", marginBottom: 20 },
  metaRow: { flexDirection: "row", gap: 12, marginBottom: 24 },
  metaBox: {
    flex: 1,
    backgroundColor: "#fff",
    borderRadius: 10,
    padding: 14,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 2,
  },
  metaValue: { fontSize: 20, fontWeight: "700", color: "#1a1a1a" },
  matchValue: { color: "#2e9e5b" },
  metaLabel: { fontSize: 12, color: "#888", marginTop: 2 },
  sectionTitle: { fontSize: 16, fontWeight: "700", color: "#333", marginBottom: 8 },
  body: { fontSize: 15, color: "#555", lineHeight: 22, marginBottom: 20 },
  missingItem: { fontSize: 14, color: "#e07b00", marginBottom: 4, paddingLeft: 4 },
  sourceBtn: {
    backgroundColor: "#FF6B35",
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 24,
  },
  sourceBtnText: { color: "#fff", fontWeight: "700", fontSize: 16 },
});
