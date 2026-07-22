import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch, clearTokens, getAccessToken, setTokens } from "./api";

describe("token storage", () => {
  afterEach(() => {
    window.localStorage.clear();
  });

  it("returns null when no token is stored", () => {
    expect(getAccessToken()).toBeNull();
  });

  it("stores and retrieves tokens", () => {
    setTokens("access-123", "refresh-456");
    expect(getAccessToken()).toBe("access-123");
    expect(window.localStorage.getItem("helios_refresh_token")).toBe("refresh-456");
  });

  it("clears tokens", () => {
    setTokens("access-123", "refresh-456");
    clearTokens();
    expect(getAccessToken()).toBeNull();
  });
});

describe("apiFetch", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("attaches the bearer token when present", async () => {
    setTokens("access-123", "refresh-456");
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), { status: 200 })
    );

    await apiFetch("/v1/whoami");

    const [, init] = vi.mocked(fetch).mock.calls[0];
    const headers = init?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer access-123");
  });

  it("throws ApiError with the response detail on failure", async () => {
    vi.mocked(fetch).mockImplementation(
      async () =>
        new Response(JSON.stringify({ detail: "Invalid email or password" }), { status: 401 })
    );

    await expect(apiFetch("/v1/auth/login")).rejects.toThrow(ApiError);
    await expect(apiFetch("/v1/auth/login")).rejects.toThrow("Invalid email or password");
  });
});
