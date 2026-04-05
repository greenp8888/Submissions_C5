import type { DatePreset } from "@/lib/types";

export const DATE_PRESETS: Array<{ value: DatePreset; label: string }> = [
  { value: "last_30_days", label: "Last 30 days" },
  { value: "last_90_days", label: "Last 90 days" },
  { value: "last_1_year", label: "Last 1 year" },
  { value: "last_5_years", label: "Last 5 years" },
  { value: "all_time", label: "All time" },
];

export function presetToRange(preset: DatePreset) {
  const today = new Date();
  const end = today.toISOString().slice(0, 10);
  const start = new Date(today);

  if (preset === "all_time") {
    return { startDate: "", endDate: "" };
  }
  if (preset === "last_30_days") {
    start.setDate(start.getDate() - 30);
  } else if (preset === "last_90_days") {
    start.setDate(start.getDate() - 90);
  } else if (preset === "last_1_year") {
    start.setFullYear(start.getFullYear() - 1);
  } else {
    start.setFullYear(start.getFullYear() - 5);
  }
  return { startDate: start.toISOString().slice(0, 10), endDate: end };
}
