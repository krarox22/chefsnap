import React from "react";
import { TouchableOpacity, Text, StyleSheet } from "react-native";

interface Props {
  label: string;
  onRemove: () => void;
}

export function IngredientChip({ label, onRemove }: Props) {
  return (
    <TouchableOpacity style={styles.chip} onPress={onRemove}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.x}>✕</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  chip: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFF0E8",
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    margin: 4,
    borderWidth: 1,
    borderColor: "#FF6B35",
  },
  label: { color: "#333", fontSize: 14, marginRight: 6 },
  x: { color: "#FF6B35", fontSize: 12, fontWeight: "bold" },
});
