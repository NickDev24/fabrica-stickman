export const provider = "openai";
export const docUrl = "https://example.com/openai";
export async function probe(key: string) {
  if (!key || key.length < 8) return { ok: false, message: "Key too short" };
  return { ok: true, message: "openai OK (mock)" };
}
