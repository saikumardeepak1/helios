import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { setTokens } from "@/lib/api";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn() }),
}));

import { AuthGate } from "./auth-gate";

describe("AuthGate", () => {
  beforeEach(() => {
    replace.mockClear();
    window.localStorage.clear();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it("renders children when a token is present", () => {
    setTokens("access-123", "refresh-456");

    render(
      <AuthGate>
        <p>Protected content</p>
      </AuthGate>
    );

    expect(screen.getByText("Protected content")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("redirects to /login when no token is present", () => {
    render(
      <AuthGate>
        <p>Protected content</p>
      </AuthGate>
    );

    expect(replace).toHaveBeenCalledWith("/login");
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });
});
