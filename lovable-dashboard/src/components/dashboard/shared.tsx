import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { ArrowDown, ArrowRight, ArrowUp } from "lucide-react";
import type { Severity, Trend, Platform } from "@/lib/mock-data";

export function SeverityBadge({ severity }: { severity: Severity }) {
  const map: Record<Severity, string> = {
    critical: "bg-destructive/15 text-destructive border-destructive/30",
    high: "bg-warning/20 text-warning-foreground border-warning/40 dark:text-warning",
    medium: "bg-amber-500/15 text-amber-700 border-amber-500/30 dark:text-amber-300",
    low: "bg-muted text-muted-foreground border-border",
  };
  return (
    <Badge variant="outline" className={cn("capitalize font-medium", map[severity])}>
      {severity}
    </Badge>
  );
}

export function TrendIndicator({
  trend,
  delta,
  compact = false,
}: {
  trend: Trend;
  delta?: number;
  compact?: boolean;
}) {
  const map = {
    Improving: {
      icon: ArrowUp,
      cls: "text-success bg-success/10 border-success/20",
    },
    Declining: {
      icon: ArrowDown,
      cls: "text-destructive bg-destructive/10 border-destructive/20",
    },
    Stable: {
      icon: ArrowRight,
      cls: "text-muted-foreground bg-muted border-border",
    },
  } as const;
  const { icon: Icon, cls } = map[trend];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium",
        cls,
      )}
    >
      <Icon className="h-3 w-3" />
      {compact ? null : trend}
      {typeof delta === "number" && delta !== 0 && (
        <span className="tabular-nums">
          {delta > 0 ? "+" : ""}
          {delta.toFixed(1)}
        </span>
      )}
    </span>
  );
}

export function PlatformBadge({ platform }: { platform: Platform }) {
  const label = platform === "x" ? "X" : platform === "reddit" ? "Reddit" : "Web";
  const cls =
    platform === "x"
      ? "bg-foreground text-background"
      : platform === "reddit"
        ? "bg-orange-500/15 text-orange-600 dark:text-orange-300 border-orange-500/30"
        : "bg-info/15 text-info border-info/30";
  return (
    <Badge variant="outline" className={cn("text-[10px] tracking-wide", cls)}>
      {label}
    </Badge>
  );
}

export function SentimentDot({ sentiment }: { sentiment: "positive" | "negative" | "neutral" | "mixed" }) {
  const color =
    sentiment === "positive"
      ? "bg-success"
      : sentiment === "negative"
        ? "bg-destructive"
        : sentiment === "mixed"
          ? "bg-warning"
          : "bg-muted-foreground";
  return <span className={cn("inline-block h-2 w-2 rounded-full", color)} />;
}
