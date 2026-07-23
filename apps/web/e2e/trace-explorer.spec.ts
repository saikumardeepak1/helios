import { expect, test } from "@playwright/test";

const API_ORIGIN = "http://localhost:8000";

const RUN_ID = "11111111-1111-1111-1111-111111111111";

test("login, browse the trace list, and drill into a run's span timeline", async ({ page }) => {
  await page.route(`${API_ORIGIN}/v1/auth/login`, async (route) => {
    await route.fulfill({
      json: {
        access_token: "fake-access-token",
        refresh_token: "fake-refresh-token",
        token_type: "bearer",
      },
    });
  });

  await page.route(`${API_ORIGIN}/v1/runs`, async (route) => {
    await route.fulfill({
      json: [
        {
          id: RUN_ID,
          agent_name: "support-bot",
          status: "completed",
          started_at: "2026-01-01T00:00:00Z",
          ended_at: "2026-01-01T00:00:05Z",
          span_count: 1,
          risk_score: 0,
        },
      ],
    });
  });

  await page.route(`${API_ORIGIN}/v1/runs/${RUN_ID}`, async (route) => {
    await route.fulfill({
      json: {
        id: RUN_ID,
        agent_name: "support-bot",
        status: "completed",
        started_at: "2026-01-01T00:00:00Z",
        ended_at: "2026-01-01T00:00:05Z",
        risk_score: 0,
        spans: [
          {
            id: "22222222-2222-2222-2222-222222222222",
            parent_span_id: null,
            kind: "llm_call",
            model: "gpt-4o-mini",
            input: { prompt: "Where is my order?" },
            output: { text: "Your order shipped yesterday." },
            prompt_tokens: 12,
            completion_tokens: 8,
            started_at: "2026-01-01T00:00:00Z",
            ended_at: "2026-01-01T00:00:01Z",
            tool_calls: [
              { id: "tc-1", tool_name: "lookup_order", arguments: null, result: null },
            ],
          },
        ],
      },
    });
  });

  await page.goto("/login");
  await page.getByLabel("Email").fill("dashboard@example.com");
  await page.getByLabel("Password").fill("hunter2");
  await page.getByRole("button", { name: /sign in/i }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByRole("link", { name: "support-bot" })).toBeVisible();
  await expect(page.getByText("completed")).toBeVisible();

  await page.getByRole("link", { name: "support-bot" }).click();

  await expect(page).toHaveURL(`/runs/${RUN_ID}`);
  await expect(page.getByRole("heading", { name: "support-bot" })).toBeVisible();
  await expect(page.getByText("llm_call")).toBeVisible();
  await expect(page.getByText("lookup_order")).toBeVisible();
});
