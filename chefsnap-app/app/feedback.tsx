import React, { useState } from "react";
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, ScrollView,
} from "react-native";
import { useRouter } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { apiClient } from "../src/api/client";
import { trackEvent } from "../src/hooks/useAnalytics";

interface FeedbackPayload {
  rating: number;
  comment: string;
}

async function submitFeedback(body: FeedbackPayload): Promise<void> {
  await apiClient.post("/api/v1/feedback", body);
}

export default function FeedbackScreen() {
  const router = useRouter();
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");

  const mutation = useMutation({
    mutationFn: () => submitFeedback({ rating, comment }),
    onSuccess: () => {
      trackEvent("feedback_submitted", { rating });
      Alert.alert("Thanks!", "Your feedback helps us improve ChefSnap.", [
        { text: "Done", onPress: () => router.back() },
      ]);
    },
    onError: () =>
      Alert.alert("Error", "Could not send feedback. Please try again."),
  });

  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <Text style={styles.title}>How is ChefSnap working for you?</Text>

      <Text style={styles.label}>Rating</Text>
      <View style={styles.stars}>
        {[1, 2, 3, 4, 5].map((n) => (
          <TouchableOpacity key={n} onPress={() => setRating(n)}>
            <Text style={[styles.star, n <= rating && styles.starFilled]}>★</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Comments (optional)</Text>
      <TextInput
        style={styles.input}
        value={comment}
        onChangeText={setComment}
        placeholder="What's working well? What could be better?"
        multiline
        numberOfLines={5}
        textAlignVertical="top"
      />

      <TouchableOpacity
        style={[styles.btn, (rating === 0 || mutation.isPending) && styles.btnDisabled]}
        onPress={() => mutation.mutate()}
        disabled={rating === 0 || mutation.isPending}
      >
        {mutation.isPending ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.btnText}>Send Feedback</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { flex: 1, backgroundColor: "#F9F5F1" },
  container: { padding: 24, paddingBottom: 40 },
  title: { fontSize: 20, fontWeight: "800", color: "#1a1a1a", marginBottom: 28 },
  label: { fontSize: 14, fontWeight: "600", color: "#555", marginBottom: 10 },
  stars: { flexDirection: "row", gap: 8, marginBottom: 24 },
  star: { fontSize: 40, color: "#ddd" },
  starFilled: { color: "#FF6B35" },
  input: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 12,
    padding: 14,
    fontSize: 15,
    minHeight: 120,
    marginBottom: 28,
  },
  btn: {
    backgroundColor: "#FF6B35",
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
  },
  btnText: { color: "#fff", fontWeight: "700", fontSize: 16 },
  btnDisabled: { opacity: 0.4 },
});
