import type { Agent, Step } from "./types";

export class DialogueEngine {
  private agent: Agent;
  private index = 0;
  private context: Record<string, unknown> = {};

  constructor(agent: Agent) {
    this.agent = agent;
  }

  getContext(): Record<string, unknown> {
    return this.context;
  }

  setContext(key: string, value: unknown): void {
    this.context[key] = value;
  }

  start(): Step {
    this.index = 0;
    return this.current();
  }

  current(): Step {
    const step = this.agent.steps[this.index];
    return step ?? this.agent.steps[0] as Step;
  }

  next(input?: unknown): Step | null {
    const step = this.agent.steps[this.index];
    if (step === undefined) return null;

    if (input !== undefined && step.inputKey) {
      this.context[step.inputKey] = input;
    }

    if (step.type === "branch" && step.branches && typeof input === "string") {
      const target = step.branches[input];
      const idx = this.agent.steps.findIndex((s) => s.id === target);
      if (idx >= 0) {
        this.index = idx;
        return this.agent.steps[idx] as Step;
      }
    }

    const nextId = step.next;
    if (nextId) {
      const idx = this.agent.steps.findIndex((s) => s.id === nextId);
      if (idx >= 0) {
        this.index = idx;
        return this.agent.steps[idx] as Step;
      }
    }

    this.index += 1;
    const next = this.agent.steps[this.index];
    if (next === undefined) return null;
    return next;
  }

  validate(step: Step, value: unknown): boolean {
    if (step.type !== "input") return true;
    if (step.inputType === "secret") return typeof value === "string" && value.length > 8;
    if (step.inputType === "text") return typeof value === "string" && value.trim().length > 0;
    return true;
  }

  onError(err: unknown): Step {
    const idx = this.agent.steps.findIndex((s) => s.type === "input");
    if (idx >= 0) {
      this.index = idx;
      return this.current();
    }
    this.index = 0;
    return this.current();
  }

  onComplete(): Step {
    this.index = 0;
    return this.current();
  }
}
