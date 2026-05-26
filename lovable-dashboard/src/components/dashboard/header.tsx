import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { WEEKLY_REPORTS, getWeek } from "@/lib/mock-data";
import { format, parseISO } from "date-fns";
import { Download, FileText, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { downloadMarkdown, downloadPDF, downloadZIP } from "@/lib/export";
import { ZpiIcon } from "@/components/ui/zpi-icon";

export function DashboardHeader({
  week,
  onWeekChange,
}: {
  week: string;
  onWeekChange: (w: string) => void;
}) {
  const current = WEEKLY_REPORTS.find((w) => w.week === week) ?? WEEKLY_REPORTS[0];
  const range = `${format(parseISO(current.week_start), "MMM d")} – ${format(
    parseISO(current.week_end),
    "MMM d, yyyy",
  )}`;
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/80 px-4 backdrop-blur">
      <SidebarTrigger />
      <Separator orientation="vertical" className="h-5" />
      <div className="flex min-w-0 flex-col leading-tight">
        <span className="text-xs text-muted-foreground">Week of</span>
        <span className="truncate text-sm font-medium">{range}</span>
      </div>
      <div className="ml-auto flex items-center gap-2">
        <Select value={week} onValueChange={onWeekChange}>
          <SelectTrigger className="h-9 w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {WEEKLY_REPORTS.map((w) => (
              <SelectItem key={w.week} value={w.week}>
                {w.week} · {format(parseISO(w.week_start), "MMM d")}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          variant="outline"
          size="sm"
          onClick={() => toast.success("Data refreshed")}
        >
          <RefreshCw className="h-4 w-4" />
          <span className="hidden md:inline">Refresh</span>
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            downloadMarkdown(getWeek(week));
            toast.success("Markdown downloaded");
          }}
        >
          <FileText className="h-4 w-4" />
          <span className="hidden md:inline">Markdown</span>
        </Button>
        <Button
          size="sm"
          onClick={async () => {
            try {
              await downloadPDF(getWeek(week));
              toast.success("PDF downloaded");
            } catch (e) {
              console.error(e);
              toast.error("PDF export failed");
            }
          }}
        >
          <Download className="h-4 w-4" />
          <span className="hidden md:inline">Export PDF</span>
        </Button>

        {/* Custom ZpiIcon + full ZIP bundle (recommended) */}
        <Button
          variant="default"
          size="sm"
          className="gap-1.5 bg-zinc-900 hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200"
          onClick={async () => {
            try {
              await downloadZIP(getWeek(week));
              toast.success("ZIP archive downloaded");
            } catch (e) {
              console.error(e);
              toast.error("ZIP export failed");
            }
          }}
        >
          <ZpiIcon size={16} className="text-white dark:text-black" />
          <span className="hidden md:inline">Export ZIP</span>
        </Button>
      </div>
    </header>
  );
}
