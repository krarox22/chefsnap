import React, { useEffect, useState } from "react";
import { View, Text, FlatList, StyleSheet, TouchableOpacity } from "react-native";
import { useRouter } from "expo-router";
import { useAppStore } from "../src/store/useAppStore";
import { RecipeCard } from "../src/components/RecipeCard";
import { loadCachedRecipes } from "../src/hooks/useOfflineCache";
import type { RecipeDTO } from "../src/api/recipes";

export default function RecipesScreen() {
  const router = useRouter();
  const storeRecipes = useAppStore((s) => s.recipes);
  const [displayed, setDisplayed] = useState<RecipeDTO[]>(storeRecipes);

  useEffect(() => {
    if (storeRecipes.length > 0) {
      setDisplayed(storeRecipes);
    } else {
      loadCachedRecipes().then(setDisplayed);
    }
  }, [storeRecipes]);

  const indianCount = displayed.filter((r) => r.is_indian).length;

  return (
    <View style={styles.container}>
      {displayed.length > 0 && (
        <Text style={styles.summary}>
          {indianCount} Indian · {displayed.length} total
        </Text>
      )}
      <FlatList
        data={displayed}
        keyExtractor={(r) => r.id}
        renderItem={({ item }) => (
          <RecipeCard
            recipe={item}
            onPress={() => router.push(`/recipe/${item.id}`)}
          />
        )}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No recipes found.</Text>
            <TouchableOpacity onPress={() => router.back()}>
              <Text style={styles.backLink}>Go back and adjust ingredients</Text>
            </TouchableOpacity>
          </View>
        }
        contentContainerStyle={styles.list}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F9F5F1" },
  summary: { fontSize: 14, color: "#888", paddingHorizontal: 20, paddingTop: 14 },
  list: { paddingBottom: 24 },
  empty: { alignItems: "center", marginTop: 80 },
  emptyText: { fontSize: 16, color: "#aaa" },
  backLink: { color: "#FF6B35", marginTop: 12, fontSize: 14 },
});
