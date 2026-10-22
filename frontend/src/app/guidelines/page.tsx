import SampleDataNotice from "@/components/SampleDataNotice";
import { SAMPLE_GUIDELINES as g } from "@/lib/mock/sampleData";

function RuleId({ id }: { id: string }) {
  return <span className="rounded border border-line px-1.5 py-0.5 text-xs text-muted">{id}</span>;
}

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section aria-labelledby={id} className="rounded-2xl border border-line bg-surface p-5">
      <h2 id={id} className="text-lg font-semibold">{title}</h2>
      <ul className="mt-3 space-y-3">{children}</ul>
    </section>
  );
}

const item = "flex flex-wrap items-center gap-2 text-sm";

export default function GuidelinesPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight md:text-5xl">Brand guidelines</h1>
        <p className="mt-3 text-sm text-muted">
          Rules for <span className="font-semibold text-ink">{g.name}</span>. Read-only: editing rules is planned for a later release.
        </p>
      </div>

      <SampleDataNotice>These rules are examples, not a real brand’s guidelines.</SampleDataNotice>

      <Section id="voice" title="Voice and tone">
        {g.voice.map((r) => (
          <li key={r.rule_id} className={item}><RuleId id={r.rule_id} /> {r.text}</li>
        ))}
      </Section>

      <Section id="preferred" title="Preferred terminology">
        {g.preferred_terms.map((r) => (
          <li key={r.rule_id} className={item}>
            <RuleId id={r.rule_id} /> Use <strong>{r.use}</strong> instead of <strong>{r.instead_of}</strong>
          </li>
        ))}
      </Section>

      <Section id="banned" title="Banned or discouraged terms">
        {g.banned_terms.map((r) => (
          <li key={r.rule_id} className={item}>
            <RuleId id={r.rule_id} /> <strong>{r.term}</strong>: {r.reason}
          </li>
        ))}
      </Section>

      <Section id="required" title="Required phrases and disclaimers">
        {g.required_phrases.map((r) => (
          <li key={r.rule_id} className={item}>
            <RuleId id={r.rule_id} /> <strong>{r.phrase}</strong> ({r.when})
          </li>
        ))}
      </Section>

      <Section id="facts" title="Approved facts">
        {g.facts.map((r) => (
          <li key={r.rule_id} className="text-sm">
            <div className={item}><RuleId id={r.rule_id} /> {r.text}</div>
            <p className="mt-1 text-xs text-muted">
              Source: {r.source} · {r.expires ? `Expires: ${r.expires}` : "No expiry set"}
            </p>
          </li>
        ))}
      </Section>
    </div>
  );
}