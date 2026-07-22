import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, listAlerts: vi.fn() };
});

import { listAlerts } from "@/lib/api";
import { renderWithQueryClient } from "@/lib/test-utils";

import SecurityPage from "./page";

describe("SecurityPage", () => {
  beforeEach(() => {
    vi.mocked(listAlerts).mockReset();
  });

  it("renders an empty state when there are no alerts", async () => {
    vi.mocked(listAlerts).mockResolvedValue([]);

    renderWithQueryClient(<SecurityPage />);

    expect(await screen.findByText(/no security alerts/i)).toBeInTheDocument();
  });

  it("renders a table row per alert", async () => {
    vi.mocked(listAlerts).mockResolvedValue([
      {
        id: "alert-1",
        run_id: "run-1",
        agent_name: "support-bot",
        category: "pii",
        severity: "high",
        detail: "Detected an SSN",
        created_at: "2026-01-01T00:00:00Z",
      },
    ]);

    renderWithQueryClient(<SecurityPage />);

    await waitFor(() => expect(screen.getByText("support-bot")).toBeInTheDocument());
    expect(screen.getByText("pii")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
  });
});
