import RevisionHistory from "@/components/RevisionHistory";
import SampleDataNotice from "@/components/SampleDataNotice";
import { SAMPLE_DRAFTS, SAMPLE_REVISIONS } from "@/lib/mock/sampleData";

export default function HistoryPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight md:text-5xl">Revision history</h1>
        <p className="mt-3 text-sm text-muted">
          Draft: <span className="font-semibold text-ink">{SAMPLE_DRAFTS[0].title}</span>
        </p>
      </div>
      <SampleDataNotice>These are sample records, not a real audit trail.</SampleDataNotice>
      <RevisionHistory revisions={SAMPLE_REVISIONS} />
    </div>
  );
}