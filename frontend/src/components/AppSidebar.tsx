"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/guidelines", label: "Brand Guidelines" },
  { href: "/review", label: "Draft Review" },
  { href: "/approvals", label: "Approvals" },
  { href: "/history", label: "Revision History" },
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
              <Link
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`block whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium ${
                  active ? "bg-maroon text-white" : "text-ink hover:bg-surface-2"
                }`}
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}