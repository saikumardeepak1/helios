import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "./page";

describe("HomePage", () => {
  it("renders the Helios heading", () => {
    render(<HomePage />);
    expect(screen.getByRole("heading", { name: "Helios" })).toBeInTheDocument();
  });
});
