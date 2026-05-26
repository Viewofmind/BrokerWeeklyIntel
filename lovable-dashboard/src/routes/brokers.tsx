import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { DashboardHeader } from "@/components/dashboard/header";
import { useWeek } from "@/hooks/use-week";
import { Card, CardContent } from "@/components/ui/card";
import { TrendIndicator } from "@/components/dashboard/shared";
import { BrokerDetailSheet } from "@/components/dashboard/broker-detail";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/brokers")({
  component: BrokersPage,
});

function BrokersPage() {
  const { week, setWeek, report } = useWeek();
  const [selected, setSelected] = useState<string | null>(null);
  const broker = report.brokers.find((b) => b.slug === selected) ?? null;

  return (
    <>
      <DashboardHeader week={week} onWeekChange={setWeek} />
      <main className="space-y-6 p-4 md:p-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Brokers</h1>
          <p className="text-sm text-muted-foreground">
            Detailed weekly report cards for each tracked broker
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {report.brokers.map((b) => {
            const delta = b.previous_rating
              ? +(b.overall_rating - b.previous_rating).toFixed(1)
              : 0;
            return (
              <Card key={b.slug} className="overflow-hidden">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-lg">{b.broker}</h3>
                      <TrendIndicator trend={b.trend} delta={delta} />
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-semibold tabular-nums">
                        {b.overall_rating.toFixed(1)}
                      </div>
                      <div className="text-[10px] text-muted-foreground">/ 10</div>
                    </div>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs">
                    {Object.entries(b.rating_breakdown).slice(0, 6).map(([k, v]) => (
                      <div key={k} className="flex items-center justify-between">
                        <span className="text-muted-foreground capitalize">
                          {k.replace(/_/g, " ")}
                        </span>
                        <span className="font-mono tabular-nums">{v.toFixed(1)}</span>
                      </div>
                    ))}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-4 w-full"
                    onClick={() => setSelected(b.slug)}
                  >
                    View details
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </main>
      <BrokerDetailSheet
        broker={broker}
        open={!!broker}
        onOpenChange={(o) => !o && setSelected(null)}
      />
    </>
  );
}
