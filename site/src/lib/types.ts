export type Prediction = {
  p_a: number;
  p_b: number;
  confidence: "Low" | "Medium" | "High" | string;
  edge_a: number | null;
  edge_b: number | null;
};

export type Odds = {
  book: string;
  odds_a_american: number;
  odds_b_american: number;
  odds_timestamp_utc: string;
};

export type Outcome = {
  winner: "A" | "B" | string;
  method: string | null;
  recorded_timestamp_utc: string | null;
};

export type Bout = {
  bout_id: string;
  bout_order: number;
  weight_class_lbs: number | null;
  fighter_a: string;
  fighter_b: string;
  prediction: Prediction | null;
  odds: Odds | null;
  outcome: Outcome | null;
};

export type Event = {
  event_id: string;
  slug: string;
  event_name: string;
  event_date_utc: string;
  location: string | null;
  bouts: Bout[];
};

export type EventsPayload = { events: Event[] };
