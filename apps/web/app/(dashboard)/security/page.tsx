"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { SeverityBadge } from "@/components/severity-badge";
import { listAlerts } from "@/lib/api";

export default function SecurityPage() {
  const { data: alerts, isLoading, isError } = useQuery({
    queryKey: ["alerts"],
    queryFn: listAlerts,
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Security</h1>

      {isLoading && <p className="text-slate-600">Loading alerts…</p>}
      {isError && <p className="text-red-600">Couldn&apos;t load alerts.</p>}

      {alerts && alerts.length === 0 && (
        <p className="text-slate-600">No security alerts. Nice and quiet.</p>
      )}

      {alerts && alerts.length > 0 && (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500">
              <th className="py-2 font-medium">Severity</th>
              <th className="py-2 font-medium">Category</th>
              <th className="py-2 font-medium">Agent</th>
              <th className="py-2 font-medium">Detected</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert) => (
              <tr key={alert.id} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="py-2">
                  <Link href={`/security/${alert.id}`} className="hover:underline">
                    <SeverityBadge severity={alert.severity} />
                  </Link>
                </td>
                <td className="py-2">{alert.category}</td>
                <td className="py-2 text-slate-600">{alert.agent_name}</td>
                <td className="py-2 text-slate-600">
                  {new Date(alert.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
