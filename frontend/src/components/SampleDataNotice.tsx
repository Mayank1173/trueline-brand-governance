export default function SampleDataNotice({ children }: { children?: React.ReactNode }) {
  return (
    <p role="note" className="rounded-xl border border-maroon-soft/60 bg-maroon/15 p-3 text-sm text-ink">
      <strong>Sample data.</strong>{" "}
      {children ?? "The backend isn’t connected. Nothing on this page is a real record."}
    </p>
  );
}