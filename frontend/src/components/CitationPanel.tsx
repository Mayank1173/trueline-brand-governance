import type { Citation } from "@/lib/types";

export default function CitationPanel({ citation }: { citation: Citation }) {
  return (
    <details className="rounded-xl border border-line bg-surface-2 p-3 text-sm">
      <summary className="cursor-pointer font-medium text-ink">Why? Rule {citation.rule_id}</summary>
      <p className="mt-2 text-ink">{citation.excerpt}</p>
      <p className="mt-1 text-xs text-muted">Source: {citation.source}</p>
    </details>
  );
}