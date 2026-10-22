"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard", label: "Dashboard", ready: false },
  { href: "/guidelines", label: "Brand Guidelines", ready: false },
  { href: "/review", label: "Draft Review", ready: true },
  { href: "/approvals", label: "Approvals", ready: false },
  { href: "/history", label: "Revision History", ready: false },
];

export default function AppSidebar() {
  const path = usePathname();
  return (
    <nav aria-label="Main" className="border-b border-line bg-surface md:w-60 md:border-b-0 md:border-r">
      <div className="px-5 py-4 text-xl font-bold tracking-tight text-ink">
        True<span className="text-maroon-soft">line</span>
      </div>
      <ul className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:overflow-visible">
        {NAV.map((item) => {
          const active = path === item.href;
          return (
            <li key={item.href}>
              {item.ready ? (
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`block whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium ${
                    active ? "bg-maroon text-white" : "text-ink hover:bg-surface-2"
                  }`}
                >
                  {item.label}
                </Link>
              ) : (
                <span aria-disabled="true" className="block whitespace-nowrap rounded-full px-4 py-2 text-sm text-muted">
                  {item.label} <span className="text-xs">(soon)</span>
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </nav>
  );
}