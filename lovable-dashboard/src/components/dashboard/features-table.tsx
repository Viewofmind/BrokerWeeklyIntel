import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExternalLink, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import type { BrokerReport } from "@/lib/mock-data";

const reactionColor = (r: string) =>
  r === "Positive"
    ? "bg-success/15 text-success border-success/30"
    : r === "Negative"
      ? "bg-destructive/15 text-destructive border-destructive/30"
      : r === "Mixed"
        ? "bg-warning/20 border-warning/40 dark:text-warning"
        : "bg-muted text-muted-foreground";

export function FeaturesTable({
  brokers,
  title = "New Features Launched This Week",
  subtitle,
}: {
  brokers: BrokerReport[];
  title?: string;
  subtitle?: string;
}) {
  const rows = brokers.flatMap((b) =>
    b.new_features.map((f) => ({ broker: b.broker, ...f })),
  );
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="h-4 w-4 text-primary" />
            {title}
          </CardTitle>
          {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
        </div>
        <Badge variant="outline" className="font-mono text-[10px]">
          {rows.length} entries
        </Badge>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Broker</TableHead>
              <TableHead>Feature / Update</TableHead>
              <TableHead>Approx. Launch</TableHead>
              <TableHead>User Reaction</TableHead>
              <TableHead>Discussion</TableHead>
              <TableHead>Key Evidence / Link</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((f, i) => (
              <TableRow key={f.broker + f.feature_name + i}>
                <TableCell className="font-medium whitespace-nowrap">{f.broker}</TableCell>
                <TableCell>{f.feature_name}</TableCell>
                <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                  {f.launch_date}
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={cn(reactionColor(f.user_reaction))}>
                    {f.user_reaction}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">{f.discussion_volume}</Badge>
                </TableCell>
                <TableCell>
                  {f.evidence_links[0] ? (
                    <a
                      href={f.evidence_links[0]}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                    >
                      Source <ExternalLink className="h-3 w-3" />
                    </a>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
