import { z } from "zod";

export const StepSchema = z.object({
  id: z.string(),
  type: z.enum(["info", "input", "action", "branch", "complete"]),
  agent: z.string(),
  title: z.string(),
  body: z.string(),
  inputKey: z.string().optional(),
  inputType: z.enum(["text", "secret", "select", "boolean"]).optional(),
  options: z.array(z.string()).optional(),
  validate: z.string().optional(),
  next: z.string().optional(),
  branches: z.record(z.string()).optional(),
  helpUrl: z.string().optional(),
  explainLike10: z.string().optional(),
});

export type Step = z.infer<typeof StepSchema>;

export const AgentSchema = z.object({
  id: z.string(),
  name: z.string(),
  role: z.string(),
  avatar: z.string(),
  steps: z.array(StepSchema),
});

export type Agent = z.infer<typeof AgentSchema>;

export interface AgentRuntime {
  id: string;
  start(): Step;
  next(input?: unknown): Step | null;
  validate(step: Step, value: unknown): boolean;
  onError(err: unknown): Step;
  onComplete(): Step;
}
