// Display helpers for raw API values. Display only; never changes the data.

export function shortReviewId(id: string): string {
  return id.replace(/^review_/, "").slice(0, 8);
}

const STATUS_TEXT: Record<string, string> = {
  draft: "Draft",
  in_review: "In Review",
  changes_requested: "Changes Requested",
  needs_human_review: "Needs Human Review",
  approved: "Approved",
};

// Plain-text twin of DisplayStatus, for places that can't render a badge (e.g. <option>).
// A clean review (0 findings) is NOT shown as Approved until a human approves.
export function statusText(status: string, findingCount: number): string {
  if (status === "approved" && findingCount === 0) return "Awaiting Human Approval";
  return STATUS_TEXT[status] ?? status;
}

export function findingsText(count: number, needHuman: number): string {
  const f = `${count} ${count === 1 ? "finding" : "findings"}`;
  return needHuman > 0 ? `${f}, ${needHuman} need human review` : `${f}, none need human review`;
}