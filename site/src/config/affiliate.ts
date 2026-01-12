export type SportsbookKey = "fanduel" | "draftkings";

export interface AffiliateConfig {
  enabled: boolean;
  sportsbook: SportsbookKey;
  label: string;
  url: string;
}

export const affiliateConfig: AffiliateConfig = {
  enabled: false, // <-- DO NOT CHANGE YET
  sportsbook: "fanduel",
  label: "View this market on FanDuel",
  url: "", // will be filled after approval
};
