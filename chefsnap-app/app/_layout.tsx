import React, { useEffect } from "react";
import { TouchableOpacity, Text } from "react-native";
import { Stack, useRouter, useSegments } from "expo-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StatusBar } from "expo-status-bar";
import { ClerkProvider, useAuth } from "@clerk/clerk-expo";
import * as SecureStore from "expo-secure-store";
import * as Sentry from "@sentry/react-native";
import { setTokenProvider } from "../src/api/client";
import { trackEvent } from "../src/hooks/useAnalytics";

// ── Sentry ───────────────────────────────────────────────────────────────────
const SENTRY_DSN = process.env.EXPO_PUBLIC_SENTRY_DSN ?? "";
if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    tracesSampleRate: 0.2,
    attachScreenshot: true,
  });
}

// ── Clerk token cache via expo-secure-store ───────────────────────────────────
const tokenCache = {
  async getToken(key: string) { return SecureStore.getItemAsync(key); },
  async saveToken(key: string, value: string) { return SecureStore.setItemAsync(key, value); },
  async clearToken(key: string) { return SecureStore.deleteItemAsync(key); },
};

const queryClient = new QueryClient();
const CLERK_KEY = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "";

// Injects the Clerk session token into every axios request.
function TokenBridge() {
  const { getToken } = useAuth();
  useEffect(() => {
    setTokenProvider(() => getToken());
  }, [getToken]);
  return null;
}

// Fires session_start once per signed-in session (plan.md §10 activation KPI).
function SessionTracker() {
  const { isSignedIn } = useAuth();
  useEffect(() => {
    if (isSignedIn) trackEvent("session_start");
  }, [isSignedIn]);
  return null;
}

// Redirects unauthenticated users to sign-in and vice-versa.
function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isSignedIn, isLoaded } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (!isLoaded) return;
    const inAuthGroup = segments[0] === "(auth)";
    if (!isSignedIn && !inAuthGroup) router.replace("/(auth)/sign-in");
    else if (isSignedIn && inAuthGroup) router.replace("/");
  }, [isSignedIn, isLoaded, segments, router]);

  return <>{children}</>;
}

function SettingsButton() {
  const router = useRouter();
  return (
    <TouchableOpacity onPress={() => router.push("/settings")} style={{ marginRight: 12 }}>
      <Text style={{ color: "#fff", fontSize: 22 }}>⚙</Text>
    </TouchableOpacity>
  );
}

export default function RootLayout() {
  return (
    <ClerkProvider publishableKey={CLERK_KEY} tokenCache={tokenCache}>
      <QueryClientProvider client={queryClient}>
        <StatusBar style="light" />
        <TokenBridge />
        <SessionTracker />
        <AuthGuard>
          <Stack
            screenOptions={{
              headerStyle: { backgroundColor: "#FF6B35" },
              headerTintColor: "#fff",
              headerTitleStyle: { fontWeight: "700" },
            }}
          >
            <Stack.Screen
              name="index"
              options={{ title: "ChefSnap", headerRight: () => <SettingsButton /> }}
            />
            <Stack.Screen name="ingredients" options={{ title: "Your Ingredients" }} />
            <Stack.Screen name="recipes" options={{ title: "Recipe Suggestions" }} />
            <Stack.Screen name="recipe/[id]" options={{ title: "Recipe" }} />
            <Stack.Screen name="settings" options={{ title: "Settings" }} />
            <Stack.Screen name="feedback" options={{ title: "Feedback" }} />
            <Stack.Screen name="(auth)/sign-in" options={{ headerShown: false }} />
          </Stack>
        </AuthGuard>
      </QueryClientProvider>
    </ClerkProvider>
  );
}
