import { createFileRoute } from "@tanstack/react-router";
import { DashboardHeader } from "@/components/dashboard/header";
import { useWeek } from "@/hooks/use-week";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Globe, Twitter, MessageCircle, Flame } from "lucide-react";

export const Route = createFileRoute("/sources")({
  component: SourcesPage,
});

const SOURCES = [
  { name: "Web Blogs", icon: Globe, last: "12 minutes ago", items: 248, status: "Healthy" },
  { name: "X / Twitter", icon: Twitter, last: "3 minutes ago", items: 1842, status: "Healthy" },
  { name: "Reddit (Apify)", icon: MessageCircle, last: "8 minutes ago", items: 612, status: "Healthy" },
  { name: "Firecrawl Extraction", icon: Flame, last: "27 minutes ago", items: 96, status: "Degraded" },
];

function SourcesPage() {
  const { week, setWeek } = useWeek();
  return (
    <>
      <DashboardHeader week={week} onWeekChange={setWeek} />
      <main className="space-y-6 p-4 md:p-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Data Sources</h1>
          <p className="text-sm text-muted-foreground">
            Pipeline health, last refresh, and item counts for each ingestion source
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {SOURCES.map((s) => (
            <Card key={s.name}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <s.icon className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="font-semibold">{s.name}</h3>
                      <p className="text-xs text-muted-foreground">Last refresh {s.last}</p>
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      s.status === "Healthy"
                        ? "bg-success/15 text-success border-success/30"
                        : "bg-warning/20 border-warning/40"
                    }
                  >
                    {s.status}
                  </Badge>
                </div>
                <div className="mt-4 flex items-baseline gap-2">
                  <span className="text-3xl font-semibold tabular-nums">
                    {s.items.toLocaleString()}
                  </span>
                  <span className="text-xs text-muted-foreground">items this week</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </>
  );
}
