"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

import { SeverityBadge } from "@/components/severity-badge";
import { getAlert } from "@/lib/api";

export default function AlertDetailPage() {
  const params = useParams<{ id: string }>();
  const {
    data: alert,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["alerts", params.id],
    queryFn: () => getAlert(params.id),
  });

  if (isLoading) return <p className="text-slate-600">Loading alert…</p>;
  if (isError || !alert) return <p className="text-red-600">Couldn&apos;t load this alert.</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold">{alert.category}</h1>
        <SeverityBadge severity={alert.severity} />
      </div>
      <p className="text-sm text-slate-500">
        Agent {alert.agent_name} · Detected {new Date(alert.created_at).toLocaleString()}
      </p>

      <div className="rounded-md border border-slate-200 p-4">
        <p className="text-sm">{alert.detail}</p>
      </div>

      <Link href={`/runs/${alert.run_id}`} className="text-sm font-medium hover:underline">
        View the triggering run and its full span timeline →
      </Link>
    </div>
  );
}
