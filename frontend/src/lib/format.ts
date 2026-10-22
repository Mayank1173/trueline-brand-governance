// Deterministic (no locale/timezone), so server and browser render the same text.
export function formatUtc(iso: string): string {
  return `${iso.slice(0, 10)} ${iso.slice(11, 16)} UTC`;
}
