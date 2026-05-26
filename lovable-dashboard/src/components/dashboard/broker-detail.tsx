import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { ExternalLink } from "lucide-react";
import type { BrokerReport } from "@/lib/mock-data";
import { PlatformBadge, SentimentDot, SeverityBadge, TrendIndicator } from "./shared";

const PARAMS: Array<{ key: keyof BrokerReport["rating_breakdown"]; label: string; weight: number }> = [
  { key: "engagement", label: "Engagement", weight: 10 },
  { key: "sentiment", label: "Sentiment", weight: 20 },
  { key: "new_feature_response", label: "New Feature Response", weight: 15 },
  { key: "technical_reliability", label: "Technical Reliability", weight: 20 },
  { key: "support", label: "Support", weight: 15 },
  { key: "transparency", label: "Transparency", weight: 10 },
  { key: "historical_trend", label: "Historical Trend", weight: 10 },
];

export function BrokerDetailSheet({
  broker,
  open,
  onOpenChange,
}: {
  broker: BrokerReport | null;
  open: boolean;
  onOpenChange: (o: boolean) => void;
}) {
  if (!broker) return null;
  const delta = broker.previous_rating
    ? +(broker.overall_rating - broker.previous_rating).toFixed(1)
    : 0;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader>
          <div className="flex items-start justify-between gap-4">
            <div>
              <SheetTitle className="text-2xl">{broker.broker}</SheetTitle>
              <SheetDescription>Weekly intelligence snapshot</SheetDescription>
            </div>
            <div className="text-right">
              <div className="text-4xl font-semibold tabular-nums">
                {broker.overall_rating.toFixed(1)}
                <span className="text-sm text-muted-foreground font-normal">/10</span>
              </div>
              <div className="mt-1 flex justify-end">
                <TrendIndicator trend={broker.trend} delta={delta} />
              </div>
            </div>
          </div>
        </SheetHeader>

        <div className="space-y-6 pt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Rating Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {PARAMS.map((p) => {
                const v = broker.rating_breakdown[p.key];
                return (
                  <div key={p.key}>
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2">
                        {p.label}
                        <span className="text-[10px] text-muted-foreground">
                          weight {p.weight}%
                        </span>
                      </span>
                      <span className="font-mono tabular-nums">{v.toFixed(1)}</span>
                    </div>
                    <Progress value={v * 10} className="mt-1.5 h-1.5" />
                  </div>
                );
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">New Features</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {broker.new_features.map((f) => (
                <div
                  key={f.feature_name}
                  className="flex items-start justify-between rounded-md border bg-card p-3"
                >
                  <div>
                    <div className="font-medium text-sm">{f.feature_name}</div>
                    <div className="text-xs text-muted-foreground">
                      Launched {f.launch_date} · Volume {f.discussion_volume}
                    </div>
                  </div>
                  <Badge variant="secondary">{f.user_reaction}</Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Key Quotes</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              {broker.key_quotes.map((q) => (
                <div key={q.quote} className="rounded-md border bg-card p-3">
                  <div className="flex items-center justify-between mb-2">
                    <PlatformBadge platform={q.platform} />
                    <SentimentDot sentiment={q.sentiment} />
                  </div>
                  <p className="text-sm leading-relaxed">"{q.quote}"</p>
                  <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                    <span>{q.author}</span>
                    <a
                      href={q.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 hover:text-foreground"
                    >
                      Source <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Negative Themes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 sm:grid-cols-2">
                {broker.negative_themes.map((t) => (
                  <div
                    key={t.theme}
                    className="flex items-center justify-between rounded-md border bg-card p-3"
                  >
                    <div>
                      <div className="font-medium text-sm">{t.theme}</div>
                      <div className="text-xs text-muted-foreground">{t.count} mentions</div>
                    </div>
                    <SeverityBadge severity={t.severity} />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Technical Issues</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {broker.technical_issues.map((i) => (
                <div key={i.description} className="rounded-md border bg-card p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="text-sm font-medium">{i.description}</div>
                    <SeverityBadge severity={i.severity} />
                  </div>
                  <div className="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <Badge variant="outline">{i.issue_type.replace("_", " ")}</Badge>
                    <span>Volume: {i.volume}</span>
                    <span>
                      {i.first_seen} → {i.last_seen}
                    </span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Watch Items (Next Week)</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                {broker.watch_items.map((w) => (
                  <li key={w} className="flex gap-2">
                    <span className="text-primary mt-1.5 h-1.5 w-1.5 rounded-full bg-primary" />
                    {w}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Separator />
          <div className="flex justify-end">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Close
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
