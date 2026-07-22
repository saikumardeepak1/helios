import { describe, expect, it } from "vitest";

import type { Span } from "@/lib/api";
import { buildSpanTree } from "@/lib/span-tree";

function span(overrides: Partial<Span>): Span {
  return {
    id: "id",
    parent_span_id: null,
    kind: "llm_call",
    input: null,
    output: null,
    prompt_tokens: 0,
    completion_tokens: 0,
    started_at: "2026-01-01T00:00:00Z",
    ended_at: null,
    tool_calls: [],
    ...overrides,
  };
}

describe("buildSpanTree", () => {
  it("returns spans with no parent as roots", () => {
    const tree = buildSpanTree([span({ id: "a" }), span({ id: "b" })]);
    expect(tree).toHaveLength(2);
  });

  it("nests a span under its parent", () => {
    const tree = buildSpanTree([
      span({ id: "root" }),
      span({ id: "child", parent_span_id: "root" }),
    ]);

    expect(tree).toHaveLength(1);
    expect(tree[0].children).toHaveLength(1);
    expect(tree[0].children[0].id).toBe("child");
  });

  it("treats a span with an unknown parent id as a root", () => {
    const tree = buildSpanTree([span({ id: "orphan", parent_span_id: "missing" })]);
    expect(tree).toHaveLength(1);
    expect(tree[0].id).toBe("orphan");
  });

  it("supports multiple levels of nesting", () => {
    const tree = buildSpanTree([
      span({ id: "root" }),
      span({ id: "mid", parent_span_id: "root" }),
      span({ id: "leaf", parent_span_id: "mid" }),
    ]);

    expect(tree[0].children[0].children[0].id).toBe("leaf");
  });
});
