import type { SpanNode } from "@/lib/span-tree";

function SpanRow({ node, depth }: { node: SpanNode; depth: number }) {
  const durationMs =
    node.ended_at && node.started_at
      ? new Date(node.ended_at).getTime() - new Date(node.started_at).getTime()
      : null;

  return (
    <li>
      <div
        className="flex items-center gap-3 border-b border-slate-100 py-2 text-sm"
        style={{ paddingLeft: depth * 20 }}
      >
        <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
          {node.kind}
        </span>
        {(node.prompt_tokens > 0 || node.completion_tokens > 0) && (
          <span className="text-xs text-slate-500">
            {node.prompt_tokens} in / {node.completion_tokens} out tokens
          </span>
        )}
        {durationMs !== null && (
          <span className="text-xs text-slate-500">{durationMs}ms</span>
        )}
        {node.tool_calls.length > 0 && (
          <span className="text-xs text-slate-500">
            {node.tool_calls.map((tc) => tc.tool_name).join(", ")}
          </span>
        )}
      </div>
      {node.children.length > 0 && (
        <ul>
          {node.children.map((child) => (
            <SpanRow key={child.id} node={child} depth={depth + 1} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function SpanTreeView({ roots }: { roots: SpanNode[] }) {
  if (roots.length === 0) {
    return <p className="text-slate-600">This run has no spans.</p>;
  }

  return (
    <ul>
      {roots.map((root) => (
        <SpanRow key={root.id} node={root} depth={0} />
      ))}
    </ul>
  );
}
