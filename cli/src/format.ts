import type { RecallResult } from "./cogneeClient.js";

/** Pull display text out of a recall hit and strip the leading [tag=val ...] line. */
export function resultText(r: RecallResult): string {
  const raw = r.text ?? r.content ?? "";
  return raw.replace(/^\[[^\]]*\]\n?/, "").trim();
}

export function isEmpty(results: RecallResult[]): boolean {
  return results.length === 0 || results.every((r) => resultText(r) === "");
}
