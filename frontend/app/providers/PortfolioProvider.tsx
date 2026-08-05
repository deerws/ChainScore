"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

export interface PortfolioItem {
  address: string;
  score: number;
  pd: number;
  risk_tier: string;
  weight: number;
}

interface PortfolioCtx {
  portfolio: PortfolioItem[];
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean | ((prev: boolean) => boolean)) => void;
  addWallet: (item: Omit<PortfolioItem, "weight">) => void;
  removeWallet: (addr: string) => void;
  setWeight: (addr: string, w: number) => void;
  normalize: () => void;
  isInPortfolio: (addr: string) => boolean;
}

const Ctx = createContext<PortfolioCtx | null>(null);

export function usePortfolio() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("usePortfolio must be inside PortfolioProvider");
  return ctx;
}

function normalizeWeights(items: PortfolioItem[]): PortfolioItem[] {
  if (!items.length) return items;
  const total = items.reduce((s, p) => s + p.weight, 0);
  if (total === 0) return items.map((p) => ({ ...p, weight: 100 / items.length }));
  return items.map((p) => ({
    ...p,
    weight: parseFloat(((p.weight / total) * 100).toFixed(1)),
  }));
}

export function PortfolioProvider({ children }: { children: ReactNode }) {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Restore once on mount — lives in layout so it never re-runs on page navigation
  useEffect(() => {
    try {
      const saved = localStorage.getItem("cs_portfolio");
      if (saved) {
        const p = JSON.parse(saved);
        if (Array.isArray(p) && p.length > 0) {
          setPortfolio(p);
          setSidebarOpen(true);
        }
      }
    } catch {}
  }, []);

  const persist = useCallback((items: PortfolioItem[]) => {
    localStorage.setItem("cs_portfolio", JSON.stringify(items));
  }, []);

  const addWallet = useCallback(
    (item: Omit<PortfolioItem, "weight">) => {
      setPortfolio((prev) => {
        if (prev.some((p) => p.address.toLowerCase() === item.address.toLowerCase())) {
          setSidebarOpen(true);
          return prev;
        }
        const next = normalizeWeights([...prev, { ...item, weight: 100 }]);
        persist(next);
        setSidebarOpen(true);
        return next;
      });
    },
    [persist]
  );

  const removeWallet = useCallback(
    (addr: string) => {
      setPortfolio((prev) => {
        const next = normalizeWeights(prev.filter((p) => p.address !== addr));
        persist(next);
        if (next.length === 0) setSidebarOpen(false);
        return next;
      });
    },
    [persist]
  );

  const setWeight = useCallback((addr: string, w: number) => {
    setPortfolio((prev) =>
      prev.map((p) => (p.address === addr ? { ...p, weight: Math.max(0, w) } : p))
    );
  }, []);

  const normalize = useCallback(() => {
    setPortfolio((prev) => {
      const next = normalizeWeights(prev);
      persist(next);
      return next;
    });
  }, [persist]);

  const isInPortfolio = useCallback(
    (addr: string) =>
      portfolio.some((p) => p.address.toLowerCase() === addr.toLowerCase()),
    [portfolio]
  );

  return (
    <Ctx.Provider
      value={{
        portfolio,
        sidebarOpen,
        setSidebarOpen,
        addWallet,
        removeWallet,
        setWeight,
        normalize,
        isInPortfolio,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}
