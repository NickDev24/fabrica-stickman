export const provider = "runway";
export const docUrl = "https://example.com/runway";
export async function probe(key: string) {
  if (!key || key.length < 8) return { ok: false, message: "Key too short" };
  return { ok: true, message: "runway OK (mock)" };
}
