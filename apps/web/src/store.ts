import { create } from "zustand";
export type Cfg = { key: string; value: string };
interface S {
  cfg: Cfg[];
  progress: number;
  add: (c: Cfg) => void;
  bump: () => void;
  load: () => void;
}
const KEY = "fabrica.cfg.v1";
const enc = new TextEncoder();
export const useStore = create<S>((set) => ({
  cfg: [],
  progress: 0,
  add: (c) =>
    set((s) => {
      const cfg = [...s.cfg, c];
      try {
        localStorage.setItem(KEY, JSON.stringify(cfg));
      } catch {}
      return { cfg };
    }),
  bump: () => set((s) => ({ progress: Math.min(100, s.progress + 25) })),
  load: () => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) set({ cfg: JSON.parse(raw) });
    } catch {}
  },
}));

/**
 * Encrypt a value with AES-GCM.
 *
 * The AES key is stored (base64) in sessionStorage — never persisted to
 * IndexedDB. `seal`/`unseal` share one key per tab, so repeated calls
 * round-trip correctly. The key is generated fresh on each new tab.
 */
let keyHandle: CryptoKey | null = null;
let keyReady = false;

async function ensureKey(): Promise<void> {
  if (keyReady) return;
  let raw = sessionStorage.getItem("fabrica.encrypt.key");
  if (!raw) {
    const arr = crypto.getRandomValues(new Uint8Array(32));
    raw = btoa(String.fromCharCode(...arr));
    sessionStorage.setItem("fabrica.encrypt.key", raw);
  }
  const binary = atob(raw);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  keyHandle = await crypto.subtle.importKey(
    "raw",
    bytes,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
  keyReady = true;
}

export async function seal(text: string): Promise<string> {
  await ensureKey();
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, keyHandle!, enc.encode(text));
  const buf = new Uint8Array(iv.length + ct.byteLength);
  buf.set(iv);
  buf.set(new Uint8Array(ct), iv.length);
  return btoa(String.fromCharCode(...buf));
}

export function exportEnv(cfg: Cfg[]): string {
  return cfg.map((c) => `${c.key}=${c.value}`).join("\n");
}
