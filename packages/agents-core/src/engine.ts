import type { Agent, Step } from "./types";

export class DialogueEngine {
  private agent: Agent;
  private index = 0;
  private context: Record<string, unknown> = {};

  constructor(agent: Agent) {
    this.agent = agent;
  }

  getContext() { return this.context; }
  setContext(k: string, v: unknown) { this.context[k] = v; }

  start(): Step { this.index = 0; return this.agent.steps[0]; }

  current(): Step { return this.agent.steps[this.index]; }

  next(input?: unknown): Step | null {
    const step = this.agent.steps[this.index];
    if (input !== undefined && step.inputKey) this.context[step.inputKey] = input;
    if (step.type === "branch" && step.branches && typeof input === "string") {
      const target = step.branches[input];
      const idx = this.agent.steps.findIndex(s => s.id === target);
      if (idx >= 0) { this.index = idx; return this.agent.steps[idx]; }
    }
    const nextId = step.next;
    if (nextId) {
      const idx = this.agent.steps.findIndex(s => s.id === nextId);
      if (idx >= 0) { this.index = idx; return this.agent.steps[idx]; }
    }
    this.index += 1;
    if (this.index >= this.agent.steps.length) return null;
    return this.agent.steps[this.index];
  }

  validate(step: Step, value: unknown): boolean {
    if (step.type !== "input") return true;
    if (step.inputType === "secret") return typeof value === "string" && value.length > 8;
    if (step.inputType === "text") return typeof value === "string" && value.trim().length > 0;
    return true;
  }
}
