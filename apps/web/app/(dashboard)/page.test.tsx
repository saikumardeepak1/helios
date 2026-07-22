import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, listRuns: vi.fn() };
});

import { listRuns } from "@/lib/api";
import { renderWithQueryClient } from "@/lib/test-utils";

import TracesPage from "./page";

describe("TracesPage", () => {
  beforeEach(() => {
    vi.mocked(listRuns).mockReset();
  });

  it("renders an empty state when there are no runs", async () => {
    vi.mocked(listRuns).mockResolvedValue([]);

    renderWithQueryClient(<TracesPage />);

    expect(await screen.findByText(/no runs yet/i)).toBeInTheDocument();
  });

  it("renders a table row per run", async () => {
    vi.mocked(listRuns).mockResolvedValue([
      {
        id: "run-1",
        agent_name: "support-bot",
        status: "completed",
        started_at: "2026-01-01T00:00:00Z",
        ended_at: null,
        span_count: 3,
        risk_score: 0,
      },
    ]);

    renderWithQueryClient(<TracesPage />);

    await waitFor(() => expect(screen.getByText("support-bot")).toBeInTheDocument());
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });
});
