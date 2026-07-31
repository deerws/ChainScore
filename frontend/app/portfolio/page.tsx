"use client";

import { useState, useCallback } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
} from "recharts";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────

interface TierBreakdown {
  tier: string;
  count: number;
  pct: number;
  avg_pd: number;
}

interface PortfolioStats {
  n_wallets: number;
  n_scored: number;
  n_failed: number;
  avg_score: number;
  avg_pd: number;
  weighted_pd: number;
  var_95: number;
  cvar_95: number;
  concentration_high_risk: number;
  tier_breakdown: TierBreakdown[];
  model_version: string;
  scored_at: string;
}

interface WalletResult {
  wallet_address: string;
  score: number | null;
  risk_tier: string | null;
  probability_of_default: number | null;
  error: string | null;
}

interface WalletRow {
  id: string;
  address: string;
}

// ── Constants ──────────────────────────────────────────────────────────────

const TIER_CONFIG: Record<string, { label: string; color: string }> = {
  very_low:  { label: "Very Low",  color: "var(--positive)" },
  low:       { label: "Low",       color: "#22c55e" },
  medium:    { label: "Medium",    color: "var(--warning)" },
  high:      { label: "High",      color: "#f97316" },
  very_high: { label: "Very High", color: "var(--negative)" },
};

const TIER_ORDER = ["very_low", "low", "medium", "high", "very_high"];

const DEMO_WALLETS = [
  "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
  "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B",
  "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE",
];

let nextId = 1;
function makeRow(address = ""): WalletRow {
  return { id: String(nextId++), address };
}

// ── Sub-components ─────────────────────────────────────────────────────────

function KpiCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub?: string;
  color?: string;
}) {
  return (
    <div
      className="rounded border p-4"
      style={{ background: "var(--card)", borderColor: "var(--border)" }}
    >
      <p className="text-[11px] uppercase tracking-widest mb-1" style={{ color: "var(--muted)" }}>
        {label}
      </p>
      <p className="text-2xl font-mono font-bold" style={{ color: color ?? "var(--foreground)" }}>
        {value}
      </p>
      {sub && (
        <p className="text-[11px] mt-1" style={{ color: "var(--muted)" }}>
          {sub}
        </p>
      )}
    </div>
  );
}

function TierBadge({ tier }: { tier: string }) {
  const cfg = TIER_CONFIG[tier] ?? { label: tier, color: "var(--muted)" };
  return (
    <span
      className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded"
      style={{
        color: cfg.color,
        background: `color-mix(in srgb, ${cfg.color} 12%, transparent)`,
      }}
    >
      {cfg.label}
    </span>
  );
}

function RiskMeter({ value, label }: { value: number; label: string }) {
  const pct = Math.min(value * 100, 100);
  const color =
    pct < 30 ? "var(--positive)" : pct < 55 ? "var(--warning)" : "var(--negative)";
  return (
    <div>
      <div className="flex justify-between text-[11px] mb-1" style={{ color: "var(--muted)" }}>
        <span>{label}</span>
        <span style={{ color: "var(--foreground)", fontFamily: "var(--font-mono)" }}>
          {(pct).toFixed(1)}%
        </span>
      </div>
      <div className="h-1.5 rounded-full" style={{ background: "var(--border)" }}>
        <div
          className="h-1.5 rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

// ── Custom tooltip for Recharts ────────────────────────────────────────────

function DonutTooltip({ active, payload }: { active?: boolean; payload?: { payload: TierBreakdown }[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const cfg = TIER_CONFIG[d.tier] ?? { label: d.tier, color: "var(--muted)" };
  return (
    <div
      className="rounded border px-3 py-2 text-xs shadow-lg"
      style={{ background: "var(--card)", borderColor: "var(--border)", color: "var(--foreground)" }}
    >
      <p className="font-semibold mb-1" style={{ color: cfg.color }}>{cfg.label}</p>
      <p>{d.count} wallet{d.count !== 1 ? "s" : ""} · {d.pct.toFixed(1)}%</p>
      <p style={{ color: "var(--muted)" }}>Avg PD {(d.avg_pd * 100).toFixed(1)}%</p>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function PortfolioPage() {
  const [rows, setRows] = useState<WalletRow[]>([makeRow()]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PortfolioStats | null>(null);
  const [walletResults, setWalletResults] = useState<WalletResult[]>([]);

  // Wallet list helpers
  const updateRow = useCallback((id: string, address: string) => {
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, address } : r)));
  }, []);

  const addRow = () => {
    if (rows.length >= 20) return;
    setRows((prev) => [...prev, makeRow()]);
  };

  const removeRow = (id: string) => {
    setRows((prev) => (prev.length > 1 ? prev.filter((r) => r.id !== id) : prev));
  };

  const loadDemo = () => {
    setRows(DEMO_WALLETS.map((a) => makeRow(a)));
    setResult(null);
    setError(null);
    setWalletResults([]);
  };

  // API call
  const analyze = async () => {
    const addresses = rows.map((r) => r.address.trim()).filter(Boolean);
    if (addresses.length < 2) {
      setError("Enter at least 2 wallet addresses.");
      return;
    }
    for (const a of addresses) {
      if (!a.startsWith("0x") || a.length !== 42) {
        setError(`Invalid address: ${a}`);
        return;
      }
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setWalletResults([]);

    try {
      // Run portfolio aggregation and per-wallet batch in parallel when ≤20 wallets
      const portfolioFetch = fetch(`${API_BASE}/v1/portfolio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wallet_addresses: addresses, name: "Portfolio Analysis" }),
      });

      const batchFetch =
        addresses.length <= 20
          ? fetch(`${API_BASE}/v1/batch`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ wallet_addresses: addresses }),
            })
          : Promise.resolve(null);

      const [portfolioResp, batchResp] = await Promise.all([portfolioFetch, batchFetch]);

      if (!portfolioResp.ok) {
        const detail = await portfolioResp.json().catch(() => ({}));
        throw new Error(detail?.detail ?? `API error ${portfolioResp.status}`);
      }
      const portfolioData: PortfolioStats = await portfolioResp.json();
      setResult(portfolioData);

      if (batchResp?.ok) {
        const batchData = await batchResp.json();
        setWalletResults(batchData.results ?? []);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  };

  // Derived display values
  const sortedTiers = result
    ? TIER_ORDER.map((t) => result.tier_breakdown.find((b) => b.tier === t)).filter(Boolean) as TierBreakdown[]
    : [];

  const scoreColor =
    !result ? "var(--foreground)"
    : result.avg_score >= 650 ? "var(--positive)"
    : result.avg_score >= 450 ? "var(--warning)"
    : "var(--negative)";

  return (
    <main className="max-w-[1200px] mx-auto px-6 py-8">
      {/* ── Page header ── */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-xl font-semibold tracking-tight">Portfolio Builder</h1>
          <span
            className="text-[9px] uppercase tracking-widest px-2 py-0.5 rounded font-semibold"
            style={{ color: "var(--primary)", background: "rgba(37,99,235,0.10)" }}
          >
            Beta
          </span>
        </div>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Score multiple wallets at once and view aggregate DeFi credit risk metrics —
          VaR 95%, CVaR 95%, and tier composition.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-6">
        {/* ── LEFT: wallet input panel ── */}
        <aside>
          <div
            className="rounded border"
            style={{ background: "var(--card)", borderColor: "var(--border)" }}
          >
            <div
              className="flex items-center justify-between px-4 py-3 border-b"
              style={{ borderColor: "var(--border)" }}
            >
              <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--muted)" }}>
                Wallets ({rows.length}/20)
              </span>
              <button
                onClick={loadDemo}
                className="text-[11px] transition-opacity hover:opacity-70"
                style={{ color: "var(--primary)" }}
              >
                Load demo
              </button>
            </div>

            <div className="p-4 space-y-2">
              {rows.map((row, idx) => (
                <div key={row.id} className="flex items-center gap-2">
                  <span
                    className="text-[10px] font-mono w-5 text-right flex-shrink-0"
                    style={{ color: "var(--muted)" }}
                  >
                    {idx + 1}
                  </span>
                  <input
                    type="text"
                    placeholder="0x..."
                    value={row.address}
                    onChange={(e) => updateRow(row.id, e.target.value)}
                    className="flex-1 text-xs font-mono px-2 py-1.5 rounded border outline-none transition-colors min-w-0"
                    style={{
                      background: "var(--background)",
                      borderColor: "var(--border)",
                      color: "var(--foreground)",
                    }}
                    onFocus={(e) =>
                      (e.currentTarget.style.borderColor = "var(--primary)")
                    }
                    onBlur={(e) =>
                      (e.currentTarget.style.borderColor = "var(--border)")
                    }
                  />
                  <button
                    onClick={() => removeRow(row.id)}
                    disabled={rows.length === 1}
                    className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded transition-opacity hover:opacity-70 disabled:opacity-20"
                    style={{ color: "var(--muted)" }}
                    aria-label="Remove wallet"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>

            <div
              className="px-4 pb-4 flex items-center gap-2 border-t pt-3"
              style={{ borderColor: "var(--border)" }}
            >
              <button
                onClick={addRow}
                disabled={rows.length >= 20}
                className="flex-1 text-xs py-1.5 rounded border transition-colors hover:bg-[var(--card-hover)] disabled:opacity-30"
                style={{ borderColor: "var(--border)", color: "var(--muted)" }}
              >
                + Add wallet
              </button>
            </div>

            <div className="px-4 pb-4">
              <button
                onClick={analyze}
                disabled={loading}
                className="w-full py-2.5 rounded text-sm font-semibold transition-colors disabled:opacity-50"
                style={{
                  background: "var(--primary)",
                  color: "white",
                }}
              >
                {loading ? "Analyzing…" : "Analyze Portfolio →"}
              </button>
            </div>
          </div>

          {/* Methodology note */}
          <p className="text-[11px] mt-3 leading-relaxed" style={{ color: "var(--muted)" }}>
            Calls <code style={{ color: "var(--muted)" }}>/v1/portfolio</code> — scores each
            wallet individually then aggregates. VaR 95% is the PD at the 95th-percentile
            wallet; CVaR 95% is the mean PD of the worst 5%.
          </p>
        </aside>

        {/* ── RIGHT: results ── */}
        <div className="space-y-5">
          {/* Error */}
          {error && (
            <div
              className="rounded border px-4 py-3 text-sm"
              style={{
                background: "rgba(153,27,27,0.07)",
                borderColor: "var(--negative)",
                color: "var(--negative)",
              }}
            >
              {error}
            </div>
          )}

          {/* Loading skeleton */}
          {loading && (
            <div
              className="rounded border p-6 text-center"
              style={{ background: "var(--card)", borderColor: "var(--border)" }}
            >
              <p className="text-sm animate-pulse" style={{ color: "var(--muted)" }}>
                Scoring {rows.filter((r) => r.address.trim()).length} wallets via Ethereum RPC…
              </p>
              <p className="text-xs mt-1" style={{ color: "var(--muted)" }}>
                This may take 15–60s depending on wallet history size.
              </p>
            </div>
          )}

          {/* Empty state */}
          {!loading && !result && !error && (
            <div
              className="rounded border border-dashed p-10 text-center"
              style={{ borderColor: "var(--border)" }}
            >
              <p className="text-sm" style={{ color: "var(--muted)" }}>
                Enter wallet addresses and click <strong style={{ color: "var(--foreground)" }}>Analyze Portfolio</strong> to see aggregate risk metrics.
              </p>
              <button
                onClick={loadDemo}
                className="mt-4 text-xs transition-opacity hover:opacity-70"
                style={{ color: "var(--primary)" }}
              >
                Try with demo wallets →
              </button>
            </div>
          )}

          {/* Results */}
          {result && (
            <>
              {/* KPI row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <KpiCard
                  label="Avg Score"
                  value={result.avg_score.toFixed(0)}
                  sub={`${result.n_scored}/${result.n_wallets} scored`}
                  color={scoreColor}
                />
                <KpiCard
                  label="Avg PD"
                  value={`${(result.avg_pd * 100).toFixed(1)}%`}
                  sub="Equal-weighted"
                />
                <KpiCard
                  label="VaR 95%"
                  value={`${(result.var_95 * 100).toFixed(1)}%`}
                  sub="95th-pct wallet PD"
                  color={result.var_95 > 0.6 ? "var(--negative)" : undefined}
                />
                <KpiCard
                  label="CVaR 95%"
                  value={`${(result.cvar_95 * 100).toFixed(1)}%`}
                  sub="Expected shortfall"
                  color={result.cvar_95 > 0.65 ? "var(--negative)" : undefined}
                />
              </div>

              {/* Risk meters */}
              <div
                className="rounded border p-4 space-y-3"
                style={{ background: "var(--card)", borderColor: "var(--border)" }}
              >
                <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: "var(--muted)" }}>
                  Risk Exposure
                </p>
                <RiskMeter value={result.avg_pd} label="Portfolio Avg PD" />
                <RiskMeter value={result.var_95} label="VaR 95%" />
                <RiskMeter value={result.cvar_95} label="CVaR 95% (Expected Shortfall)" />
                <RiskMeter value={result.concentration_high_risk} label="High / Very-High Concentration" />
              </div>

              {/* Tier breakdown: donut + bar */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Donut */}
                <div
                  className="rounded border p-4"
                  style={{ background: "var(--card)", borderColor: "var(--border)" }}
                >
                  <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: "var(--muted)" }}>
                    Tier Composition
                  </p>
                  <ResponsiveContainer width="100%" height={180}>
                    <PieChart>
                      <Pie
                        data={sortedTiers}
                        dataKey="count"
                        nameKey="tier"
                        cx="50%"
                        cy="50%"
                        innerRadius={48}
                        outerRadius={72}
                        paddingAngle={2}
                      >
                        {sortedTiers.map((entry) => (
                          <Cell
                            key={entry.tier}
                            fill={TIER_CONFIG[entry.tier]?.color ?? "var(--muted)"}
                          />
                        ))}
                      </Pie>
                      <Tooltip content={<DonutTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                  {/* Legend */}
                  <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
                    {sortedTiers.map((b) => (
                      <span key={b.tier} className="flex items-center gap-1 text-[10px]" style={{ color: "var(--muted)" }}>
                        <span
                          className="inline-block w-2 h-2 rounded-full"
                          style={{ background: TIER_CONFIG[b.tier]?.color ?? "var(--muted)" }}
                        />
                        {TIER_CONFIG[b.tier]?.label} ({b.count})
                      </span>
                    ))}
                  </div>
                </div>

                {/* Avg PD by tier bar */}
                <div
                  className="rounded border p-4"
                  style={{ background: "var(--card)", borderColor: "var(--border)" }}
                >
                  <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: "var(--muted)" }}>
                    Avg PD by Tier
                  </p>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart
                      data={sortedTiers.map((b) => ({
                        ...b,
                        label: TIER_CONFIG[b.tier]?.label ?? b.tier,
                        pd_pct: parseFloat((b.avg_pd * 100).toFixed(1)),
                      }))}
                      margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
                    >
                      <XAxis
                        dataKey="label"
                        tick={{ fontSize: 9, fill: "var(--muted)" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        tick={{ fontSize: 9, fill: "var(--muted)" }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(v) => `${v}%`}
                      />
                      <Tooltip
                        formatter={(v) => [`${v}%`, "Avg PD"]}
                        contentStyle={{
                          background: "var(--card)",
                          border: "1px solid var(--border)",
                          borderRadius: 4,
                          fontSize: 11,
                        }}
                        labelStyle={{ color: "var(--foreground)", fontSize: 11 }}
                      />
                      <Bar dataKey="pd_pct" radius={[3, 3, 0, 0]}>
                        {sortedTiers.map((entry) => (
                          <Cell
                            key={entry.tier}
                            fill={TIER_CONFIG[entry.tier]?.color ?? "var(--muted)"}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Per-wallet table */}
              <div
                className="rounded border overflow-hidden"
                style={{ background: "var(--card)", borderColor: "var(--border)" }}
              >
                <div
                  className="px-4 py-3 border-b flex items-center justify-between"
                  style={{ borderColor: "var(--border)" }}
                >
                  <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--muted)" }}>
                    Individual Wallets
                  </p>
                  {result.n_failed > 0 && (
                    <span className="text-[11px]" style={{ color: "var(--negative)" }}>
                      {result.n_failed} failed to score
                    </span>
                  )}
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr style={{ borderBottom: "1px solid var(--border)" }}>
                        {["Wallet", "Score", "PD", "Tier"].map((h) => (
                          <th
                            key={h}
                            className="px-4 py-2 text-left text-[10px] uppercase tracking-wider font-medium"
                            style={{ color: "var(--muted)" }}
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(walletResults.length > 0 ? walletResults : rows.map((r) => ({
                        wallet_address: r.address.trim(),
                        score: null,
                        risk_tier: null,
                        probability_of_default: null,
                        error: null,
                      } as WalletResult))).filter((r) => r.wallet_address).map((r, i) => (
                        <tr
                          key={i}
                          className="border-b last:border-0 hover:bg-[var(--card-hover)] transition-colors"
                          style={{ borderColor: "var(--border)" }}
                        >
                          <td className="px-4 py-2.5 font-mono" style={{ color: r.error ? "var(--negative)" : "var(--foreground)" }}>
                            <span className="hidden sm:inline">{r.wallet_address}</span>
                            <span className="sm:hidden">{r.wallet_address.slice(0, 10)}…{r.wallet_address.slice(-6)}</span>
                            {r.error && (
                              <span className="ml-2 text-[10px]" style={{ color: "var(--negative)" }}>
                                ({r.error.slice(0, 40)})
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-2.5 font-mono font-semibold" style={{
                            color: r.score == null ? "var(--muted)"
                              : r.score >= 650 ? "var(--positive)"
                              : r.score >= 450 ? "var(--warning)"
                              : "var(--negative)",
                          }}>
                            {r.score ?? "—"}
                          </td>
                          <td className="px-4 py-2.5 font-mono" style={{ color: "var(--foreground)" }}>
                            {r.probability_of_default != null
                              ? `${(r.probability_of_default * 100).toFixed(1)}%`
                              : "—"}
                          </td>
                          <td className="px-4 py-2.5">
                            {r.risk_tier ? <TierBadge tier={r.risk_tier} /> : <span style={{ color: "var(--muted)" }}>—</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Model metadata */}
              <p className="text-[10px]" style={{ color: "var(--muted)" }}>
                Model {result.model_version} · Scored at{" "}
                {new Date(result.scored_at).toLocaleString()} ·{" "}
                {result.n_failed > 0
                  ? `${result.n_failed} wallet(s) could not be scored`
                  : `All ${result.n_scored} wallets scored successfully`}
              </p>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
