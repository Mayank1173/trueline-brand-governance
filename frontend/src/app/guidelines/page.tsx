"use client";
import { useEffect, useState } from "react";
import SampleDataNotice from "@/components/SampleDataNotice";
import { SAMPLE_GUIDELINES as g } from "@/lib/mock/sampleData";
import { apiGet, isLive } from "@/lib/api";

const BRAND_ID = "brand_001"; // same ID the review flow uses with the backend

interface Guideline {
  source_id: string;
  rule_id: string;
  title: string;
  section: string | null;
  content: string;
  category: string;
  severity: string;
}

interface Fact {
  source_id: string;
  statement: string;
  source: string;
  valid_until: string | null;
  is_current: boolean;
}

interface LiveData {
  brandName: string;
  guidelines: Guideline[];
  facts: Fact[];
}

const CATEGORY_LABEL: Record<string, string> = {
  tone: "Voice and tone",
  preferred_terminology: "Preferred terminology",
  banned_term: "Banned or discouraged terms",
  required_phrase: "Required phrases and disclaimers",
  unsupported_claim: "Claims",
  product_name: "Product names",
  formatting: "Formatting",
  length_limit: "Length limits",
  fact_metadata: "Fact validity",
};

const chip = "rounded border border-line px-1.5 py-0.5 text-xs text-muted";

// The backend puts the demo-data warning inside every rule title. The page already shows
// it once in the disclaimer note, so strip it from the per-rule display.
function cleanTitle(title: string): string {
  const cleaned = title.replace(/\s*\(ILLUSTRATIVE DEMO DATA[^)]*\)/i, "").trim();
  return cleaned || title;
}

function Live({ data }: { data: LiveData }) {
  const groups = new Map<string, Guideline[]>();
  for (const r of data.guidelines) {
    groups.set(r.category, [...(groups.get(r.category) ?? []), r]);
  }

  const titles = new Set(data.guidelines.map((r) => cleanTitle(r.title)));
  const sharedTitle = titles.size === 1 ? [...titles][0] : null;

  return (
    <>
      <p className="text-sm text-muted">
        Rules for <span className="font-semibold text-ink">{data.brandName}</span>. Read-only.
      </p>
      <div role="note" className="rounded-xl border border-line bg-surface-2 p-3 text-sm">
        <strong>Illustrative demo data.</strong> These brands, rules and facts are fictional and are not
        official brand policy.
        {sharedTitle && <span className="mt-1 block text-xs text-muted">Source document: {sharedTitle}</span>}
      </div>

      {[...groups.entries()].map(([cat, rules]) => (
        <section key={cat} aria-label={CATEGORY_LABEL[cat] ?? cat} className="rounded-2xl border border-line bg-surface p-5">
          <h2 className="text-lg font-semibold">{CATEGORY_LABEL[cat] ?? cat}</h2>
          <ul className="mt-3 space-y-3">
            {rules.map((r) => (
              <li key={r.source_id} className="text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={chip}>{r.rule_id}</span>
                  {!sharedTitle && <strong>{cleanTitle(r.title)}</strong>}
                  <span className="text-xs text-muted">
                    {r.severity} severity{r.section ? ` · §${r.section}` : ""}
                  </span>
                </div>
                <p className="mt-1 text-ink">{r.content}</p>
              </li>
            ))}
          </ul>
        </section>
      ))}

      <section aria-labelledby="facts-h" className="rounded-2xl border border-line bg-surface p-5">
        <h2 id="facts-h" className="text-lg font-semibold">Approved facts</h2>
        {data.facts.length === 0 ? (
          <p className="mt-3 text-sm text-muted">No approved facts for this brand.</p>
        ) : (
          <ul className="mt-3 space-y-3">
            {data.facts.map((f) => (
              <li
                key={f.source_id}
                className={`text-sm ${f.is_current ? "" : "rounded-xl border border-dashed border-line bg-surface-2 p-3"}`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className={chip}>{f.source_id}</span>
                  {!f.is_current && (
                    <span className="rounded-full border border-line px-2 py-0.5 text-xs font-semibold text-amber">
                      ⚠ Not current
                    </span>
                  )}
                  <span className={f.is_current ? "" : "text-muted"}>{f.statement}</span>
                </div>
                <p className="mt-1 text-xs text-muted">
                  Source: {f.source} · {f.valid_until ? `Valid until ${f.valid_until}` : "No expiry set"}
                </p>
                <p className={`mt-1 text-xs font-semibold ${f.is_current ? "text-muted" : "text-amber"}`}>
                  {f.is_current ? "✓ Current" : "⚠ Not current: expired, not yet valid, or superseded. Do not rely on it."}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}

function Sample() {
  return (
    <>
      <SampleDataNotice>Live guidelines need the backend. These rules are examples only.</SampleDataNotice>
      <p className="text-sm text-muted">
        Rules for <span className="font-semibold text-ink">{g.name}</span>.
      </p>
      <ul className="space-y-2 text-sm">
        {g.banned_terms.map((r) => (
          <li key={r.rule_id}>
            <span className={chip}>{r.rule_id}</span> <strong>{r.term}</strong>: {r.reason}
          </li>
        ))}
      </ul>
    </>
  );
}

export default function GuidelinesPage() {
  const [data, setData] = useState<LiveData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!isLive) return;
    let cancelled = false;
    Promise.all([
      apiGet<{ brand?: { name?: string }; guidelines?: unknown }>(`/api/brands/${BRAND_ID}/guidelines`),
      apiGet<{ approved_facts?: unknown }>(`/api/brands/${BRAND_ID}/facts`),
    ])
      .then(([gl, fa]) => {
        if (cancelled) return;
        if (!Array.isArray(gl.guidelines) || !Array.isArray(fa.approved_facts)) {
          throw new Error("The backend returned an unexpected guidelines response.");
        }
        setData({
          brandName: gl.brand?.name ?? BRAND_ID,
          guidelines: gl.guidelines as Guideline[],
          facts: fa.approved_facts as Fact[],
        });
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Couldn't load guidelines.");
      });
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  function retry() {
    setError(null);
    setData(null);
    setAttempt((a) => a + 1);
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <h1 className="text-3xl font-bold tracking-tight md:text-5xl">Brand guidelines</h1>

      {!isLive && <Sample />}

      {isLive && error && (
        <div role="alert" className="rounded-xl border border-line bg-surface p-3 text-sm">
          <strong>Couldn’t load guidelines.</strong> {error}
          <div className="mt-2">
            <button
              type="button"
              onClick={retry}
              className="rounded-full border border-line px-4 py-1.5 text-sm font-medium hover:bg-surface-2"
            >
              Try again
            </button>
          </div>
        </div>
      )}

      {isLive && !error && !data && (
        <p role="status" className="rounded-2xl border border-line bg-surface p-5 text-sm text-muted">
          Loading guidelines…
        </p>
      )}

      {isLive && data && <Live data={data} />}
    </div>
  );
}