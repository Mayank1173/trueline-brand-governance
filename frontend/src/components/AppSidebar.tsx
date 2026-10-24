
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard", label: "Dashboard", number: "01" },
  { href: "/guidelines", label: "Brand Guidelines", number: "02" },
  { href: "/review", label: "Draft Review", number: "03" },
  { href: "/approvals", label: "Approvals", number: "04" },
  { href: "/history", label: "Revision History", number: "05" },
];

export default function AppSidebar() {
  const path = usePathname();

  return (
    <nav
      aria-label="Main"
      className="flex shrink-0 flex-col border-b border-line bg-surface md:min-h-screen md:w-60 md:border-b-0 md:border-r"
    >
      <Link
        href="/dashboard"
        className="flex items-center gap-3 px-5 py-5 no-underline"
        aria-label="Trueline home"
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-maroon text-sm font-bold text-[#0d0f0d]">
          T.
        </span>

        <span className="text-xl font-bold tracking-[-0.07em] text-ink">
          true<span className="text-maroon">line</span>
          <span className="text-maroon">.</span>
        </span>
      </Link>

      <div className="hidden px-5 pb-3 pt-5 md:block">
        <p className="eyebrow">Workspace</p>
      </div>

      <ul className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-1 md:flex-col md:overflow-visible">
        {NAV.map((item) => {
          const active =
            path === item.href || path.startsWith(`${item.href}/`);

          return (
            <li key={item.href} className="shrink-0">
              <Link
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center gap-3 rounded-md border-l-2 px-3 py-3 text-sm font-medium no-underline transition-colors ${
                  active
                    ? "border-maroon bg-surface-2 text-maroon"
                    : "border-transparent text-muted hover:bg-surface-2 hover:text-ink"
                }`}
              >
                <span
                  className={`font-mono text-[10px] ${
                    active ? "text-maroon" : "text-muted"
                  }`}
                >
                  {item.number}
                </span>

                <span>{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>

      <div className="hidden border-t border-line px-5 py-4 md:block">
        <p className="eyebrow">Brand governance</p>
        <p className="mt-2 text-xs leading-5 text-muted">
          Review before you publish.
        </p>
      </div>
    </nav>
  );
}
