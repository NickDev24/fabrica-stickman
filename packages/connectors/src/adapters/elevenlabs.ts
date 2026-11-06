export const provider = "elevenlabs";
export const docUrl = "https://example.com/elevenlabs";
export async function probe(key: string) {
  if (!key || key.length < 8) return { ok: false, message: "Key too short" };
  return { ok: true, message: "elevenlabs OK (mock)" };
}
