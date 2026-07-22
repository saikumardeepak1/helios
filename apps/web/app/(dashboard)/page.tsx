"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { StatusBadge } from "@/components/status-badge";
import { listRuns } from "@/lib/api";

export default function TracesPage() {
  const { data: runs, isLoading, isError } = useQuery({
    queryKey: ["runs"],
    queryFn: listRuns,
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Traces</h1>

      {isLoading && <p className="text-slate-600">Loading runs…</p>}
      {isError && <p className="text-red-600">Couldn&apos;t load runs.</p>}

      {runs && runs.length === 0 && (
        <p className="text-slate-600">
          No runs yet. Instrument an agent with helios-sdk to see traces here.
        </p>
      )}

      {runs && runs.length > 0 && (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500">
              <th className="py-2 font-medium">Agent</th>
              <th className="py-2 font-medium">Status</th>
              <th className="py-2 font-medium">Spans</th>
              <th className="py-2 font-medium">Started</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="py-2">
                  <Link href={`/runs/${run.id}`} className="font-medium hover:underline">
                    {run.agent_name}
                  </Link>
                </td>
                <td className="py-2">
                  <StatusBadge status={run.status} />
                </td>
                <td className="py-2 text-slate-600">{run.span_count}</td>
                <td className="py-2 text-slate-600">
                  {new Date(run.started_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
