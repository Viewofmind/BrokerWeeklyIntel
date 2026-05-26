import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { BrokerReport } from "@/lib/mock-data";

const PARAMS = [
  { key: "engagement", label: "Engagement" },
  { key: "sentiment", label: "Sentiment" },
  { key: "new_feature_response", label: "Features" },
  { key: "technical_reliability", label: "Reliability" },
  { key: "support", label: "Support" },
  { key: "transparency", label: "Transparency" },
  { key: "historical_trend", label: "Trend" },
] as const;

const COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)"];

export function BrokerRadar({ brokers }: { brokers: BrokerReport[] }) {
  const top = [...brokers].sort((a, b) => b.overall_rating - a.overall_rating).slice(0, 4);
  const data = PARAMS.map((p) => {
    const row: Record<string, string | number> = { parameter: p.label };
    top.forEach((b) => {
      row[b.broker] = b.rating_breakdown[p.key];
    });
    return row;
  });
  return (
    <Card>
      <CardHeader>
        <CardTitle>7-Parameter Comparison</CardTitle>
        <p className="text-xs text-muted-foreground">Top 4 brokers across rating dimensions</p>
      </CardHeader>
      <CardContent>
        <div className="h-[340px]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={data}>
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis dataKey="parameter" tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
              <PolarRadiusAxis angle={90} domain={[0, 10]} tick={{ fontSize: 10 }} />
              {top.map((b, i) => (
                <Radar
                  key={b.slug}
                  name={b.broker}
                  dataKey={b.broker}
                  stroke={COLORS[i]}
                  fill={COLORS[i]}
                  fillOpacity={0.15}
                />
              ))}
              <Tooltip
                contentStyle={{
                  background: "var(--popover)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius)",
                  fontSize: 12,
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
