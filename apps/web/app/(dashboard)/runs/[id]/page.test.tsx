import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "run-1" }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, getRun: vi.fn() };
});

import { getRun } from "@/lib/api";
import { renderWithQueryClient } from "@/lib/test-utils";

import RunDetailPage from "./page";

describe("RunDetailPage", () => {
  beforeEach(() => {
    vi.mocked(getRun).mockReset();
  });

  it("renders the agent name, status, and span tree", async () => {
    vi.mocked(getRun).mockResolvedValue({
      id: "run-1",
      agent_name: "support-bot",
      status: "completed",
      started_at: "2026-01-01T00:00:00Z",
      ended_at: "2026-01-01T00:00:05Z",
      risk_score: 0,
      spans: [
        {
          id: "span-1",
          parent_span_id: null,
          kind: "llm_call",
          input: null,
          output: null,
          prompt_tokens: 10,
          completion_tokens: 5,
          started_at: "2026-01-01T00:00:00Z",
          ended_at: "2026-01-01T00:00:01Z",
          tool_calls: [{ id: "tc-1", tool_name: "lookup_order", arguments: null, result: null }],
        },
      ],
    });

    renderWithQueryClient(<RunDetailPage />);

    await waitFor(() => expect(screen.getByText("support-bot")).toBeInTheDocument());
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("llm_call")).toBeInTheDocument();
    expect(screen.getByText("lookup_order")).toBeInTheDocument();
  });

  it("renders an empty state when the run has no spans", async () => {
    vi.mocked(getRun).mockResolvedValue({
      id: "run-1",
      agent_name: "support-bot",
      status: "running",
      started_at: "2026-01-01T00:00:00Z",
      ended_at: null,
      risk_score: 0,
      spans: [],
    });

    renderWithQueryClient(<RunDetailPage />);

    expect(await screen.findByText(/no spans/i)).toBeInTheDocument();
  });
});
