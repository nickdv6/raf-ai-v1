import events from "../data/events.json";
import type { EventsPayload } from "./types";

export function loadEvents(): EventsPayload {
  return events as EventsPayload;
}

export function latestEvent(): ReturnType<typeof loadEvents>["events"][number] | null {
  const payload = loadEvents();
  return payload.events?.[0] ?? null;
}
