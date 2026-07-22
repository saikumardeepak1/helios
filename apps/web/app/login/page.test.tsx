import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, login: vi.fn(), setTokens: vi.fn() };
});

import { ApiError, login, setTokens } from "@/lib/api";

import LoginPage from "./page";

describe("LoginPage", () => {
  beforeEach(() => {
    push.mockClear();
    vi.mocked(login).mockReset();
    vi.mocked(setTokens).mockReset();
  });

  it("stores tokens and redirects on successful login", async () => {
    vi.mocked(login).mockResolvedValue({
      access_token: "access-123",
      refresh_token: "refresh-456",
      token_type: "bearer",
    });

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "a@acme.com" } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "hunter2" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/"));
    expect(setTokens).toHaveBeenCalledWith("access-123", "refresh-456");
  });

  it("shows an error message when login fails", async () => {
    vi.mocked(login).mockRejectedValue(new ApiError(401, "Invalid email or password"));

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "a@acme.com" } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "wrong" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password");
    expect(push).not.toHaveBeenCalled();
  });
});
