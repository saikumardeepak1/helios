"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { SpanTreeView } from "@/components/span-tree-view";
import { StatusBadge } from "@/components/status-badge";
import { getRun } from "@/lib/api";
import { buildSpanTree } from "@/lib/span-tree";

export default function RunDetailPage() {
  const params = useParams<{ id: string }>();
  const {
    data: run,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["runs", params.id],
    queryFn: () => getRun(params.id),
  });

  if (isLoading) return <p className="text-slate-600">Loading run…</p>;
  if (isError || !run) return <p className="text-red-600">Couldn&apos;t load this run.</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold">{run.agent_name}</h1>
        <StatusBadge status={run.status} />
      </div>
      <p className="text-sm text-slate-500">
        Started {new Date(run.started_at).toLocaleString()}
        {run.ended_at && ` · Ended ${new Date(run.ended_at).toLocaleString()}`}
      </p>

      <div className="rounded-md border border-slate-200 p-4">
        <SpanTreeView roots={buildSpanTree(run.spans)} />
      </div>
    </div>
  );
}
