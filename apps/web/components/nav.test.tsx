import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: vi.fn() }),
}));

import { Nav } from "./nav";

describe("Nav", () => {
  it("renders links for each dashboard section", () => {
    render(<Nav />);

    expect(screen.getByRole("link", { name: /traces/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /costs/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /security/i })).toBeInTheDocument();
  });

  it("renders a sign out control", () => {
    render(<Nav />);
    expect(screen.getByRole("button", { name: /sign out/i })).toBeInTheDocument();
  });
});
