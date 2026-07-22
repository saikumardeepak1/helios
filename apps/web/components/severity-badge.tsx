import { cn } from "@/lib/utils";

const SEVERITY_STYLES: Record<string, string> = {
  medium: "bg-yellow-100 text-yellow-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
};

export function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        SEVERITY_STYLES[severity] ?? "bg-slate-100 text-slate-800"
      )}
    >
      {severity}
    </span>
  );
}
