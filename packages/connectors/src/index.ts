import { z } from "zod";

export const ApiKeySchema = z.object({
  provider: z.enum(["openai", "anthropic", "gemini", "elevenlabs", "heygen", "runway", "stability"]),
  key: z.string().min(8),
});

export type ApiKey = z.infer<typeof ApiKeySchema>;

export const PROVIDERS = [
  { id: "openai", name: "OpenAI", doc: "https://platform.openai.com/api-keys", probe: "https://api.openai.com/v1/models" },
  { id: "anthropic", name: "Anthropic", doc: "https://console.anthropic.com/settings/keys", probe: "https://api.anthropic.com/v1/messages" },
  { id: "gemini", name: "Google Gemini", doc: "https://aistudio.google.com/app/apikey", probe: "https://generativelanguage.googleapis.com/v1beta/models" },
  { id: "elevenlabs", name: "ElevenLabs", doc: "https://elevenlabs.io/app/settings/api-keys", probe: "https://api.elevenlabs.io/v1/user" },
  { id: "heygen", name: "HeyGen", doc: "https://app.heygen.com/settings/api", probe: "https://api.heygen.com/v2/user/remaining_quota" },
  { id: "runway", name: "Runway", doc: "https://dev.runwayml.com/", probe: "https://api.dev.runwayml.com/v1" },
  { id: "stability", name: "Stability AI", doc: "https://platform.stability.ai/account/keys", probe: "https://api.stability.ai/v1/user/account" },
] as const;

export async function probeProvider(provider: string, key: string): Promise<{ ok: boolean; message: string }> {
  // Mock probe (real network calls wired per-adapter in production).
  if (!key || key.length < 8) return { ok: false, message: "Key too short" };
  return { ok: true, message: `${provider}: connection OK (mock)` };
}

export const McpServerSchema = z.object({
  name: z.string(),
  command: z.string(),
  args: z.array(z.string()).default([]),
  env: z.record(z.string()).optional(),
});
export type McpServer = z.infer<typeof McpServerSchema>;

export const POPULAR_MCPS = ["filesystem", "fetch", "playwright", "github", "memory", "sequential-thinking"];

export const ZernioPlatformSchema = z.enum(["tiktok", "facebook", "instagram", "youtube"]);
export type ZernioPlatform = z.infer<typeof ZernioPlatformSchema>;

export interface ZernioAccount {
  platform: ZernioPlatform;
  accountId: string;
  displayName: string;
  avatarUrl?: string;
}

export async function zernioOAuthStart(platform: ZernioPlatform): Promise<{ authUrl: string; redirectUri: string }> {
  return {
    authUrl: `https://zernio.example.com/oauth/${platform}?redirect_uri=http://localhost:4321/callback`,
    redirectUri: "http://localhost:4321/callback",
  };
}

export * from "./oauth";

export function exportEnv(config: Record<string, string>): string {
  return Object.entries(config)
    .map(([k, v]) => `${k}=${v}`)
    .join("\n") + "\n";
}

export async function scanMcpInstalled(): Promise<string[]> {
  return ["filesystem", "fetch"];
}

export async function scanSkills(dirs: string[]): Promise<string[]> {
  return dirs.flatMap(() => ["example-skill"]);
}

export async function installSkill(repo: string): Promise<{ ok: boolean; message: string }> {
  return { ok: true, message: `Installed ${repo} (mock)` };
}
