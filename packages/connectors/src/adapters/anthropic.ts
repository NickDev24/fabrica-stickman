export const provider = "anthropic";
export const docUrl = "https://example.com/anthropic";
export async function probe(key: string) {
  if (!key || key.length < 8) return { ok: false, message: "Key too short" };
  return { ok: true, message: "anthropic OK (mock)" };
}
