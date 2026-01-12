export type PlanTier = "free" | "basic" | "pro";

export interface FeatureFlags {
  tier: PlanTier;

  // Visibility
  showEdgeSorting: boolean;
  showAdvancedMetrics: boolean;
  showAffiliateCTA: boolean;

  // Messaging
  showUpgradePrompt: boolean;
}

export const FEATURES: Record<PlanTier, FeatureFlags> = {
  free: {
    tier: "free",
    showEdgeSorting: false,
    showAdvancedMetrics: false,
    showAffiliateCTA: false,
    showUpgradePrompt: true,
  },

  basic: {
    tier: "basic",
    showEdgeSorting: false,
    showAdvancedMetrics: true,
    showAffiliateCTA: false,
    showUpgradePrompt: true,
  },

  pro: {
    tier: "pro",
    showEdgeSorting: true,
    showAdvancedMetrics: true,
    showAffiliateCTA: true,
    showUpgradePrompt: false,
  },
};
