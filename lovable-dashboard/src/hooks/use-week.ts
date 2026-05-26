import { useNavigate, useSearch } from "@tanstack/react-router";
import { WEEKLY_REPORTS, getWeek } from "@/lib/mock-data";

export function useWeek() {
  const navigate = useNavigate();
  const search = useSearch({ strict: false }) as { week?: string };
  const week = search.week ?? WEEKLY_REPORTS[WEEKLY_REPORTS.length - 1].week;
  const setWeek = (w: string) => {
    navigate({ to: ".", search: (prev: Record<string, unknown>) => ({ ...prev, week: w }) } as never);
  };
  return { week, setWeek, report: getWeek(week) };
}
