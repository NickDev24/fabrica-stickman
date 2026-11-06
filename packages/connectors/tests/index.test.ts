import { describe, it, expect } from "vitest";
import { probeProvider, exportEnv } from "../src/index";

describe("connectors", () => {
  it("rejects short keys", async () => {
    const r = await probeProvider("openai", "short");
    expect(r.ok).toBe(false);
  });
  it("accepts valid keys (mock)", async () => {
    const r = await probeProvider("openai", "sk-1234567890");
    expect(r.ok).toBe(true);
  });
  it("exports env", () => {
    expect(exportEnv({ A: "1" })).toContain("A=1");
  });
});
