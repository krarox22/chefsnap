import React from "react";
import { View, Text, StyleSheet } from "react-native";

interface Props {
  warnings: string[];
}

export function AllergyBanner({ warnings }: Props) {
  if (warnings.length === 0) return null;
  return (
    <View style={styles.banner}>
      <Text style={styles.icon}>⚠️</Text>
      <View style={styles.textWrap}>
        <Text style={styles.title}>Allergen detected</Text>
        <Text style={styles.body}>{warnings.join(", ")}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: "row",
    alignItems: "flex-start",
    backgroundColor: "#FFF3CD",
    borderLeftWidth: 4,
    borderLeftColor: "#F59E0B",
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    gap: 10,
  },
  icon: { fontSize: 18 },
  textWrap: { flex: 1 },
  title: { fontSize: 14, fontWeight: "700", color: "#92400E" },
  body: { fontSize: 13, color: "#78350F", marginTop: 2 },
});
