import React, { useRef, useState } from "react";
import {
  View, Text, TouchableOpacity, Image, FlatList,
  StyleSheet, Alert, ActivityIndicator,
} from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";
import * as ImagePicker from "expo-image-picker";
import { useRouter } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { useAppStore } from "../src/store/useAppStore";
import { detectIngredients } from "../src/api/ingredients";
import { trackEvent } from "../src/hooks/useAnalytics";

export default function ScanScreen() {
  const router = useRouter();
  const [permission, requestPermission] = useCameraPermissions();
  const [cameraOpen, setCameraOpen] = useState(false);
  const cameraRef = useRef<CameraView>(null);

  const photoUris = useAppStore((s) => s.photoUris);
  const addPhoto = useAppStore((s) => s.addPhoto);
  const removePhoto = useAppStore((s) => s.removePhoto);
  const clearPhotos = useAppStore((s) => s.clearPhotos);
  const setIngredients = useAppStore((s) => s.setIngredients);
  const setAllergenWarnings = useAppStore((s) => s.setAllergenWarnings);

  const detectMutation = useMutation({
    mutationFn: () => detectIngredients(photoUris),
    onSuccess: (data) => {
      setIngredients(data.ingredients);
      setAllergenWarnings(data.allergen_warnings ?? []);
      trackEvent("scan_complete", { ingredient_count: data.ingredients.length });
      router.push("/ingredients");
    },
    onError: () =>
      Alert.alert("Error", "Could not detect ingredients. Please try again."),
  });

  async function takePicture() {
    if (!cameraRef.current) return;
    const photo = await cameraRef.current.takePictureAsync({ quality: 0.7 });
    if (photo?.uri) {
      addPhoto(photo.uri);
      if (photoUris.length + 1 >= 5) setCameraOpen(false);
    }
  }

  async function pickFromLibrary() {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsMultipleSelection: true,
      selectionLimit: 5 - photoUris.length,
      quality: 0.7,
    });
    if (!result.canceled) {
      result.assets.forEach((a) => addPhoto(a.uri));
    }
  }

  if (cameraOpen) {
    if (!permission?.granted) {
      requestPermission();
      setCameraOpen(false);
      return null;
    }
    return (
      <View style={styles.flex}>
        <CameraView ref={cameraRef} style={styles.flex} facing="back" />
        <View style={styles.cameraControls}>
          <TouchableOpacity style={styles.captureBtn} onPress={takePicture} />
          <TouchableOpacity
            style={styles.doneBtn}
            onPress={() => setCameraOpen(false)}
          >
            <Text style={styles.doneBtnText}>Done ({photoUris.length}/5)</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.headline}>Point your camera at your fridge.</Text>
      <Text style={styles.sub}>Get dinner in under 30 seconds.</Text>

      <FlatList
        data={photoUris}
        horizontal
        keyExtractor={(uri) => uri}
        contentContainerStyle={styles.photoRow}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => removePhoto(item)}>
            <Image source={{ uri: item }} style={styles.thumb} />
            <View style={styles.removeOverlay}>
              <Text style={styles.removeX}>✕</Text>
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={styles.emptyPhotos}>
            <Text style={styles.emptyText}>No photos yet — add up to 5</Text>
          </View>
        }
      />

      <View style={styles.actions}>
        <TouchableOpacity
          style={[styles.btn, styles.btnOutline, photoUris.length >= 5 && styles.btnDisabled]}
          onPress={() => { trackEvent("scan_initiated"); setCameraOpen(true); }}
          disabled={photoUris.length >= 5}
        >
          <Text style={styles.btnOutlineText}>Camera</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.btn, styles.btnOutline, photoUris.length >= 5 && styles.btnDisabled]}
          onPress={pickFromLibrary}
          disabled={photoUris.length >= 5}
        >
          <Text style={styles.btnOutlineText}>Library</Text>
        </TouchableOpacity>
      </View>

      {photoUris.length > 0 && (
        <TouchableOpacity
          style={[
            styles.btn,
            styles.btnPrimary,
            detectMutation.isPending && styles.btnDisabled,
          ]}
          onPress={() => detectMutation.mutate()}
          disabled={detectMutation.isPending}
        >
          {detectMutation.isPending ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.btnPrimaryText}>Scan Ingredients →</Text>
          )}
        </TouchableOpacity>
      )}

      {photoUris.length > 0 && (
        <TouchableOpacity onPress={clearPhotos} style={styles.clearLink}>
          <Text style={styles.clearLinkText}>Clear all photos</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  container: { flex: 1, backgroundColor: "#F9F5F1", padding: 20 },
  headline: { fontSize: 26, fontWeight: "800", color: "#1a1a1a", marginTop: 20 },
  sub: { fontSize: 15, color: "#888", marginTop: 4, marginBottom: 24 },
  photoRow: { paddingVertical: 8, gap: 10 },
  thumb: { width: 90, height: 90, borderRadius: 10 },
  removeOverlay: {
    position: "absolute",
    top: 4,
    right: 4,
    backgroundColor: "rgba(0,0,0,0.5)",
    borderRadius: 10,
    width: 20,
    height: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  removeX: { color: "#fff", fontSize: 11 },
  emptyPhotos: {
    width: 220,
    height: 90,
    borderRadius: 10,
    backgroundColor: "#eee",
    alignItems: "center",
    justifyContent: "center",
  },
  emptyText: { color: "#aaa", fontSize: 13 },
  actions: { flexDirection: "row", gap: 12, marginTop: 20 },
  btn: {
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 20,
    alignItems: "center",
  },
  btnOutline: { flex: 1, borderWidth: 2, borderColor: "#FF6B35" },
  btnOutlineText: { color: "#FF6B35", fontWeight: "700", fontSize: 15 },
  btnPrimary: {
    backgroundColor: "#FF6B35",
    marginTop: 16,
    width: "100%",
  },
  btnPrimaryText: { color: "#fff", fontWeight: "700", fontSize: 16 },
  btnDisabled: { opacity: 0.4 },
  clearLink: { alignItems: "center", marginTop: 12 },
  clearLinkText: { color: "#aaa", fontSize: 13 },
  cameraControls: {
    position: "absolute",
    bottom: 40,
    left: 0,
    right: 0,
    alignItems: "center",
    gap: 16,
  },
  captureBtn: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: "#fff",
    borderWidth: 4,
    borderColor: "#FF6B35",
  },
  doneBtn: {
    backgroundColor: "rgba(0,0,0,0.6)",
    borderRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: 8,
  },
  doneBtnText: { color: "#fff", fontWeight: "600" },
});
