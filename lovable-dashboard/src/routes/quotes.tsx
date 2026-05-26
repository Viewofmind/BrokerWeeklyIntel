import { createFileRoute } from "@tanstack/react-router";
import { DashboardHeader } from "@/components/dashboard/header";
import { useWeek } from "@/hooks/use-week";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PlatformBadge, SentimentDot } from "@/components/dashboard/shared";
import { ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/quotes")({
  component: QuotesPage,
});

function QuotesPage() {
  const { week, setWeek, report } = useWeek();
  const all = report.brokers.flatMap((b) =>
    b.key_quotes.map((q) => ({ ...q, broker: b.broker })),
  );
  const positive = all.filter((q) => q.sentiment === "positive");
  const negative = all.filter((q) => q.sentiment === "negative");
  const themes = report.brokers.flatMap((b) => b.negative_themes);
  const themeCounts = themes.reduce<Record<string, number>>((acc, t) => {
    acc[t.theme] = (acc[t.theme] ?? 0) + t.count;
    return acc;
  }, {});
  const sortedThemes = Object.entries(themeCounts).sort((a, b) => b[1] - a[1]);
  const maxCount = sortedThemes[0]?.[1] ?? 1;

  return (
    <>
      <DashboardHeader week={week} onWeekChange={setWeek} />
      <main className="space-y-6 p-4 md:p-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Sentiment & Quotes</h1>
          <p className="text-sm text-muted-foreground">
            Aggregated investor voice this week — best and worst of what's being said
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <SentimentTile label="Positive" count={positive.length} sentiment="positive" />
          <SentimentTile label="Negative" count={negative.length} sentiment="negative" />
          <SentimentTile label="Neutral / Mixed" count={all.length - positive.length - negative.length} sentiment="mixed" />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Best of the week</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {positive.slice(0, 8).map((q, i) => (
                <QuoteCard key={`${q.quote}-${i}`} q={q} />
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Worst of the week</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {negative.slice(0, 8).map((q, i) => (
                <QuoteCard key={`${q.quote}-${i}`} q={q} />
              ))}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Theme volume across brokers</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {sortedThemes.map(([theme, count]) => (
              <div key={theme}>
                <div className="flex justify-between text-sm mb-1">
                  <span>{theme}</span>
                  <span className="font-mono tabular-nums text-muted-foreground">{count}</span>
                </div>
                <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full bg-primary"
                    style={{ width: `${(count / maxCount) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </main>
    </>
  );
}

function SentimentTile({
  label,
  count,
  sentiment,
}: {
  label: string;
  count: number;
  sentiment: "positive" | "negative" | "mixed";
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
          <SentimentDot sentiment={sentiment} />
          {label}
        </div>
        <p className="mt-2 text-3xl font-semibold tabular-nums">{count}</p>
      </CardContent>
    </Card>
  );
}

function QuoteCard({
  q,
}: {
  q: {
    quote: string;
    context: string;
    sentiment: "positive" | "negative" | "neutral";
    source_url: string;
    author?: string;
    platform: "x" | "reddit" | "web" | "linkedin" | "youtube" | "discord" | "instagram" | "other";
    broker: string;
    sentimentScore?: number;
  };
}) {
  const score = q.sentimentScore;
  const scoreColor = score == null ? "" : score >= 0.5 ? "bg-emerald-500/15 text-emerald-600 border-emerald-500/30" : score <= -0.5 ? "bg-rose-500/15 text-rose-600 border-rose-500/30" : score > 0 ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20" : "bg-rose-500/10 text-rose-600 border-rose-500/20";
  return (
    <div className="rounded-md border bg-card p-3">
      <div className="flex items-center justify-between mb-2 gap-2">
        <div className="flex items-center gap-2">
          <Badge variant="outline">{q.broker}</Badge>
          <PlatformBadge platform={q.platform} />
          {score != null && (
            <Badge variant="outline" className={`font-mono tabular-nums text-[10px] px-1.5 py-0 ${scoreColor}`}>
              {score > 0 ? "+" : ""}{score.toFixed(2)}
            </Badge>
          )}
        </div>
        <SentimentDot sentiment={q.sentiment} />
      </div>
      <p className="text-sm leading-relaxed">"{q.quote}"</p>
      <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
        <span className="truncate">{q.author} · {q.context}</span>
        <a href={q.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:text-foreground shrink-0">
          Source <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    </div>
  );
}
