import React, { useState } from "react";
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  Alert, Switch,
} from "react-native";
import { useAuth } from "@clerk/clerk-expo";
import { useRouter } from "expo-router";
import { useAppStore } from "../src/store/useAppStore";
import { trackEvent } from "../src/hooks/useAnalytics";

export default function SettingsScreen() {
  const router = useRouter();
  const { signOut } = useAuth();

  const userAge = useAppStore((s) => s.userAge);
  const setUserAge = useAppStore((s) => s.setUserAge);
  const preferences = useAppStore((s) => s.preferences);
  const setPreferences = useAppStore((s) => s.setPreferences);

  const [ageInput, setAgeInput] = useState(userAge?.toString() ?? "");

  function saveAge() {
    const parsed = parseInt(ageInput, 10);
    if (!isNaN(parsed) && parsed >= 13 && parsed <= 120) {
      setUserAge(parsed);
      Alert.alert("Saved", "Age updated.");
    } else {
      Alert.alert("Invalid", "Enter a valid age between 13 and 120.");
    }
  }

  async function handleSignOut() {
    Alert.alert("Sign out", "Are you sure?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Sign out",
        style: "destructive",
        onPress: async () => {
          trackEvent("sign_out");
          await signOut();
          router.replace("/(auth)/sign-in");
        },
      },
    ]);
  }

  return (
    <View style={styles.container}>
      <Text style={styles.section}>Preferences</Text>

      <View style={styles.row}>
        <Text style={styles.rowLabel}>Indian-first recipes</Text>
        <Switch
          value={preferences.cuisine_preference === "indian_first"}
          onValueChange={(v) =>
            setPreferences({ cuisine_preference: v ? "indian_first" : "any" })
          }
          trackColor={{ true: "#FF6B35" }}
        />
      </View>

      <Text style={styles.section}>Age verification</Text>
      <Text style={styles.hint}>
        Used for the alcohol age-gate on recipe suggestions (plan.md §8).
      </Text>
      <View style={styles.ageRow}>
        <TextInput
          style={styles.ageInput}
          value={ageInput}
          onChangeText={setAgeInput}
          placeholder="Your age"
          keyboardType="number-pad"
          maxLength={3}
        />
        <TouchableOpacity style={styles.saveBtn} onPress={saveAge}>
          <Text style={styles.saveBtnText}>Save</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.section}>Feedback</Text>
      <TouchableOpacity
        style={styles.feedbackBtn}
        onPress={() => router.push("/feedback")}
      >
        <Text style={styles.feedbackBtnText}>Leave feedback →</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.signOutBtn} onPress={handleSignOut}>
        <Text style={styles.signOutText}>Sign out</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F9F5F1", padding: 20 },
  section: {
    fontSize: 13,
    fontWeight: "700",
    color: "#888",
    textTransform: "uppercase",
    letterSpacing: 0.8,
    marginTop: 28,
    marginBottom: 10,
  },
  hint: { fontSize: 13, color: "#aaa", marginBottom: 10 },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 10,
    padding: 14,
  },
  rowLabel: { fontSize: 15, color: "#333" },
  ageRow: { flexDirection: "row", gap: 10, alignItems: "center" },
  ageInput: {
    flex: 1,
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 15,
  },
  saveBtn: {
    backgroundColor: "#FF6B35",
    borderRadius: 10,
    paddingHorizontal: 18,
    paddingVertical: 10,
  },
  saveBtnText: { color: "#fff", fontWeight: "700" },
  feedbackBtn: {
    backgroundColor: "#fff",
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    borderColor: "#FF6B35",
  },
  feedbackBtnText: { color: "#FF6B35", fontWeight: "600", fontSize: 15 },
  signOutBtn: {
    marginTop: 40,
    backgroundColor: "#fff",
    borderRadius: 10,
    padding: 14,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#e00",
  },
  signOutText: { color: "#e00", fontWeight: "700", fontSize: 15 },
});
