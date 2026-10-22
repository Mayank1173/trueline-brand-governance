export default function AppHeader() {
  return (
    <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line bg-surface px-4 py-3 md:px-8">
      <p className="text-sm text-muted">
        Workspace: <span className="font-semibold text-ink">Sample Brand (mock)</span>
      </p>
      <span className="rounded-full border border-maroon-soft px-3 py-0.5 text-xs font-semibold text-maroon-soft">
        Sample data: backend not connected
      </span>
    </header>
  );
}