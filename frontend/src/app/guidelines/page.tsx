"use client";

import { useEffect, useState } from "react";
import SampleDataNotice from "@/components/SampleDataNotice";
import { apiGet, fetchBrands, isLive } from "@/lib/api";
import { SAMPLE_GUIDELINES as sample } from "@/lib/mock/sampleData";

interface Guideline { source_id: string; rule_id: string; section: string | null; content: string; category: string; severity: string; }
interface Fact { source_id: string; statement: string; source: string; valid_until: string | null; }
interface LiveData { brandName: string; guidelines: Guideline[]; facts: Fact[]; }

export default function GuidelinesPage() {
  const [data, setData] = useState<LiveData | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!isLive) return;
    let cancelled = false;
    fetchBrands().then(async (brands) => {
      const brand = brands[0];
      const [guidelines, facts] = await Promise.all([
        apiGet<{ brand?: { name?: string }; guidelines?: unknown }>(`/api/brands/${encodeURIComponent(brand.id)}/guidelines`),
        apiGet<{ approved_facts?: unknown }>(`/api/brands/${encodeURIComponent(brand.id)}/facts`),
      ]);
      if (!Array.isArray(guidelines.guidelines) || !Array.isArray(facts.approved_facts)) throw new Error("The backend returned an unexpected guidelines response.");
      return { brandName: guidelines.brand?.name ?? brand.name, guidelines: guidelines.guidelines as Guideline[], facts: facts.approved_facts as Fact[] };
    }).then((value) => { if (!cancelled) setData(value); }).catch((err) => { if (!cancelled) setError(err instanceof Error ? err.message : "Couldn't load guidelines."); });
    return () => { cancelled = true; };
  }, []);

  if (!isLive) return <Sample />;
  if (error) return <div className="mx-auto max-w-4xl space-y-6"><h1 className="text-3xl font-bold tracking-tight md:text-5xl">Brand guidelines</h1><p role="alert" className="rounded-xl border border-maroon-soft bg-maroon/25 p-3 text-sm"><strong>Couldn’t load guidelines.</strong> {error}</p></div>;
  if (!data) return <div className="mx-auto max-w-4xl space-y-6"><h1 className="text-3xl font-bold tracking-tight md:text-5xl">Brand guidelines</h1><p role="status" className="rounded-2xl border border-line bg-surface p-5 text-sm text-muted">Loading guidelines…</p></div>;

  const groups = data.guidelines.reduce<Record<string, Guideline[]>>((all, rule) => ({ ...all, [rule.category]: [...(all[rule.category] ?? []), rule] }), {});
  return <div className="mx-auto max-w-4xl space-y-6"><h1 className="text-3xl font-bold tracking-tight md:text-5xl">Brand guidelines</h1><p className="text-sm text-muted">Rules for <span className="font-semibold text-ink">{data.brandName}</span>. Read-only.</p><p className="rounded-xl border border-line bg-surface-2 p-3 text-sm"><strong>Illustrative demo data.</strong> These rules and facts are examples only.</p>{Object.entries(groups).map(([category, rules]) => <section key={category} className="rounded-2xl border border-line bg-surface p-5"><h2 className="text-lg font-semibold">{category}</h2><ul className="mt-3 space-y-3">{rules.map((rule) => <li key={rule.source_id} className="text-sm"><span className="rounded border border-line px-1.5 py-0.5 text-xs text-muted">{rule.rule_id}</span> <span className="text-xs text-muted">{rule.severity} severity{rule.section ? ` · §${rule.section}` : ""}</span><p className="mt-1">{rule.content}</p></li>)}</ul></section>)}<section className="rounded-2xl border border-line bg-surface p-5"><h2 className="text-lg font-semibold">Approved facts</h2><ul className="mt-3 space-y-3">{data.facts.map((fact) => <li key={fact.source_id} className="text-sm"><span className="rounded border border-line px-1.5 py-0.5 text-xs text-muted">{fact.source_id}</span> {fact.statement}<p className="mt-1 text-xs text-muted">Source: {fact.source} · {fact.valid_until ? `Valid until ${fact.valid_until}` : "No expiry set"}</p></li>)}</ul></section></div>;
}

function Sample() {
  return <div className="mx-auto max-w-4xl space-y-6"><h1 className="text-3xl font-bold tracking-tight md:text-5xl">Brand guidelines</h1><SampleDataNotice>These rules are examples, not a real brand’s guidelines.</SampleDataNotice><p className="text-sm text-muted">Rules for <span className="font-semibold text-ink">{sample.name}</span>.</p><ul className="space-y-2 text-sm">{sample.banned_terms.map((rule) => <li key={rule.rule_id}><strong>{rule.term}</strong>: {rule.reason}</li>)}</ul></div>;
}
