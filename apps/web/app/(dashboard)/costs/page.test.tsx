import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, getCostSummary: vi.fn() };
});

import { getCostSummary } from "@/lib/api";
import { renderWithQueryClient } from "@/lib/test-utils";

import CostsPage from "./page";

describe("CostsPage", () => {
  beforeEach(() => {
    vi.mocked(getCostSummary).mockReset();
  });

  it("renders the total spend and per-agent breakdown", async () => {
    vi.mocked(getCostSummary).mockResolvedValue({
      total_usd: "12.50",
      by_agent: [{ agent_name: "support-bot", cost_usd: "12.50" }],
      by_day: [{ day: "2026-01-01", cost_usd: "12.50" }],
    });

    renderWithQueryClient(<CostsPage />);

    await waitFor(() => expect(screen.getAllByText("$12.50")).toHaveLength(2));
    expect(screen.getByText("support-bot")).toBeInTheDocument();
  });

  it("renders an empty state when there is no cost data", async () => {
    vi.mocked(getCostSummary).mockResolvedValue({
      total_usd: "0",
      by_agent: [],
      by_day: [],
    });

    renderWithQueryClient(<CostsPage />);

    expect(await screen.findByText(/no cost data yet/i)).toBeInTheDocument();
  });
});
