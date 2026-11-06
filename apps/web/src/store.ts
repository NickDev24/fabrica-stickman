import { create } from "zustand";
type Cfg = { key: string; value: string };
interface S {
  cfg: Cfg[];
  progress: number;
  add: (c: Cfg) => void;
  bump: () => void;
}
export const useStore = create<S>((set) => ({
  cfg: [],
  progress: 0,
  add: (c) => set((s) => ({ cfg: [...s.cfg, c] })),
  bump: () => set((s) => ({ progress: Math.min(100, s.progress + 25) })),
}));
export async function seal(text: string): Promise<string> {
  const enc = new TextEncoder();
  const k = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, k, enc.encode(text));
  return btoa(String.fromCharCode(...new Uint8Array(ct)));
}
export function exportEnv(cfg: Cfg[]): string {
  return cfg.map((c) => `${c.key}=${c.value}`).join("\n");
}
