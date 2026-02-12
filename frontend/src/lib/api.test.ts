import { describe, expect, test } from "vitest";

import { listModels } from "./api";

describe("listModels", () => {
  test("returns available model choices for settings page", async () => {
    const models = await listModels();

    expect(models).toContain("openai/gpt-5-image");
    expect(models).toContain("google/gemini-2.5-flash-image");
    expect(models).toContain("sourceful/riverflow-v2-fast-preview");
    expect(models.length).toBe(3);
  });
});
