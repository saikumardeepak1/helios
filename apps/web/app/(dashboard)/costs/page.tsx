"use client";

import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getCostSummary } from "@/lib/api";

function formatUsd(value: string | number): string {
  return `$${Number(value).toFixed(2)}`;
}

export default function CostsPage() {
  const { data: summary, isLoading, isError } = useQuery({
    queryKey: ["cost-summary"],
    queryFn: () => getCostSummary(30),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Costs</h1>

      {isLoading && <p className="text-slate-600">Loading cost data…</p>}
      {isError && <p className="text-red-600">Couldn&apos;t load cost data.</p>}

      {summary && (
        <>
          <div className="rounded-md border border-slate-200 p-4">
            <p className="text-sm text-slate-500">Total spend, last 30 days</p>
            <p className="text-3xl font-semibold">{formatUsd(summary.total_usd)}</p>
          </div>

          {summary.by_day.length > 0 && (
            <div className="h-64 rounded-md border border-slate-200 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={summary.by_day}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="day" fontSize={12} />
                  <YAxis fontSize={12} tickFormatter={(v) => `$${v}`} />
                  <Tooltip formatter={(value: number) => formatUsd(value)} />
                  <Bar dataKey="cost_usd" fill="#0f172a" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {summary.by_agent.length > 0 ? (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="py-2 font-medium">Agent</th>
                  <th className="py-2 font-medium">Cost</th>
                </tr>
              </thead>
              <tbody>
                {summary.by_agent.map((row) => (
                  <tr key={row.agent_name} className="border-b border-slate-100">
                    <td className="py-2">{row.agent_name}</td>
                    <td className="py-2">{formatUsd(row.cost_usd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-slate-600">No cost data yet for this period.</p>
          )}
        </>
      )}
    </div>
  );
}
