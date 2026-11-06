import { describe, it, expect } from "vitest";
import { DialogueEngine } from "../src/engine";
import { nova } from "../src/agents";

describe("DialogueEngine", () => {
  it("starts at first step", () => {
    const e = new DialogueEngine(nova);
    expect(e.start().id).toBe("welcome");
  });
  it("advances", () => {
    const e = new DialogueEngine(nova);
    e.start();
    const next = e.next();
    expect(next?.id).toBe("what-is");
  });
});
