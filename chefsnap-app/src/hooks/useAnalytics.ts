/**
 * useAnalytics — lightweight event tracking via Sentry breadcrumbs.
 *
 * Events map directly to the plan.md §10 success KPIs:
 *   session_start        → activation (% installs completing first scan within 24h)
 *   scan_complete        → activation funnel
 *   ingredients_confirmed → funnel step
 *   recipes_viewed       → relevance (target: 60% of sessions reach this)
 *   recipe_detail_opened → relevance confirmed
 *   feedback_submitted   → beta quality signal
 *
 * For production, swap the Sentry breadcrumb implementation for Amplitude,
 * Mixpanel, or PostHog by changing only this file.
 */

import * as Sentry from "@sentry/react-native";

export type AnalyticsEvent =
  | "session_start"
  | "scan_initiated"
  | "scan_complete"
  | "ingredients_confirmed"
  | "recipes_viewed"
  | "recipe_detail_opened"
  | "feedback_submitted"
  | "sign_in"
  | "sign_out";

export interface EventData {
  [key: string]: string | number | boolean | undefined;
}

export function trackEvent(event: AnalyticsEvent, data?: EventData): void {
  Sentry.addBreadcrumb({
    category: "analytics",
    message: event,
    data,
    level: "info",
  });

  // Console in dev so breadcrumbs are visible without a Sentry project
  if (__DEV__) {
    console.log(`[analytics] ${event}`, data ?? "");
  }
}
