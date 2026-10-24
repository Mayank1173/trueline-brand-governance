import type { Finding } from "./types";

/**
 * Returns the new draft with the fix applied, or null if it can't be applied safely.
 * Offsets refer to the ORIGINAL draft, so after earlier edits they may be stale:
 * we only trust them if the text at that position still matches.
 */
export function applySuggestedFix(draft: string, f: Finding): string | null {
  if (typeof f.suggested_fix !== "string") return null;

  if (!f.matched_text) {
    return `${draft.trimEnd()} ${f.suggested_fix}`; // missing-phrase case: append
  }

  if (f.start !== undefined && f.end !== undefined && draft.slice(f.start, f.end) === f.matched_text) {
    return draft.slice(0, f.start) + f.suggested_fix + draft.slice(f.end);
  }

  const idx = draft.indexOf(f.matched_text);
  if (idx === -1) return null;
  return draft.slice(0, idx) + f.suggested_fix + draft.slice(idx + f.matched_text.length);
}