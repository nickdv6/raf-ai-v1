export type BillingInterval = "monthly" | "annual";
export type PlanTier = "free" | "basic" | "pro";

export interface PlanDefinition {
  tier: PlanTier;
  name: string;
  monthlyPrice: number;
  annualPrice: number;
  annualNote?: string;
  description: string;
}

export const PLANS: Record<PlanTier, PlanDefinition> = {
  free: {
    tier: "free",
    name: "Free",
    monthlyPrice: 0,
    annualPrice: 0,
    description: "Public access to core event pages and highlights."
  },

  basic: {
    tier: "basic",
    name: "Forge Basic",
    monthlyPrice: 19,
    annualPrice: 190,
    annualNote: "2 months free annually",
    description: "Deeper context and historical access."
  },

  pro: {
    tier: "pro",
    name: "Forge Pro",
    monthlyPrice: 29,
    annualPrice: 290,
    annualNote: "2 months free annually",
    description: "Full tooling, filters, alerts, and affiliate access."
  }
};
