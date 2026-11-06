export const provider = "gemini";
export const docUrl = "https://example.com/gemini";
export async function probe(key: string) {
  if (!key || key.length < 8) return { ok: false, message: "Key too short" };
  return { ok: true, message: "gemini OK (mock)" };
}
