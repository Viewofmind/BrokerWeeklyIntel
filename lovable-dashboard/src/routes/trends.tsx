import { createFileRoute } from "@tanstack/react-router";
import { DashboardHeader } from "@/components/dashboard/header";
import { useWeek } from "@/hooks/use-week";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { WEEKLY_REPORTS } from "@/lib/mock-data";
import {
  Line,
  LineChart,
  CartesianGrid,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { TrendIndicator } from "@/components/dashboard/shared";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export const Route = createFileRoute("/trends")({
  component: TrendsPage,
});

const COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "oklch(0.6 0.2 320)",
];

function TrendsPage() {
  const { week, setWeek, report } = useWeek();
  const brokers = report.brokers.map((b) => b.broker);

  const series = WEEKLY_REPORTS.map((w) => {
    const row: Record<string, string | number> = { week: w.week };
    w.brokers.forEach((b) => {
      row[b.broker] = b.overall_rating;
    });
    return row;
  });

  const lastTwo = WEEKLY_REPORTS.slice(-2);
  const changes =
    lastTwo.length === 2
      ? lastTwo[1].brokers.map((b) => {
          const prev = lastTwo[0].brokers.find((p) => p.slug === b.slug);
          return {
            broker: b.broker,
            current: b.overall_rating,
            prev: prev?.overall_rating ?? 0,
            delta: +(b.overall_rating - (prev?.overall_rating ?? 0)).toFixed(1),
            trend: b.trend,
          };
        })
      : [];

  const improver = [...changes].sort((a, b) => b.delta - a.delta)[0];
  const decliner = [...changes].sort((a, b) => a.delta - b.delta)[0];

  return (
    <>
      <DashboardHeader week={week} onWeekChange={setWeek} />
      <main className="space-y-6 p-4 md:p-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Trends & History</h1>
          <p className="text-sm text-muted-foreground">
            Week-over-week rating movement across all tracked brokers
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {improver && (
            <Card className="border-success/30 bg-success/5">
              <CardContent className="p-5">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Most Improved</p>
                <p className="mt-1 text-2xl font-semibold">{improver.broker}</p>
                <div className="mt-2"><TrendIndicator trend="Improving" delta={improver.delta} /></div>
              </CardContent>
            </Card>
          )}
          {decliner && (
            <Card className="border-destructive/30 bg-destructive/5">
              <CardContent className="p-5">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Biggest Decliner</p>
                <p className="mt-1 text-2xl font-semibold">{decliner.broker}</p>
                <div className="mt-2"><TrendIndicator trend="Declining" delta={decliner.delta} /></div>
              </CardContent>
            </Card>
          )}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Overall Rating — Last {WEEKLY_REPORTS.length} Weeks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[360px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={series}>
                  <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
                  <XAxis dataKey="week" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
                  <YAxis domain={[0, 10]} tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--popover)",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius)",
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  {brokers.map((b, i) => (
                    <Line
                      key={b}
                      type="monotone"
                      dataKey={b}
                      stroke={COLORS[i % COLORS.length]}
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Week-over-Week Changes</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Broker</TableHead>
                  <TableHead className="text-right">Previous</TableHead>
                  <TableHead className="text-right">Current</TableHead>
                  <TableHead className="text-right">Δ</TableHead>
                  <TableHead>Trend</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {changes.map((c) => (
                  <TableRow key={c.broker}>
                    <TableCell className="font-medium">{c.broker}</TableCell>
                    <TableCell className="text-right tabular-nums">{c.prev.toFixed(1)}</TableCell>
                    <TableCell className="text-right tabular-nums font-semibold">
                      {c.current.toFixed(1)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {c.delta > 0 ? "+" : ""}
                      {c.delta.toFixed(1)}
                    </TableCell>
                    <TableCell>
                      <TrendIndicator trend={c.trend} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
    </>
  );
}
