"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { usePortfolio } from "../providers/PortfolioProvider";

const navItems = [
  { label: "Dashboard", href: "/" },
  { label: "Explore", href: "/explore" },
  { label: "Portfolio", href: "/portfolio" },
  { label: "About", href: "/about" },
];

function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setIsDark(document.documentElement.classList.contains('dark'));
  }, []);

  const toggleTheme = () => {
    const newIsDark = !isDark;
    setIsDark(newIsDark);
    if (newIsDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('chainscore-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('chainscore-theme', 'light');
    }
  };

  if (!mounted) {
    return <div className="w-9 h-9" />;
  }

  return (
    <button
      onClick={toggleTheme}
      className="w-9 h-9 flex items-center justify-center rounded border border-[var(--border)] hover:bg-[var(--card-hover)] transition-colors"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {isDark ? (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      ) : (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      )}
    </button>
  );
}

export default function Nav() {
  const pathname = usePathname();
  const { portfolio, sidebarOpen, setSidebarOpen } = usePortfolio();

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--border)]" style={{ background: 'var(--background)' }}>
      <div className="max-w-[1400px] mx-auto px-6">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <span className="text-lg font-mono font-bold tracking-tight">
              Chain<span style={{ color: 'var(--primary)' }}>Score</span>
            </span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-1.5 text-[13px] font-medium transition-colors rounded ${
                    isActive
                      ? "bg-[var(--card-hover)]"
                      : "hover:bg-[var(--card-hover)]"
                  }`}
                  style={{ color: isActive ? 'var(--foreground)' : 'var(--muted)' }}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-2">
            <a
              href="https://github.com/deerws/ChainScore"
              target="_blank"
              rel="noreferrer"
              className="hidden sm:block text-[13px] transition-opacity hover:opacity-70"
              style={{ color: 'var(--muted)' }}
            >
              GitHub ↗
            </a>
            {/* Portfolio toggle — always visible, badge shows count */}
            <button
              onClick={() => setSidebarOpen((o) => !o)}
              className="relative flex items-center gap-1.5 px-2.5 py-1.5 text-[12px] font-medium rounded border transition-colors"
              style={{
                borderColor: sidebarOpen ? 'var(--primary)' : 'var(--border)',
                color: sidebarOpen ? 'var(--primary)' : 'var(--muted)',
                background: sidebarOpen ? 'rgba(37,99,235,0.08)' : 'transparent',
              }}
              aria-label="Toggle portfolio panel"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="7" width="20" height="14" rx="2"/>
                <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
              </svg>
              <span className="hidden sm:inline">Portfolio</span>
              {portfolio.length > 0 && (
                <span
                  className="flex items-center justify-center w-4 h-4 rounded-full text-[9px] font-bold"
                  style={{ background: 'var(--primary)', color: '#fff' }}
                >
                  {portfolio.length}
                </span>
              )}
            </button>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
}
