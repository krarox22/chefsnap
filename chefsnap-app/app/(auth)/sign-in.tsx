import React from "react";
import {
  View, Text, TouchableOpacity, StyleSheet, ActivityIndicator,
} from "react-native";
import { useOAuth } from "@clerk/clerk-expo";
import * as WebBrowser from "expo-web-browser";

WebBrowser.maybeCompleteAuthSession();

export default function SignInScreen() {
  const [loading, setLoading] = React.useState(false);

  const { startOAuthFlow: googleFlow } = useOAuth({ strategy: "oauth_google" });
  const { startOAuthFlow: appleFlow } = useOAuth({ strategy: "oauth_apple" });

  async function signIn(flow: typeof googleFlow) {
    setLoading(true);
    try {
      const { createdSessionId, setActive } = await flow();
      if (createdSessionId && setActive) {
        await setActive({ session: createdSessionId });
      }
    } catch (err) {
      console.error("OAuth error", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.logo}>🍴</Text>
      <Text style={styles.title}>ChefSnap</Text>
      <Text style={styles.sub}>Point your camera at your fridge. Get dinner.</Text>

      {loading ? (
        <ActivityIndicator color="#FF6B35" size="large" style={styles.loader} />
      ) : (
        <View style={styles.buttons}>
          <TouchableOpacity
            style={[styles.btn, styles.google]}
            onPress={() => signIn(googleFlow)}
          >
            <Text style={styles.btnText}>Continue with Google</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.btn, styles.apple]}
            onPress={() => signIn(appleFlow)}
          >
            <Text style={[styles.btnText, styles.appleText]}>Continue with Apple</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F9F5F1",
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
  },
  logo: { fontSize: 64 },
  title: { fontSize: 34, fontWeight: "900", color: "#FF6B35", marginTop: 12 },
  sub: { fontSize: 16, color: "#888", textAlign: "center", marginTop: 8, marginBottom: 40 },
  loader: { marginTop: 24 },
  buttons: { width: "100%", gap: 14 },
  btn: {
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
  },
  google: { backgroundColor: "#FF6B35" },
  apple: { backgroundColor: "#1a1a1a" },
  btnText: { color: "#fff", fontWeight: "700", fontSize: 16 },
  appleText: { color: "#fff" },
});
