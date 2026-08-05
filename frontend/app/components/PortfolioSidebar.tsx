"use client";

import { useState } from "react";
import { usePortfolio } from "../providers/PortfolioProvider";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function PortfolioSidebar() {
  const { portfolio, sidebarOpen, setSidebarOpen, removeWallet, setWeight, normalize } =
    usePortfolio();
  const [exportingPdf, setExportingPdf] = useState(false);

  if (!sidebarOpen) return null;

  const totalWeight = parseFloat(
    portfolio.reduce((s, p) => s + p.weight, 0).toFixed(1)
  );
  const weightedScore =
    portfolio.length > 0
      ? Math.round(portfolio.reduce((s, p) => s + (p.score * p.weight) / 100, 0))
      : null;
  const weightedPd =
    portfolio.length > 0
      ? portfolio.reduce((s, p) => s + (p.pd * p.weight) / 100, 0)
      : null;

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
    <aside
      className="hidden lg:flex lg:order-2 flex-col w-72 shrink-0 border-l sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto"
      style={{ background: "var(--card)", borderColor: "var(--border)" }}
    >
      {/* Header */}
      <div
        className="p-4 border-b flex items-center justify-between shrink-0"
        style={{ borderColor: "var(--border)" }}
      >
        <p
          className="text-xs font-semibold uppercase tracking-wider"
          style={{ color: "var(--muted)" }}
        >
          Portfolio · {portfolio.length}
        </p>
        <button
          onClick={() => setSidebarOpen(false)}
          className="text-xs hover:opacity-70"
          style={{ color: "var(--muted)" }}
        >
          ✕
        </button>
      </div>

      {portfolio.length === 0 ? (
        <p className="text-xs p-4" style={{ color: "var(--muted)" }}>
          Analyze a wallet and click &ldquo;+ Portfolio&rdquo; to start tracking.
        </p>
      ) : (
        <div className="flex flex-col flex-1">
          {/* Wallet list */}
          {portfolio.map((item) => (
            <div
              key={item.address}
              className="p-4 border-b"
              style={{ borderColor: "var(--border)" }}
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className="text-xs font-mono"
                  style={{ color: "var(--foreground)" }}
                >
                  {item.address.slice(0, 6)}…{item.address.slice(-4)}
                </span>
                <button
                  onClick={() => removeWallet(item.address)}
                  className="text-[10px] hover:opacity-70"
                  style={{ color: "var(--muted)" }}
                >
                  ✕
                </button>
              </div>
              <div className="flex items-center justify-between mb-3">
                <span
                  className="text-lg font-bold"
                  style={{ color: "var(--foreground)" }}
                >
                  {item.score}
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
            className="mx-4 mb-2 py-1 text-[10px] rounded border hover:opacity-70 transition-opacity"
            style={{ borderColor: "var(--border)", color: "var(--muted)" }}
          >
            Normalize to 100%
          </button>

          {/* Weighted aggregate */}
          {weightedScore !== null && (
            <div
              className="mx-4 mb-3 p-3 rounded border"
              style={{
                background: "var(--background)",
                borderColor: "var(--border)",
              }}
            >
              <p
                className="text-[10px] uppercase tracking-wider mb-3"
                style={{ color: "var(--muted)" }}
              >
                Weighted Portfolio
              </p>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span style={{ color: "var(--muted)" }}>Avg Score</span>
                  <span
                    className="font-mono font-semibold"
                    style={{ color: "var(--foreground)" }}
                  >
                    {weightedScore}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span style={{ color: "var(--muted)" }}>Weighted PD</span>
                  <span
                    className="font-mono font-semibold"
                    style={{ color: "var(--foreground)" }}
                  >
                    {((weightedPd ?? 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span style={{ color: "var(--muted)" }}>Wallets</span>
                  <span className="font-mono" style={{ color: "var(--muted)" }}>
                    {portfolio.length}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Export PDF */}
          <button
            onClick={exportPdf}
            disabled={exportingPdf || !portfolio.length}
            className="mx-4 mb-4 py-2 text-xs rounded font-semibold transition-opacity hover:opacity-80 disabled:opacity-40 flex items-center justify-center gap-1.5"
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
    </aside>
  );
}
