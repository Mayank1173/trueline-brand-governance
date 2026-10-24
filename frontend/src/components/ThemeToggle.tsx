"use client";
import { useSyncExternalStore } from "react";

type Theme = "dark" | "light";

function subscribe(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  return () => observer.disconnect();
}

function getSnapshot(): Theme {
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

function getServerSnapshot(): Theme | null {
  return null;
}

export default function ThemeToggle() {
  const theme = useSyncExternalStore<Theme | null>(subscribe, getSnapshot, getServerSnapshot);

  function toggle() {
    const next: Theme = theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch {
      // storage blocked: theme still changes for this session
    }
  }

  const isLight = theme === "light";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={isLight}
      aria-label="Light mode"
      className="rounded-full border border-line px-3 py-1 text-xs font-semibold text-ink hover:bg-surface-2"
    >
      {theme === null ? "Theme" : isLight ? "☀ Light" : "☾ Dark"}
    </button>
  );
}