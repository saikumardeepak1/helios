import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "alert-1" }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, getAlert: vi.fn() };
});

import { getAlert } from "@/lib/api";
import { renderWithQueryClient } from "@/lib/test-utils";

import AlertDetailPage from "./page";

describe("AlertDetailPage", () => {
  beforeEach(() => {
    vi.mocked(getAlert).mockReset();
  });

  it("renders the alert detail and a link to the triggering run", async () => {
    vi.mocked(getAlert).mockResolvedValue({
      id: "alert-1",
      run_id: "run-42",
      agent_name: "support-bot",
      category: "pii",
      severity: "critical",
      detail: "Detected 2 PII finding(s): credit_card, ssn",
      created_at: "2026-01-01T00:00:00Z",
    });

    renderWithQueryClient(<AlertDetailPage />);

    await waitFor(() => expect(screen.getByText("pii")).toBeInTheDocument());
    expect(screen.getByText("critical")).toBeInTheDocument();
    expect(screen.getByText(/detected 2 pii finding/i)).toBeInTheDocument();

    const link = screen.getByRole("link", { name: /view the triggering run/i });
    expect(link).toHaveAttribute("href", "/runs/run-42");
  });
});
