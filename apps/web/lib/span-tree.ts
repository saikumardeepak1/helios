import type { Span } from "@/lib/api";

export interface SpanNode extends Span {
  children: SpanNode[];
}

export function buildSpanTree(spans: Span[]): SpanNode[] {
  const nodesById = new Map<string, SpanNode>(
    spans.map((span) => [span.id, { ...span, children: [] }])
  );
  const roots: SpanNode[] = [];

  for (const node of nodesById.values()) {
    if (node.parent_span_id && nodesById.has(node.parent_span_id)) {
      nodesById.get(node.parent_span_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  }

  return roots;
}
