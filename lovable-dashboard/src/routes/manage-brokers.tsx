import { createFileRoute } from "@tanstack/react-router";
import { DashboardHeader } from "@/components/dashboard/header";
import { useWeek } from "@/hooks/use-week";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { getTrackedBrokers, addTrackedBroker, removeTrackedBroker } from "@/lib/broker-config";
import { WEEKLY_REPORTS, getNormalizedReports } from "@/lib/mock-data";
import { useState } from "react";
import { UserPlus, Copy, Trash2, AlertCircle } from "lucide-react";

export const Route = createFileRoute("/manage-brokers")({
  component: ManageBrokersPage,
});

function ManageBrokersPage() {
  const { week, setWeek } = useWeek();
  const [brokers, setBrokers] = useState(getTrackedBrokers());
  const [newBrokerName, setNewBrokerName] = useState("");
  const [startingRating, setStartingRating] = useState("6.8");
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const handleAddBroker = () => {
    const name = newBrokerName.trim();
    
    if (!name) {
      setMessage({ text: "Broker name cannot be empty.", type: "error" });
      setTimeout(() => setMessage(null), 3000);
      return;
    }

    const result = addTrackedBroker(name);
    
    if (result.success) {
      setBrokers(getTrackedBrokers());
      setNewBrokerName("");
      setMessage({ text: result.message, type: "success" });
    } else {
      setMessage({ text: result.message, type: "error" });
    }

    setTimeout(() => setMessage(null), 4000);
  };

  const handleRemoveBroker = (slug: string, name: string) => {
    if (brokers.length <= 1) {
      setMessage({ text: "You must keep at least one broker tracked.", type: "error" });
      return;
    }

    const success = removeTrackedBroker(slug);
    if (success) {
      setBrokers(getTrackedBrokers());
      setMessage({ text: `Removed ${name}`, type: "success" });
    }
    setTimeout(() => setMessage(null), 3000);
  };

  // Generate the code that will be copied (used for both preview and copy)
  const getGeneratedCode = () => {
    const currentBrokers = getTrackedBrokers();
    
    const brokerListCode = currentBrokers
      .map(b => `  { name: "${b.name}", slug: "${b.slug}" },`)
      .join("\n");

    const latestBroker = currentBrokers[currentBrokers.length - 1];
    const rating = parseFloat(startingRating) || 6.8;

    const sampleEntry = `{
  broker: "${latestBroker?.name || 'New Broker'}",
  slug: "${latestBroker?.slug || 'new-broker'}",
  overall_rating: ${rating},
  trend: "Stable",
  rating_breakdown: {
    engagement: ${rating},
    sentiment: ${rating},
    new_feature_response: ${rating},
    technical_reliability: ${rating},
    support: ${rating},
    transparency: ${rating},
    historical_trend: ${rating},
  },
  new_features: [],
  key_quotes: [
    { 
      broker: "${latestBroker?.name || 'New Broker'}", 
      quote: "Solid platform with good execution.", 
      context: "Initial feedback after adding to tracking", 
      sentiment: "positive", 
      source_url: "https://x.com", 
      author: "Trader", 
      platform: "x", 
      sentimentScore: 0.52 
    }
  ],
  negative_themes: [],
  technical_issues: [],
  watch_items: [],
}`;

    return `// STEP 1: Update src/lib/broker-config.ts
// Replace the DEFAULT_BROKERS array:
const DEFAULT_BROKERS: TrackedBroker[] = [
${brokerListCode}
];

// STEP 2: Add this entry to the 'brokers' array
// inside the latest week object in mock-data.ts:
${sampleEntry}

// After updating, commit and push to GitHub.`;
  };

  const generateGitHubCode = () => {
    const code = getGeneratedCode();

    navigator.clipboard.writeText(code).then(() => {
      setMessage({ 
        text: "✅ Complete update copied! Paste into broker-config.ts + latest week in mock-data.ts, then commit.", 
        type: "success" 
      });
    }).catch(() => {
      console.log("=== FULL CODE UPDATE FOR GITHUB ===\n" + code);
      setMessage({ 
        text: "Code logged to console. Copy from there.", 
        type: "success" 
      });
    });

    setTimeout(() => setMessage(null), 8000);
  };

  return (
    <>
      <DashboardHeader week={week} onWeekChange={setWeek} />
      <main className="space-y-6 p-4 md:p-6 max-w-4xl">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-3">
            <UserPlus className="h-6 w-6" />
            Manage Tracked Brokers
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Add or remove brokers from tracking. Changes here affect the current session only.
          </p>
        </div>

        {/* Add New Broker */}
        <Card>
          <CardHeader>
            <CardTitle>Add New Broker</CardTitle>
            <CardDescription>
              Add a new broker to track across all historical weeks. This will appear in Overview, Quotes, Trends, etc.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="md:col-span-2">
                <Input
                  placeholder="Broker name (e.g. 5Paisa, Kotak Securities)"
                  value={newBrokerName}
                  onChange={(e) => setNewBrokerName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddBroker()}
                />
              </div>
              <div className="flex gap-2">
                <Input
                  type="number"
                  step="0.1"
                  min="5"
                  max="9.5"
                  value={startingRating}
                  onChange={(e) => setStartingRating(e.target.value)}
                  className="w-24"
                  title="Starting rating (used for code generation)"
                />
                <Button onClick={handleAddBroker} disabled={!newBrokerName.trim()} className="flex-1">
                  <UserPlus className="h-4 w-4 mr-2" />
                  Add
                </Button>
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-1.5">
              The new broker will be automatically added to all {WEEKLY_REPORTS.length} historical weeks.
              Starting Rating is used when generating code for GitHub.
            </p>

            {message && (
              <div className={`mt-3 text-sm p-3 rounded-md flex items-center gap-2 ${
                message.type === "success" 
                  ? "bg-green-50 text-green-700 border border-green-200" 
                  : "bg-red-50 text-red-700 border border-red-200"
              }`}>
                <AlertCircle className="h-4 w-4" />
                {message.text}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Current Tracked Brokers */}
        <Card>
          <CardHeader>
            <CardTitle>Currently Tracked Brokers ({brokers.length})</CardTitle>
            <CardDescription>
              These brokers appear in all weekly reports. Removing a broker only affects the current session.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {brokers.map((broker) => (
                <div 
                  key={broker.slug} 
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50"
                >
                  <div>
                    <div className="font-medium">{broker.name}</div>
                    <div className="text-xs text-muted-foreground">/{broker.slug}</div>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => handleRemoveBroker(broker.slug, broker.name)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    Remove
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* GitHub Update Section */}
        <Card className="border-2 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Copy className="h-5 w-5" />
              Update GitHub Code
            </CardTitle>
            <CardDescription>
              When you're happy with the list of brokers, copy the code below and commit it to keep the changes permanently.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-muted p-4 rounded-lg text-sm">
              <div className="font-medium mb-2">How to persist to GitHub:</div>
              <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                <li>Click the button to copy the updated <code>DEFAULT_BROKERS</code> array</li>
                <li>Open <code className="bg-background px-1 rounded">src/lib/broker-config.ts</code></li>
                <li>Replace the existing <code className="bg-background px-1 rounded">DEFAULT_BROKERS</code> array</li>
                <li>Commit and push to GitHub</li>
              </ol>
            </div>

            {/* Live Code Preview */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Code Preview (what will be copied)</span>
                <span className="text-xs text-muted-foreground">Updates live as you add brokers</span>
              </div>
              <pre className="bg-zinc-950 text-zinc-200 p-4 rounded-lg text-xs overflow-auto max-h-[280px] font-mono border">
                {getGeneratedCode()}
              </pre>
            </div>

            <Button 
              onClick={generateGitHubCode} 
              className="w-full"
              size="lg"
              variant="default"
            >
              <Copy className="h-4 w-4 mr-2" />
              Copy Code Above to Clipboard
            </Button>

            <p className="text-xs text-muted-foreground text-center">
              The app already handles adding the new broker to all historical weeks at runtime.
            </p>
          </CardContent>
        </Card>
      </main>
    </>
  );
}
