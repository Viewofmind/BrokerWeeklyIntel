import { createFileRoute } from "@tanstack/react-router";
import { DashboardHeader } from "@/components/dashboard/header";
import { useWeek } from "@/hooks/use-week";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { SeverityBadge } from "@/components/dashboard/shared";
import { AlertOctagon, Layers, Wrench } from "lucide-react";

export const Route = createFileRoute("/issues")({
  component: IssuesPage,
});

function IssuesPage() {
  const { week, setWeek, report } = useWeek();
  const all = report.brokers.flatMap((b) =>
    b.technical_issues.map((i) => ({ ...i, broker: b.broker })),
  );
  const critical = all.filter((i) => i.severity === "critical").length;
  const platformWide = all.filter((i) => i.issue_type === "platform_wide").length;
  const featureSpecific = all.filter((i) => i.issue_type === "feature_specific").length;

  return (
    <>
      <DashboardHeader week={week} onWeekChange={setWeek} />
      <main className="space-y-6 p-4 md:p-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Technical Issues</h1>
          <p className="text-sm text-muted-foreground">
            Platform reliability incidents and reported glitches this week
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="p-5 flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-destructive/15 text-destructive">
                <AlertOctagon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Critical</p>
                <p className="text-2xl font-semibold tabular-nums">{critical}</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5 flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-warning/20 text-warning-foreground dark:text-warning">
                <Layers className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Platform-wide</p>
                <p className="text-2xl font-semibold tabular-nums">{platformWide}</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5 flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-info/15 text-info">
                <Wrench className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Feature-specific</p>
                <p className="text-2xl font-semibold tabular-nums">{featureSpecific}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>All issues</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Broker</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Volume</TableHead>
                  <TableHead>First Seen</TableHead>
                  <TableHead>Last Seen</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {all
                  .sort((a, b) => b.volume - a.volume)
                  .map((i, idx) => (
                    <TableRow key={i.broker + i.description + idx}>
                      <TableCell className="font-medium">{i.broker}</TableCell>
                      <TableCell>{i.description}</TableCell>
                      <TableCell><SeverityBadge severity={i.severity} /></TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {i.issue_type.replace("_", " ")}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{i.volume}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{i.first_seen}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{i.last_seen}</TableCell>
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
