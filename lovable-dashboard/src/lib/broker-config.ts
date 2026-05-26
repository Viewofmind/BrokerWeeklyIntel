// Broker Configuration - Supports dynamic adding of brokers
// This allows users to track new brokers without hardcoding.

export interface TrackedBroker {
  name: string;
  slug: string;
}

const DEFAULT_BROKERS: TrackedBroker[] = [
  { name: "Zerodha", slug: "zerodha" },
  { name: "Groww", slug: "groww" },
  { name: "Angel One", slug: "angel-one" },
  { name: "Upstox", slug: "upstox" },
  { name: "Fyers", slug: "fyers" },
  { name: "ICICI Direct", slug: "icici-direct" },
  { name: "Sahi Broking", slug: "sahi-broking" },
];

// Runtime list of tracked brokers (can be extended at runtime)
let trackedBrokers: TrackedBroker[] = [...DEFAULT_BROKERS];

export function getTrackedBrokers(): TrackedBroker[] {
  return [...trackedBrokers];
}

export function addTrackedBroker(name: string): { success: boolean; message: string; broker?: TrackedBroker } {
  const trimmedName = name.trim();
  if (!trimmedName) {
    return { success: false, message: "Broker name cannot be empty" };
  }

  const slug = trimmedName.toLowerCase().replace(/\s+/g, "-");

  // Check if already exists
  const exists = trackedBrokers.some(b => b.slug === slug);
  if (exists) {
    return { success: false, message: `${trimmedName} is already being tracked` };
  }

  const newBroker: TrackedBroker = { name: trimmedName, slug };
  trackedBrokers.push(newBroker);

  return {
    success: true,
    message: `Added ${trimmedName} to tracking list`,
    broker: newBroker,
  };
}

export function removeTrackedBroker(slug: string): boolean {
  const initialLength = trackedBrokers.length;
  trackedBrokers = trackedBrokers.filter(b => b.slug !== slug);
  return trackedBrokers.length < initialLength;
}

// Helper to get just the names (for backward compatibility with mock-data)
export function getBrokerNames(): string[] {
  return trackedBrokers.map(b => b.name);
}

// Reset to defaults (useful for testing)
export function resetToDefaultBrokers() {
  trackedBrokers = [...DEFAULT_BROKERS];
}
