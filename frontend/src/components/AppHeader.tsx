import { isLive } from "@/lib/api";

export default function AppHeader() {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-line bg-bg px-4 py-4 md:px-8">
      <div className="min-w-0">
        <p className="eyebrow">Trueline / Workspace</p>

        <p className="mt-1 text-sm text-muted">
          Brand{" "}
          <span className="font-semibold text-ink">
            Trueline
          </span>
        </p>
      </div>

      <div
        role="status"
        className="inline-flex items-center gap-2 rounded-md border border-line bg-surface px-3 py-2 text-xs text-muted"
      >
        <span
          aria-hidden="true"
          className="h-2 w-2 rounded-full bg-maroon"
        />

        <span>{isLive ? "Live backend configured" : "Demo mode · Mock data enabled"}</span>
      </div>
    </header>
  );
}
