export default function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-line bg-surface p-6 text-sm">
      <p className="font-semibold text-ink">{title}</p>
      <p className="mt-1 text-muted">{description}</p>
    </div>
  );
}