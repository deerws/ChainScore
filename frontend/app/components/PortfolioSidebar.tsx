"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { usePortfolio } from "../providers/PortfolioProvider";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function PortfolioSidebar() {
  const router = useRouter();
  const { portfolio, sidebarOpen, setSidebarOpen, removeWallet, setWeight, normalize } =
    usePortfolio();

  const [exportingPdf, setExportingPdf] = useState(false);
  const [quickAddr, setQuickAddr] = useState("");

  const totalWeight = parseFloat(portfolio.reduce((s, p) => s + p.weight, 0).toFixed(1));
  const weightedScore =
    portfolio.length > 0
      ? Math.round(portfolio.reduce((s, p) => s + (p.score * p.weight) / 100, 0))
      : null;
  const weightedPd =
    portfolio.length > 0
      ? portfolio.reduce((s, p) => s + (p.pd * p.weight) / 100, 0)
      : null;

  const quickAddrValid =
    quickAddr.startsWith("0x") && quickAddr.trim().length === 42;

  function handleQuickAnalyze() {
    const addr = quickAddr.trim();
    if (!addr.startsWith("0x") || addr.length !== 42) return;
    localStorage.setItem("cs_auto_analyze", addr);
    setQuickAddr("");
    router.push("/");
  }

  async function exportPdf() {
    if (!portfolio.length || exportingPdf) return;
    setExportingPdf(true);
    try {
      const res = await fetch(`${API_BASE}/v1/report/portfolio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          wallets: portfolio.map((p) => ({
            address: p.address,
            score: p.score,
            pd: p.pd,
            risk_tier: p.risk_tier,
            weight: p.weight,
          })),
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail ?? res.statusText);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "chainscore_portfolio.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(
        `PDF export failed: ${err instanceof Error ? err.message : String(err)}`
      );
    } finally {
      setExportingPdf(false);
    }
  }

  function tierColor(tier: string) {
    if (tier === "very_low" || tier === "low") return "var(--positive)";
    if (tier === "medium") return "var(--warning)";
    return "var(--negative)";
  }
  function tierBg(tier: string) {
    if (tier === "very_low" || tier === "low") return "rgba(22,101,52,0.12)";
    if (tier === "medium") return "rgba(217,119,6,0.12)";
    return "rgba(185,28,28,0.12)";
  }

  return (
    <>
      {/* Mobile backdrop */}
      <div
        className="fixed inset-0 z-30 bg-black/30 transition-opacity duration-300 lg:hidden"
        style={{
          opacity: sidebarOpen ? 1 : 0,
          pointerEvents: sidebarOpen ? "auto" : "none",
        }}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Fixed panel — full-width on mobile, 320px on sm+ */}
      <div
        className="fixed right-0 top-14 bottom-0 w-full sm:w-80 z-40 flex flex-col border-l shadow-2xl transition-transform duration-300 ease-in-out"
        style={{
          background: "var(--card)",
          borderColor: "var(--border)",
          transform: sidebarOpen ? "translateX(0)" : "translateX(100%)",
        }}
      >
        {/* ── Header ── */}
        <div
          className="shrink-0 flex items-center justify-between px-4 py-3 border-b"
          style={{ borderColor: "var(--border)" }}
        >
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--muted)" }}>
              Portfolio
            </span>
            {portfolio.length > 0 && (
              <span
                className="w-4 h-4 rounded-full text-[9px] flex items-center justify-center font-bold"
                style={{ background: "var(--primary)", color: "#fff" }}
              >
                {portfolio.length}
              </span>
            )}
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="w-6 h-6 flex items-center justify-center rounded hover:bg-[var(--card-hover)] text-xs transition-colors"
            style={{ color: "var(--muted)" }}
          >
            ✕
          </button>
        </div>

        {/* ── Quick Analyze ── */}
        <div className="shrink-0 p-3 border-b" style={{ borderColor: "var(--border)" }}>
          <p className="text-[10px] uppercase tracking-wider mb-2" style={{ color: "var(--muted)" }}>
            Analyze Wallet
          </p>
          <div className="flex gap-1.5">
            <input
              type="text"
              placeholder="0x..."
              value={quickAddr}
              onChange={(e) => setQuickAddr(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleQuickAnalyze()}
              className="flex-1 min-w-0 px-2 py-1.5 text-xs font-mono rounded border focus:outline-none"
              style={{
                background: "var(--background)",
                borderColor: "var(--border)",
                color: "var(--foreground)",
              }}
            />
            <button
              onClick={handleQuickAnalyze}
              disabled={!quickAddrValid}
              title="Go to Dashboard and analyze"
              className="shrink-0 px-3 py-1.5 text-xs font-bold rounded disabled:opacity-30 transition-opacity hover:opacity-80"
              style={{ background: "var(--primary)", color: "#fff" }}
            >
              →
            </button>
          </div>
          <p className="text-[10px] mt-1" style={{ color: "var(--muted)" }}>
            Opens Dashboard with result
          </p>
        </div>

        {/* ── Wallet List (scrollable) ── */}
        <div className="flex-1 overflow-y-auto">
          {portfolio.length === 0 ? (
            <div className="p-4 text-center">
              <p className="text-xs mb-1" style={{ color: "var(--muted)" }}>
                No wallets in portfolio yet.
              </p>
              <p className="text-[11px]" style={{ color: "var(--muted)" }}>
                Score a wallet on Dashboard and click{" "}
                <strong style={{ color: "var(--foreground)" }}>+ Portfolio</strong>.
              </p>
            </div>
          ) : (
            <>
              {portfolio.map((item) => (
                <div
                  key={item.address}
                  className="p-4 border-b"
                  style={{ borderColor: "var(--border)" }}
                >
                  {/* Address + remove */}
                  <div className="flex items-center justify-between mb-1.5">
                    <button
                      onClick={() => {
                        setQuickAddr(item.address);
                      }}
                      title="Copy to analyze input"
                      className="text-xs font-mono hover:opacity-70 transition-opacity text-left"
                      style={{ color: "var(--foreground)" }}
                    >
                      {item.address.slice(0, 6)}…{item.address.slice(-4)}
                    </button>
                    <button
                      onClick={() => removeWallet(item.address)}
                      className="text-[10px] hover:opacity-70 ml-2"
                      style={{ color: "var(--muted)" }}
                    >
                      ✕
                    </button>
                  </div>

                  {/* Score + tier */}
                  <div className="flex items-center justify-between mb-3">
                    <span
                      className="text-xl font-bold"
                      style={{ color: "var(--foreground)" }}
                    >
                      {item.score}
                    </span>
                    <div className="flex items-center gap-2">
                      <span
                        className="text-[10px]"
                        style={{ color: "var(--muted)" }}
                      >
                        PD {(item.pd * 100).toFixed(1)}%
                      </span>
                      <span
                        className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded"
                        style={{
                          color: tierColor(item.risk_tier),
                          background: tierBg(item.risk_tier),
                        }}
                      >
                        {item.risk_tier.replace("_", " ")}
                      </span>
                    </div>
                  </div>

                  {/* Weight input */}
                  <div className="flex items-center gap-2">
                    <label
                      className="text-[10px] uppercase tracking-wider shrink-0"
                      style={{ color: "var(--muted)" }}
                    >
                      Weight&nbsp;%
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={parseFloat(item.weight.toFixed(1))}
                      onChange={(e) =>
                        setWeight(item.address, parseFloat(e.target.value) || 0)
                      }
                      onBlur={normalize}
                      className="w-full px-2 py-1 text-xs font-mono rounded border focus:outline-none"
                      style={{
                        background: "var(--background)",
                        borderColor: "var(--border)",
                        color: "var(--foreground)",
                      }}
                    />
                  </div>
                </div>
              ))}

              {/* Weight total */}
              <div
                className="px-4 py-2 flex items-center justify-between text-[10px]"
                style={{
                  color:
                    Math.abs(totalWeight - 100) < 0.2
                      ? "var(--positive)"
                      : "var(--warning)",
                }}
              >
                <span>Total weight</span>
                <span className="font-mono font-semibold">{totalWeight.toFixed(1)}%</span>
              </div>

              <button
                onClick={normalize}
                className="mx-4 mb-2 w-[calc(100%-2rem)] py-1 text-[10px] rounded border hover:opacity-70 transition-opacity"
                style={{ borderColor: "var(--border)", color: "var(--muted)" }}
              >
                Normalize to 100%
              </button>
            </>
          )}
        </div>

        {/* ── Footer: aggregate + export (always visible at bottom) ── */}
        {weightedScore !== null && (
          <div
            className="shrink-0 border-t"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="px-4 pt-3 pb-1">
              <p
                className="text-[10px] uppercase tracking-wider mb-2"
                style={{ color: "var(--muted)" }}
              >
                Weighted Portfolio
              </p>
              <div className="grid grid-cols-3 gap-2 text-center mb-3">
                <div>
                  <p className="text-base font-bold" style={{ color: "var(--foreground)" }}>
                    {weightedScore}
                  </p>
                  <p className="text-[9px] uppercase" style={{ color: "var(--muted)" }}>
                    Score
                  </p>
                </div>
                <div>
                  <p className="text-base font-bold" style={{ color: "var(--foreground)" }}>
                    {((weightedPd ?? 0) * 100).toFixed(1)}%
                  </p>
                  <p className="text-[9px] uppercase" style={{ color: "var(--muted)" }}>
                    Wtd PD
                  </p>
                </div>
                <div>
                  <p className="text-base font-bold" style={{ color: "var(--foreground)" }}>
                    {portfolio.length}
                  </p>
                  <p className="text-[9px] uppercase" style={{ color: "var(--muted)" }}>
                    Wallets
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={exportPdf}
              disabled={exportingPdf || !portfolio.length}
              className="mx-4 mb-4 w-[calc(100%-2rem)] py-2 text-xs rounded font-semibold transition-opacity hover:opacity-80 disabled:opacity-40 flex items-center justify-center gap-1.5"
              style={{ background: "var(--primary)", color: "#fff" }}
            >
              {exportingPdf ? (
                <>
                  <span className="w-3 h-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  Compiling PDF…
                </>
              ) : (
                "Export PDF Report"
              )}
            </button>
          </div>
        )}
      </div>
    </>
  );
}
