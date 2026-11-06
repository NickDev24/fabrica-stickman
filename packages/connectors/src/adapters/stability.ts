export const provider = "stability";
export const docUrl = "https://example.com/stability";
export async function probe(key: string) {
  if (!key || key.length < 8) return { ok: false, message: "Key too short" };
  return { ok: true, message: "stability OK (mock)" };
}
