import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { TrendIndicator } from "./shared";
import type { BrokerReport } from "@/lib/mock-data";
import { ChevronRight } from "lucide-react";

export function Leaderboard({
  brokers,
  onSelect,
}: {
  brokers: BrokerReport[];
  onSelect: (slug: string) => void;
}) {
  const sorted = [...brokers].sort((a, b) => b.overall_rating - a.overall_rating);
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Broker Leaderboard</CardTitle>
        <span className="text-xs text-muted-foreground">Ranked by overall weekly rating</span>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">#</TableHead>
              <TableHead>Broker</TableHead>
              <TableHead className="text-center">Rating</TableHead>
              <TableHead>Trend</TableHead>
              <TableHead className="hidden md:table-cell">Engagement</TableHead>
              <TableHead className="hidden md:table-cell">Sentiment</TableHead>
              <TableHead className="hidden lg:table-cell">Reliability</TableHead>
              <TableHead className="hidden lg:table-cell">Support</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((b, i) => {
              const delta = b.previous_rating ? +(b.overall_rating - b.previous_rating).toFixed(1) : 0;
              return (
                <TableRow
                  key={b.slug}
                  className="cursor-pointer"
                  onClick={() => onSelect(b.slug)}
                >
                  <TableCell className="font-mono text-muted-foreground">
                    {String(i + 1).padStart(2, "0")}
                  </TableCell>
                  <TableCell className="font-medium">{b.broker}</TableCell>
                  <TableCell className="text-center">
                    <span className="text-2xl font-semibold tabular-nums">
                      {b.overall_rating.toFixed(1)}
                    </span>
                    <span className="text-xs text-muted-foreground">/10</span>
                  </TableCell>
                  <TableCell>
                    <TrendIndicator trend={b.trend} delta={delta} />
                  </TableCell>
                  <TableCell className="hidden md:table-cell tabular-nums text-sm">
                    {b.rating_breakdown.engagement.toFixed(1)}
                  </TableCell>
                  <TableCell className="hidden md:table-cell tabular-nums text-sm">
                    {b.rating_breakdown.sentiment.toFixed(1)}
                  </TableCell>
                  <TableCell className="hidden lg:table-cell tabular-nums text-sm">
                    {b.rating_breakdown.technical_reliability.toFixed(1)}
                  </TableCell>
                  <TableCell className="hidden lg:table-cell tabular-nums text-sm">
                    {b.rating_breakdown.support.toFixed(1)}
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon" className="h-7 w-7">
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
