import { z } from "zod";
import { providerConfig as openaiConfig, probe as openaiProbe } from "./adapters/openai";
import { providerConfig as anthropicConfig, probe as anthropicProbe } from "./adapters/anthropic";
import { providerConfig as geminiConfig, probe as geminiProbe } from "./adapters/gemini";
import { providerConfig as elevenlabsConfig, probe as elevenlabsProbe } from "./adapters/elevenlabs";
import { providerConfig as heygenConfig, probe as heygenProbe } from "./adapters/heygen";
import { providerConfig as runwayConfig, probe as runwayProbe } from "./adapters/runway";
import { providerConfig as stabilityConfig, probe as stabilityProbe } from "./adapters/stability";

export const ApiKeySchema = z.object({
  provider: z.enum(["openai", "anthropic", "gemini", "elevenlabs", "heygen", "runway", "stability"]),
  key: z.string().min(8),
});
export type ApiKey = z.infer<typeof ApiKeySchema>;

export const PROVIDERS = [
  openaiConfig,
  anthropicConfig,
  geminiConfig,
  elevenlabsConfig,
  heygenConfig,
  runwayConfig,
  stabilityConfig,
] as const;

// Per-provider probe functions, wired to the adapter modules.
const adapters: Record<string, (key: string) => Promise<{ ok: boolean; message: string }>> = {
  openai: openaiProbe,
  anthropic: anthropicProbe,
  gemini: geminiProbe,
  elevenlabs: elevenlabsProbe,
  heygen: heygenProbe,
  runway: runwayProbe,
  stability: stabilityProbe,
};

export async function probeProvider(provider: string, key: string): Promise<{ ok: boolean; message: string }> {
  const adapter = adapters[provider];
  if (adapter) return adapter(key);
  // Unknown provider: fall back to the generic mock gate.
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
