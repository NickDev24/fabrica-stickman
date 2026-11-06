export const provider = "heygen";
export const docUrl = "https://example.com/heygen";
export async function probe(key: string) {
  if (!key || key.length < 8) return { ok: false, message: "Key too short" };
  return { ok: true, message: "heygen OK (mock)" };
}
