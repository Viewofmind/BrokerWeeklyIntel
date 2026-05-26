import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { ExternalLink, Eye } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/features")({
  component: FeaturesPage,
});

function FeaturesPage() {
  const { week, setWeek, report } = useWeek();
  const [brokerFilter, setBrokerFilter] = useState("all");
  const [reactionFilter, setReactionFilter] = useState("all");

  const all = report.brokers.flatMap((b) =>
    b.new_features.map((f) => ({ ...f, broker: b.broker })),
  );
  const filtered = all.filter(
    (f) =>
      (brokerFilter === "all" || f.broker === brokerFilter) &&
      (reactionFilter === "all" || f.user_reaction === reactionFilter),
  );

  const reactionColor = (r: string) =>
    r === "Positive"
      ? "bg-success/15 text-success border-success/30"
      : r === "Negative"
        ? "bg-destructive/15 text-destructive border-destructive/30"
        : r === "Mixed"
          ? "bg-warning/20 border-warning/40"
          : "bg-muted";

  return (
    <>
      <DashboardHeader week={week} onWeekChange={setWeek} />
      <main className="space-y-6 p-4 md:p-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">New Features</h1>
          <p className="text-sm text-muted-foreground">
            All product launches and feature updates across tracked brokers this week
          </p>
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between gap-2 flex-wrap">
            <CardTitle>{filtered.length} features tracked</CardTitle>
            <div className="flex gap-2">
              <Select value={brokerFilter} onValueChange={setBrokerFilter}>
                <SelectTrigger className="h-9 w-[160px]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All brokers</SelectItem>
                  {report.brokers.map((b) => (
                    <SelectItem key={b.slug} value={b.broker}>{b.broker}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={reactionFilter} onValueChange={setReactionFilter}>
                <SelectTrigger className="h-9 w-[140px]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All reactions</SelectItem>
                  <SelectItem value="Positive">Positive</SelectItem>
                  <SelectItem value="Mixed">Mixed</SelectItem>
                  <SelectItem value="Negative">Negative</SelectItem>
                  <SelectItem value="Too early to tell">Too early</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Broker</TableHead>
                  <TableHead>Feature</TableHead>
                  <TableHead>Launch Date</TableHead>
                  <TableHead>Reaction</TableHead>
                  <TableHead>Volume</TableHead>
                  <TableHead>Evidence</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((f, i) => (
                  <TableRow key={f.broker + f.feature_name + i}>
                    <TableCell className="font-medium">{f.broker}</TableCell>
                    <TableCell>{f.feature_name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{f.launch_date}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className={reactionColor(f.user_reaction)}>
                        {f.user_reaction}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{f.discussion_volume}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {f.evidence_links.slice(0, 2).map((l, j) => (
                          <a key={j} href={l} target="_blank" rel="noreferrer" className="text-muted-foreground hover:text-foreground">
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => toast.success(`${f.feature_name} added to watch`)}>
                        <Eye className="h-4 w-4" />
                      </Button>
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
