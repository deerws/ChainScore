"use client";

import { useState, useEffect, useRef } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ShapFactor {
  feature: string;
  shap_value: number;
  direction: "increases_risk" | "decreases_risk";
}

interface ApiResult {
  wallet_address: string;
  score: number;
  risk_tier: string;
  probability_of_default: number;
  top_factors: ShapFactor[];
  score_valid_until: string;
}

interface PortfolioItem {
  address: string;
  score: number;
  pd: number;
  risk_tier: string;
  weight: number;
}

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  ReferenceLine,
} from "recharts";

// ── Mock Data ──────────────────────────────────────────────────────────────

const MOCK_WALLET = {
  address: "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
  ens: "vitalik.eth",
  score: 782,
  riskTier: "low" as const,
  pdEstimate: 0.183,
  scoreValidDays: 30,
  walletAge: 2847,
  activeProtocols: 12,
  totalRepaid: 4250000,
  totalBorrowed: 3890000,
  smartMoneyPercentile: 94,
};

const SHAP_FACTORS = [
  { feature: "wallet_age_days", value: 0.142, impact: "positive", interpretation: "Long on-chain history indicates reliability" },
  { feature: "repay_to_borrow_ratio", value: 0.098, impact: "positive", interpretation: "Consistent repayment behavior above 1.0x" },
  { feature: "protocols_used", value: 0.067, impact: "positive", interpretation: "Diversified protocol engagement" },
  { feature: "recent_tx_ratio", value: -0.034, impact: "negative", interpretation: "Recent activity spike warrants monitoring" },
  { feature: "aave_borrow_count", value: 0.052, impact: "positive", interpretation: "Established Aave borrowing track record" },
];

const PROTOCOL_EXPOSURE = [
  { protocol: "Aave", exposure: "$2.4M", netUsage: "+$890K", riskSignal: "Low" },
  { protocol: "Compound", exposure: "$1.1M", netUsage: "+$340K", riskSignal: "Low" },
  { protocol: "MakerDAO", exposure: "$680K", netUsage: "+$120K", riskSignal: "Medium" },
  { protocol: "Uniswap", exposure: "$450K", netUsage: "-$45K", riskSignal: "Low" },
  { protocol: "Lido", exposure: "$2.1M", netUsage: "+$1.2M", riskSignal: "Low" },
];

// Deterministic seed so server and client render identical values (no hydration mismatch)
function seededRand(seed: number) {
  const x = Math.sin(seed + 1) * 10000;
  return x - Math.floor(x);
}
const ACTIVITY_HEATMAP = Array.from({ length: 90 }, (_, i) => ({
  day: i,
  value: Math.floor(seededRand(i) * 5),
}));

const TRANSACTION_HISTORY = [
  { month: "Jun", value: 12 },
  { month: "Jul", value: 18 },
  { month: "Aug", value: 24 },
  { month: "Sep", value: 15 },
  { month: "Oct", value: 32 },
  { month: "Nov", value: 28 },
  { month: "Dec", value: 45 },
  { month: "Jan", value: 38 },
  { month: "Feb", value: 52 },
  { month: "Mar", value: 41 },
  { month: "Apr", value: 36 },
  { month: "May", value: 48 },
];

const RECENT_TRANSACTIONS = [
  { date: "May 7, 2026", protocol: "Aave", type: "Repay", amount: "125 ETH", usd: "$312,500" },
  { date: "May 5, 2026", protocol: "Uniswap", type: "Swap", amount: "50 ETH", usd: "$125,000" },
  { date: "May 3, 2026", protocol: "Lido", type: "Stake", amount: "200 ETH", usd: "$500,000" },
  { date: "May 1, 2026", protocol: "Compound", type: "Borrow", amount: "80 ETH", usd: "$200,000" },
  { date: "Apr 28, 2026", protocol: "MakerDAO", type: "Repay", amount: "45 ETH", usd: "$112,500" },
];

// ── Semicircle Gauge ───────────────────────────────────────────────────────

function ScoreGauge({ score }: { score: number }) {
  const percentage = score / 1000;
  const angle = percentage * 180;
  const r = 80;
  const cx = 100;
  const cy = 100;

  const bands = [
    { className: "gauge-critical", start: 0,  end: 20  },
    { className: "gauge-poor",     start: 20, end: 40  },
    { className: "gauge-fair",     start: 40, end: 60  },
    { className: "gauge-good",     start: 60, end: 80  },
    { className: "gauge-excellent",start: 80, end: 100 },
  ];

  const activeClass =
    percentage < 0.2 ? "gauge-critical" :
    percentage < 0.4 ? "gauge-poor"     :
    percentage < 0.6 ? "gauge-fair"     :
    percentage < 0.8 ? "gauge-good"     : "gauge-excellent";

  const arcPoint = (deg: number) => {
    const rad = (deg - 180) * (Math.PI / 180);
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  };

  const end = arcPoint(angle);

  return (
    <div className="relative w-full max-w-[280px] mx-auto">
      <svg viewBox="0 0 200 120" className="w-full">
        {/* Background arc segments */}
        {bands.map((band, i) => {
          const p1 = arcPoint((band.start / 100) * 180);
          const p2 = arcPoint((band.end  / 100) * 180);
          return (
            <path
              key={i}
              d={`M ${p1.x} ${p1.y} A ${r} ${r} 0 0 1 ${p2.x} ${p2.y}`}
              fill="none"
              stroke="currentColor"
              className={band.className}
              strokeWidth="12"
              strokeLinecap="butt"
              opacity={0.25}
            />
          );
        })}

        {/* Active arc — large-arc-flag always 0 (arc ≤ 180°) */}
        {angle > 0 && (
          <path
            d={`M ${arcPoint(0).x} ${arcPoint(0).y} A ${r} ${r} 0 0 1 ${end.x} ${end.y}`}
            fill="none"
            stroke="currentColor"
            className={activeClass}
            strokeWidth="12"
            strokeLinecap="round"
          />
        )}
        
        {/* Center text */}
        <text x="100" y="85" textAnchor="middle" className="headline-serif text-4xl" fill="currentColor">
          {score}
        </text>
        <text x="100" y="105" textAnchor="middle" className="text-xs" style={{ fill: 'var(--muted)' }}>
          / 1000
        </text>
      </svg>
    </div>
  );
}

// ── SHAP Feature Importance ────────────────────────────────────────────────

function ShapFeatureChart({ factors }: { factors: typeof SHAP_FACTORS }) {
  const data = factors.map(f => ({
    name: f.feature,
    value: f.value,
    impact: f.impact,
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} layout="vertical" margin={{ left: 0, right: 20, top: 0, bottom: 0 }}>
        <XAxis 
          type="number" 
          domain={[-0.1, 0.2]}
          tick={{ fontSize: 10, fill: "var(--muted)" }}
          axisLine={{ stroke: "var(--border)" }}
          tickLine={false}
        />
        <YAxis 
          type="category" 
          dataKey="name" 
          width={130}
          tick={{ fontSize: 10, fill: "var(--muted)", fontFamily: "var(--font-mono)" }}
          axisLine={false}
          tickLine={false}
        />
        <ReferenceLine x={0} stroke="var(--border)" />
        <Tooltip
          formatter={(v) => [Number(v).toFixed(3), "Impact"]}
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 4,
            fontSize: 11,
            color: "var(--foreground)",
          }}
        />
        <Bar dataKey="value" barSize={16}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.impact === "positive" ? "var(--primary)" : "var(--negative)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Activity Heatmap ───────────────────────────────────────────────────────

function ActivityHeatmap() {
  const weeks = 13;
  const days = 7;

  return (
    <div className="flex gap-1">
      {Array.from({ length: weeks }, (_, week) => (
        <div key={week} className="flex flex-col gap-1">
          {Array.from({ length: days }, (_, day) => {
            const index = week * 7 + day;
            const value = ACTIVITY_HEATMAP[index]?.value ?? 0;
            return (
              <div
                key={day}
                className={`w-3 h-3 rounded-sm heatmap-${value}`}
                style={{
                  backgroundColor: value === 0 ? 'var(--border)' : undefined,
                  opacity: value === 0 ? 0.5 : 1,
                }}
              />
            );
          })}
        </div>
      ))}
    </div>
  );
}

// ── Transaction Line Chart ─────────────────────────────────────────────────

function TransactionChart() {
  return (
    <ResponsiveContainer width="100%" height={160}>
      <LineChart data={TRANSACTION_HISTORY} margin={{ left: 0, right: 0, top: 10, bottom: 0 }}>
        <XAxis 
          dataKey="month" 
          tick={{ fontSize: 10, fill: "var(--muted)" }}
          axisLine={{ stroke: "var(--border)" }}
          tickLine={false}
        />
        <YAxis 
          tick={{ fontSize: 10, fill: "var(--muted)" }}
          axisLine={false}
          tickLine={false}
          width={30}
        />
        <Tooltip
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 4,
            fontSize: 11,
            color: "var(--foreground)",
          }}
        />
        <Line 
          type="monotone" 
          dataKey="value" 
          stroke="var(--primary)" 
          strokeWidth={1.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── Status Badge ───────────────────────────────────────────────────────────

type BadgeType = "live" | "sample" | "beta" | "roadmap";

const BADGE_CONFIG: Record<BadgeType, { label: string; color: string; bg: string; tooltip?: string }> = {
  live:    { label: "Live",        color: "var(--positive)", bg: "rgba(22,101,52,0.12)"   },
  sample:  { label: "Sample Data", color: "var(--warning)",  bg: "rgba(217,119,6,0.12)",
             tooltip: "Illustrative data — displayed for demonstration purposes. Real values are populated when a wallet is analyzed via the API." },
  beta:    { label: "Beta",        color: "var(--primary)",  bg: "rgba(37,99,235,0.12)"  },
  roadmap: { label: "Roadmap",     color: "var(--muted)",    bg: "var(--border)"          },
};

function StatusBadge({ type }: { type: BadgeType }) {
  const cfg = BADGE_CONFIG[type];
  return (
    <span
      title={cfg.tooltip}
      className="text-[9px] uppercase tracking-widest px-2 py-0.5 rounded font-semibold"
      style={{
        color: cfg.color,
        background: cfg.bg,
        cursor: cfg.tooltip ? "help" : "default",
      }}
    >
      {cfg.label}
    </span>
  );
}

// ── Page Component ─────────────────────────────────────────────────────────

export default function Home() {
  const [address, setAddress] = useState("");
  const [apiResult, setApiResult] = useState<ApiResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Watch Live (SSE)
  const [watching, setWatching] = useState(false);
  const [watchScore, setWatchScore] = useState<number | null>(null);
  const [watchTier, setWatchTier] = useState<string | null>(null);
  const [watchPd, setWatchPd] = useState<number | null>(null);
  const [watchLastUpdate, setWatchLastUpdate] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  function startWatch(addr: string) {
    if (esRef.current) esRef.current.close();
    const es = new EventSource(`${API_BASE}/v1/watch/${addr}/stream`);
    esRef.current = es;
    setWatching(true);

    const handleScore = (e: MessageEvent) => {
      const d = JSON.parse(e.data);
      setWatchScore(d.score);
      setWatchTier(d.risk_tier);
      setWatchPd(d.probability_of_default);
      setWatchLastUpdate(new Date(d.polled_at).toLocaleTimeString());
    };
    es.addEventListener("score_update", handleScore);
    es.addEventListener("score_unchanged", handleScore);
    es.onerror = () => { stopWatch(); };
  }

  function stopWatch() {
    esRef.current?.close();
    esRef.current = null;
    setWatching(false);
  }

  // Stop stream when user changes wallet
  useEffect(() => { stopWatch(); }, [apiResult]);

  // ── Portfolio sidebar ──────────────────────────────────────────────────
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);

  // Persist last result and portfolio across page navigation
  useEffect(() => {
    try {
      const saved = localStorage.getItem("cs_last_result");
      if (saved) {
        const { addr, result } = JSON.parse(saved);
        setAddress(addr);
        setApiResult(result);
      }
      const savedPortfolio = localStorage.getItem("cs_portfolio");
      if (savedPortfolio) {
        const p = JSON.parse(savedPortfolio);
        if (Array.isArray(p) && p.length > 0) { setPortfolio(p); setSidebarOpen(true); }
      }
    } catch {}

    // Auto-analyze: triggered by Explore page OR by resuming an interrupted in-flight analysis
    try {
      const autoAddr = localStorage.getItem("cs_auto_analyze");
      if (autoAddr && autoAddr.startsWith("0x") && autoAddr.length === 42) {
        setAddress(autoAddr);
        analyzeWallet(autoAddr); // pass directly — bypasses stale address state
      }
    } catch {}
  }, []);

  useEffect(() => {
    if (apiResult) localStorage.setItem("cs_last_result", JSON.stringify({ addr: address, result: apiResult }));
  }, [apiResult]);

  useEffect(() => {
    localStorage.setItem("cs_portfolio", JSON.stringify(portfolio));
  }, [portfolio]);

  function normalizeWeights(items: PortfolioItem[]): PortfolioItem[] {
    if (items.length === 0) return items;
    const total = items.reduce((s, p) => s + p.weight, 0);
    if (total === 0) return items.map(p => ({ ...p, weight: 100 / items.length }));
    return items.map(p => ({ ...p, weight: parseFloat(((p.weight / total) * 100).toFixed(1)) }));
  }

  function addToPortfolio() {
    if (!apiResult) return;
    const addr = apiResult.wallet_address;
    if (portfolio.some(p => p.address.toLowerCase() === addr.toLowerCase())) {
      setSidebarOpen(true); return;
    }
    const newItem: PortfolioItem = {
      address: addr, score, pd, risk_tier: riskTier, weight: 100,
    };
    setPortfolio(prev => normalizeWeights([...prev, newItem]));
    setSidebarOpen(true);
  }

  function removeFromPortfolio(addr: string) {
    setPortfolio(prev => normalizeWeights(prev.filter(p => p.address !== addr)));
  }

  function setRawWeight(addr: string, val: number) {
    setPortfolio(prev => prev.map(p => p.address === addr ? { ...p, weight: Math.max(0, val) } : p));
  }

  function applyNormalize() {
    setPortfolio(prev => normalizeWeights(prev));
  }

  async function exportPdf() {
    if (portfolio.length === 0 || exportingPdf) return;
    setExportingPdf(true);
    try {
      const res = await fetch(`${API_BASE}/v1/report/portfolio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          wallets: portfolio.map(p => ({
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
      console.error("PDF export failed:", err);
      alert(`PDF export failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setExportingPdf(false);
    }
  }

  const weightedScore = portfolio.length > 0
    ? Math.round(portfolio.reduce((s, p) => s + p.score * p.weight / 100, 0)) : null;
  const weightedPd = portfolio.length > 0
    ? portfolio.reduce((s, p) => s + p.pd * p.weight / 100, 0) : null;
  const totalWeight = parseFloat(portfolio.reduce((s, p) => s + p.weight, 0).toFixed(1));
  const isInPortfolio = apiResult
    ? portfolio.some(p => p.address.toLowerCase() === apiResult.wallet_address.toLowerCase())
    : false;

  // Anchor state
  const [anchoring, setAnchoring] = useState(false);
  const [anchorResult, setAnchorResult] = useState<{
    tx_hash: string; score_hash: string; valid_until_iso: string; etherscan_url: string;
  } | null>(null);
  const [anchorError, setAnchorError] = useState<string | null>(null);

  async function anchorScore() {
    if (!apiResult) return;
    setAnchoring(true);
    setAnchorError(null);
    try {
      const res = await fetch(`${API_BASE}/v1/anchor`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wallet_address: apiResult.wallet_address }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail ?? `HTTP ${res.status}`);
      setAnchorResult(data);
    } catch (e) {
      setAnchorError(e instanceof Error ? e.message : "Anchor failed.");
    } finally {
      setAnchoring(false);
    }
  }

  const hasResult = apiResult !== null;

  // Use watch values when active, otherwise API result values
  const liveScore = watching && watchScore !== null ? watchScore : null;

  const score    = (watching && watchScore !== null ? watchScore  : apiResult?.score)     ?? MOCK_WALLET.score;
  const riskTier = (watching && watchTier  !== null ? watchTier  : apiResult?.risk_tier) ?? MOCK_WALLET.riskTier;
  const pd       = (watching && watchPd    !== null ? watchPd    : apiResult?.probability_of_default) ?? MOCK_WALLET.pdEstimate;
  const validDays   = apiResult?.score_valid_until
    ? Math.max(0, Math.round((new Date(apiResult.score_valid_until).getTime() - Date.now()) / 86_400_000))
    : MOCK_WALLET.scoreValidDays;

  const shapData = apiResult?.top_factors.length
    ? apiResult.top_factors.map((f) => ({
        feature: f.feature,
        value: f.shap_value,
        impact: f.direction === "decreases_risk" ? "positive" : "negative",
        interpretation: f.direction === "decreases_risk"
          ? "Reduces probability of default"
          : "Increases probability of default",
      }))
    : SHAP_FACTORS;

  async function analyzeWallet(overrideAddr?: string) {
    const addr = (overrideAddr ?? address).trim();
    if (!addr.startsWith("0x") || addr.length !== 42) {
      setApiError("Enter a valid Ethereum address (42-char hex starting with 0x).");
      return;
    }
    // Mark the address as in-flight so we can resume if the user navigates away mid-analysis
    localStorage.setItem("cs_auto_analyze", addr);
    setLoading(true);
    setApiError(null);
    setApiResult(null);
    try {
      const res = await fetch(`${API_BASE}/v1/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wallet_address: addr, include_shap: true }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail ?? `HTTP ${res.status}`);
      }
      const data: ApiResult = await res.json();
      setApiResult(data);
      localStorage.removeItem("cs_auto_analyze"); // clear only on success
    } catch (e: unknown) {
      setApiError(e instanceof Error ? e.message : "Failed to reach API.");
      localStorage.removeItem("cs_auto_analyze"); // clear on error too
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--background)' }}>

    {/* ── PORTFOLIO SIDEBAR ──────────────────────────────────────────────── */}
    {sidebarOpen && (
      <aside
        className="hidden lg:flex flex-col w-72 shrink-0 border-l sticky top-0 h-screen overflow-y-auto"
        style={{ background: 'var(--card)', borderColor: 'var(--border)' }}
      >
        <div className="p-4 border-b flex items-center justify-between" style={{ borderColor: 'var(--border)' }}>
          <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Portfolio</p>
          <button onClick={() => setSidebarOpen(false)} className="text-xs hover:opacity-70" style={{ color: 'var(--muted)' }}>✕</button>
        </div>

        {portfolio.length === 0 ? (
          <p className="text-xs p-4" style={{ color: 'var(--muted)' }}>
            Analyze a wallet and click "Add to Portfolio" to build your portfolio.
          </p>
        ) : (
          <div className="flex flex-col gap-0 flex-1">
            {portfolio.map((item) => (
              <div key={item.address} className="p-4 border-b" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono" style={{ color: 'var(--foreground)' }}>
                    {item.address.slice(0,6)}…{item.address.slice(-4)}
                  </span>
                  <button onClick={() => removeFromPortfolio(item.address)} className="text-[10px] hover:opacity-70" style={{ color: 'var(--muted)' }}>✕</button>
                </div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-lg font-bold" style={{ color: 'var(--foreground)' }}>{item.score}</span>
                  <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded" style={{
                    color: item.risk_tier === 'very_low' || item.risk_tier === 'low' ? 'var(--positive)' : item.risk_tier === 'medium' ? 'var(--warning)' : 'var(--negative)',
                    background: item.risk_tier === 'very_low' || item.risk_tier === 'low' ? 'rgba(22,101,52,0.12)' : item.risk_tier === 'medium' ? 'rgba(217,119,6,0.12)' : 'rgba(185,28,28,0.12)',
                  }}>
                    {item.risk_tier.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-[10px] uppercase tracking-wider shrink-0" style={{ color: 'var(--muted)' }}>Weight %</label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={parseFloat(item.weight.toFixed(1))}
                    onChange={e => setRawWeight(item.address, parseFloat(e.target.value) || 0)}
                    onBlur={applyNormalize}
                    className="w-full px-2 py-1 text-xs font-mono rounded border focus:outline-none"
                    style={{ background: 'var(--background)', borderColor: 'var(--border)', color: 'var(--foreground)' }}
                  />
                </div>
              </div>
            ))}

            {/* Weight total indicator */}
            <div className="px-4 py-2 flex items-center justify-between text-[10px]" style={{ color: Math.abs(totalWeight - 100) < 0.2 ? 'var(--positive)' : 'var(--warning)' }}>
              <span>Total weight</span>
              <span className="font-mono font-semibold">{totalWeight.toFixed(1)}%</span>
            </div>
            <button
              onClick={applyNormalize}
              className="mx-4 mb-2 py-1 text-[10px] rounded border hover:opacity-70 transition-opacity"
              style={{ borderColor: 'var(--border)', color: 'var(--muted)' }}
            >
              Normalize to 100%
            </button>

            {/* Weighted aggregate */}
            {weightedScore !== null && (
              <div className="mx-4 mb-3 p-3 rounded border" style={{ background: 'var(--background)', borderColor: 'var(--border)' }}>
                <p className="text-[10px] uppercase tracking-wider mb-3" style={{ color: 'var(--muted)' }}>Weighted Portfolio</p>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span style={{ color: 'var(--muted)' }}>Avg Score</span>
                    <span className="font-mono font-semibold" style={{ color: 'var(--foreground)' }}>{weightedScore}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span style={{ color: 'var(--muted)' }}>Weighted PD</span>
                    <span className="font-mono font-semibold" style={{ color: 'var(--foreground)' }}>{((weightedPd ?? 0) * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span style={{ color: 'var(--muted)' }}>Wallets</span>
                    <span className="font-mono" style={{ color: 'var(--muted)' }}>{portfolio.length}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Export PDF */}
            <button
              onClick={exportPdf}
              disabled={exportingPdf || portfolio.length === 0}
              className="mx-4 mb-4 py-2 text-xs rounded font-semibold transition-opacity hover:opacity-80 disabled:opacity-40 flex items-center justify-center gap-1.5"
              style={{ background: 'var(--primary)', color: '#fff' }}
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
    )}

    <main className="flex-1 min-w-0" style={{ background: 'var(--background)' }}>
      <div className="max-w-[1400px] mx-auto px-6 py-8">
        
        {/* ── HERO / REPORT TITLE ─────────────────────────────────────── */}
        <section className="mb-10">
          <div className="flex items-start justify-between gap-6">
            <div className="flex-1 max-w-3xl">
              <h1 className="headline-serif text-4xl md:text-5xl mb-2">
                Wallet Credit Intelligence Report
              </h1>
              <p className="text-lg mb-5" style={{ color: 'var(--muted)' }}>
                On-chain credit risk analysis and behavioral scoring
              </p>
              
              {/* Wallet Input */}
              <div className="flex gap-3 mb-3">
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && analyzeWallet()}
                  placeholder="Enter wallet address (0x...)"
                  className="flex-1 px-4 py-2.5 border rounded text-sm font-mono focus:outline-none focus:ring-1"
                  style={{
                    background: 'var(--card)',
                    borderColor: 'var(--border)',
                    color: 'var(--foreground)',
                  }}
                />
                <button
                  onClick={() => analyzeWallet()}
                  disabled={loading}
                  className="px-5 py-2.5 text-sm font-medium rounded hover:opacity-90 transition-opacity disabled:opacity-50"
                  style={{ background: 'var(--primary)', color: '#fff' }}
                >
                  {loading ? "Scoring…" : "Analyze"}
                </button>
              </div>
              {apiError && (
                <p className="text-xs mb-3 px-1" style={{ color: 'var(--negative)' }}>{apiError}</p>
              )}
              {apiResult && (
                <p className="text-xs mb-3 px-1 font-mono" style={{ color: 'var(--muted)' }}>
                  Scored: {apiResult.wallet_address.slice(0,6)}…{apiResult.wallet_address.slice(-4)} · valid until {apiResult.score_valid_until}
                </p>
              )}
              
              {/* Analyst Note */}
              <div className="border p-4 rounded card-shadow" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
                <div className="flex items-start gap-3">
                  <div className="w-1 h-full rounded-full shrink-0" style={{ minHeight: "40px", background: 'var(--primary)' }} />
                  <div>
                    <p className="text-xs uppercase tracking-wider mb-1 font-medium" style={{ color: 'var(--muted)' }}>
                      Analyst Note
                    </p>
                    <p className="text-sm leading-relaxed">
                      Wallet exhibits disciplined leverage behavior across Aave and Compound with low short-term liquidation probability. Consistent repayment patterns suggest institutional-grade risk management practices.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Hero Illustration + Portfolio toggle */}
            <div className="hidden lg:flex flex-col items-end gap-3 w-56 xl:w-72 shrink-0">
              {portfolio.length > 0 && (
                <button
                  onClick={() => setSidebarOpen(o => !o)}
                  className="flex items-center gap-1.5 text-[10px] px-2 py-1 rounded border font-semibold transition-colors"
                  style={{ borderColor: 'var(--primary)', color: 'var(--primary)', background: 'rgba(37,99,235,0.08)' }}
                >
                  <span>Portfolio</span>
                  <span className="w-4 h-4 rounded-full text-[9px] flex items-center justify-center font-bold" style={{ background: 'var(--primary)', color: '#fff' }}>{portfolio.length}</span>
                  {sidebarOpen ? "→" : "←"}
                </button>
              )}
              <img
                src="/hero-bull.png"
                alt="ChainScore Bull - Wall Street meets Blockchain"
                className="w-full h-auto hero-bull"
              />
            </div>
          </div>
        </section>

        {/* ── EMPTY STATE ─────────────────────────────────────────────── */}
        {!hasResult && !loading && (
          <section className="mb-10">
            <div
              className="rounded border border-dashed py-16 text-center"
              style={{ borderColor: 'var(--border)' }}
            >
              <p className="text-sm font-medium mb-1" style={{ color: 'var(--foreground)' }}>
                No wallet analyzed yet
              </p>
              <p className="text-xs mb-5" style={{ color: 'var(--muted)' }}>
                Enter an Ethereum address above and click <strong>Analyze</strong> to generate a credit report.
              </p>
              <button
                onClick={() => setAddress(MOCK_WALLET.address)}
                className="text-xs transition-opacity hover:opacity-70"
                style={{ color: 'var(--primary)' }}
              >
                Try with a demo address →
              </button>
            </div>
          </section>
        )}

        {/* ── RESULTS (shown only after a wallet is analyzed) ─────────── */}
        {hasResult && <>

        {/* ── CREDIT SCORE SECTION (Two columns) ──────────────────────── */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
          {/* LEFT: Score Gauge */}
          <div className="border p-6 rounded card-shadow" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <h2 className="text-xs uppercase tracking-wider font-medium" style={{ color: 'var(--muted)' }}>Credit Score</h2>
                {watching && (
                  <span className="flex items-center gap-1 text-[10px] font-semibold" style={{ color: 'var(--positive)' }}>
                    <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'var(--positive)' }} />
                    LIVE
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge type="live" />
                <button
                  onClick={() => watching ? stopWatch() : startWatch(apiResult!.wallet_address)}
                  className="text-[10px] px-2 py-0.5 rounded border transition-colors font-semibold"
                  style={watching
                    ? { borderColor: 'var(--positive)', color: 'var(--positive)', background: 'rgba(22,101,52,0.08)' }
                    : { borderColor: 'var(--border)', color: 'var(--muted)' }}
                >
                  {watching ? "Stop" : "Watch Live"}
                </button>
                <button
                  onClick={isInPortfolio ? () => setSidebarOpen(true) : addToPortfolio}
                  className="text-[10px] px-2 py-0.5 rounded border transition-colors font-semibold"
                  style={isInPortfolio
                    ? { borderColor: 'var(--primary)', color: 'var(--primary)', background: 'rgba(37,99,235,0.08)' }
                    : { borderColor: 'var(--border)', color: 'var(--muted)' }}
                >
                  {isInPortfolio ? "In Portfolio ✓" : "+ Portfolio"}
                </button>
              </div>
            </div>
            {watching && watchLastUpdate && (
              <p className="text-[10px] text-center mb-2" style={{ color: 'var(--muted)' }}>
                Last polled: {watchLastUpdate} · refreshes every 60s
              </p>
            )}
            <ScoreGauge score={score} />
            <div className="flex justify-center gap-4 mt-4 text-[10px] uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm" style={{ background: 'var(--negative)' }} /> High</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm" style={{ background: 'var(--warning)' }} /> Med-High</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm" style={{ background: '#CA8A04' }} /> Medium</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm" style={{ background: 'var(--primary)' }} /> Low</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm" style={{ background: 'var(--positive)' }} /> V.Low</span>
            </div>
          </div>

          {/* RIGHT: KPI Cards */}
          <div className="flex flex-col gap-4">
            {/* Top row - main metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="border p-4 rounded card-shadow relative" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
                <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>Risk Tier</p>
                <p className="text-xl font-medium capitalize" style={{ color: 'var(--positive)' }}>
                  {riskTier.replace("_", " ")}
                </p>
              </div>
              <div className="border p-4 rounded card-shadow" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
                <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>PD Estimate</p>
                <p className="text-xl font-medium">{(pd * 100).toFixed(1)}%</p>
              </div>
              <div className="border p-4 rounded card-shadow" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
                <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>Valid For</p>
                <p className="text-xl font-medium">{validDays}d</p>
              </div>
            </div>

            {/* Key stats table */}
            <div className="border p-4 rounded card-shadow flex-1" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between mb-3">
                <p className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Key Statistics</p>
                <StatusBadge type="sample" />
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span style={{ color: 'var(--muted)' }}>Wallet Age</span>
                  <span className="font-mono">{MOCK_WALLET.walletAge.toLocaleString()} days</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: 'var(--muted)' }}>Active Protocols</span>
                  <span className="font-mono">{MOCK_WALLET.activeProtocols}</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: 'var(--muted)' }}>Total Repaid</span>
                  <span className="font-mono">${(MOCK_WALLET.totalRepaid / 1000000).toFixed(2)}M</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: 'var(--muted)' }}>Total Borrowed</span>
                  <span className="font-mono">${(MOCK_WALLET.totalBorrowed / 1000000).toFixed(2)}M</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: 'var(--muted)' }}>Smart Money Percentile</span>
                  <span className="font-mono" style={{ color: 'var(--primary)' }}>{MOCK_WALLET.smartMoneyPercentile}th</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── ON-CHAIN ANCHORING ──────────────────────────────────────── */}
        <section className="mb-10">
          <div className="border rounded card-shadow overflow-hidden" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-3">
                <h2 className="text-xs uppercase tracking-wider font-medium" style={{ color: 'var(--muted)' }}>
                  On-Chain Score Proof
                </h2>
                <StatusBadge type="beta" />
              </div>
              {!anchorResult && (
                <button
                  onClick={anchorScore}
                  disabled={anchoring}
                  className="text-xs px-3 py-1.5 rounded font-semibold transition-colors disabled:opacity-50"
                  style={{ background: 'var(--primary)', color: '#fff' }}
                >
                  {anchoring ? "Anchoring…" : "Anchor Score on Sepolia →"}
                </button>
              )}
            </div>
            <div className="px-6 py-5">
              {!anchorResult && !anchorError && (
                <p className="text-sm" style={{ color: 'var(--muted)' }}>
                  Publish a cryptographic commitment of this score to the Sepolia testnet.
                  Lenders can verify the score was issued at a specific time without trusting the ChainScore server.
                </p>
              )}
              {anchorError && (
                <p className="text-sm" style={{ color: 'var(--negative)' }}>{anchorError}</p>
              )}
              {anchorResult && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full" style={{ background: 'var(--positive)' }} />
                    <span className="text-sm font-medium" style={{ color: 'var(--positive)' }}>
                      Score anchored on Sepolia
                    </span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
                    <div>
                      <p className="uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>Tx Hash</p>
                      <a
                        href={anchorResult.etherscan_url}
                        target="_blank"
                        rel="noreferrer"
                        className="hover:underline break-all"
                        style={{ color: 'var(--primary)' }}
                      >
                        {anchorResult.tx_hash.slice(0, 20)}…{anchorResult.tx_hash.slice(-8)} ↗
                      </a>
                    </div>
                    <div>
                      <p className="uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>Score Hash</p>
                      <p className="break-all" style={{ color: 'var(--foreground)' }}>
                        {anchorResult.score_hash.slice(0, 20)}…
                      </p>
                    </div>
                    <div>
                      <p className="uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>Valid Until</p>
                      <p style={{ color: 'var(--foreground)' }}>{anchorResult.valid_until_iso.replace("T", " ").slice(0, 19)} UTC</p>
                    </div>
                    <div>
                      <p className="uppercase tracking-wider mb-1" style={{ color: 'var(--muted)' }}>Network</p>
                      <p style={{ color: 'var(--foreground)' }}>Ethereum Sepolia Testnet</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* ── SHAP FEATURE IMPORTANCE ─────────────────────────────────── */}
        <section className="mb-10">
          <div className="border p-6 rounded card-shadow" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-sm font-medium mb-1">{"What's Driving This Score?"}</h2>
                <p className="text-xs" style={{ color: 'var(--muted)' }}>SHAP-based feature importance analysis</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-wider px-2 py-1 rounded" style={{ color: 'var(--muted)', background: 'var(--border)' }}>ML Explainability</span>
                <StatusBadge type="live" />
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ShapFeatureChart factors={shapData} />

              <div className="space-y-3">
                {shapData.map((factor, i) => (
                  <div key={i} className="flex items-start gap-3 text-sm">
                    <span 
                      className="w-2 h-2 rounded-full mt-1.5 shrink-0"
                      style={{ background: factor.impact === "positive" ? "var(--primary)" : "var(--negative)" }}
                    />
                    <div>
                      <span className="font-mono text-xs" style={{ color: 'var(--muted)' }}>{factor.feature}</span>
                      <p>{factor.interpretation}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-6 mt-6 pt-4 border-t text-xs" style={{ borderColor: 'var(--border)' }}>
              <span className="flex items-center gap-2" style={{ color: 'var(--muted)' }}>
                <span className="w-3 h-1 rounded" style={{ background: 'var(--primary)' }} /> Positive Impact
              </span>
              <span className="flex items-center gap-2" style={{ color: 'var(--muted)' }}>
                <span className="w-3 h-1 rounded" style={{ background: 'var(--negative)' }} /> Negative Impact
              </span>
            </div>
          </div>
        </section>

        {/* ── PROTOCOL EXPOSURE + ACTIVITY HEATMAP ────────────────────── */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">
          {/* Protocol Exposure Table */}
          <div className="lg:col-span-2 border p-6 rounded card-shadow" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium">Protocol Exposure</h2>
              <StatusBadge type="sample" />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full data-table">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th className="text-left py-2 pr-4">Protocol</th>
                    <th className="text-right py-2 px-4">Exposure</th>
                    <th className="text-right py-2 px-4">Net Usage</th>
                    <th className="text-right py-2 pl-4">Risk Signal</th>
                  </tr>
                </thead>
                <tbody>
                  {PROTOCOL_EXPOSURE.map((row, i) => (
                    <tr key={i} style={{ borderBottom: i < PROTOCOL_EXPOSURE.length - 1 ? '1px solid var(--border)' : 'none' }}>
                      <td className="py-2.5 pr-4">
                        <span className="font-medium">{row.protocol}</span>
                      </td>
                      <td className="text-right py-2.5 px-4 font-mono">{row.exposure}</td>
                      <td className="text-right py-2.5 px-4 font-mono" style={{ color: row.netUsage.startsWith("+") ? "var(--positive)" : "var(--negative)" }}>
                        {row.netUsage}
                      </td>
                      <td className="text-right py-2.5 pl-4">
                        <span 
                          className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded"
                          style={{ 
                            backgroundColor: row.riskSignal === "Low" ? "rgba(22, 101, 52, 0.15)" : "rgba(217, 119, 6, 0.15)",
                            color: row.riskSignal === "Low" ? "var(--positive)" : "var(--warning)"
                          }}
                        >
                          {row.riskSignal}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Activity Heatmap */}
          <div className="border p-6 rounded card-shadow" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between mb-1">
              <h2 className="text-sm font-medium">Activity Heatmap</h2>
              <StatusBadge type="sample" />
            </div>
            <p className="text-xs mb-4" style={{ color: 'var(--muted)' }}>Last 90 days</p>
            <ActivityHeatmap />
            <div className="flex items-center gap-2 mt-4 text-[10px]" style={{ color: 'var(--muted)' }}>
              <span>Less</span>
              <div className="flex gap-0.5">
                {[0.3, 0.4, 0.6, 0.8, 1].map((o, i) => (
                  <div key={i} className="w-2.5 h-2.5 rounded-sm" style={{ background: 'var(--primary)', opacity: o }} />
                ))}
              </div>
              <span>More</span>
            </div>
          </div>
        </section>

        {/* ── TRANSACTION HISTORY CHART ───────────────────────────────── */}
        <section className="mb-10">
          <div className="border p-6 rounded card-shadow" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between mb-1">
              <h2 className="text-sm font-medium">Transaction History</h2>
              <StatusBadge type="sample" />
            </div>
            <p className="text-xs mb-4" style={{ color: 'var(--muted)' }}>Monthly transaction count (12 months)</p>
            <TransactionChart />
          </div>
        </section>

        {/* ── RISK ASSESSMENT ─────────────────────────────────────────── */}
        <section className="mb-10">
          <div className="border p-6 rounded card-shadow" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium">Risk Assessment</h2>
              <StatusBadge type="sample" />
            </div>
            <div className="max-w-3xl">
              <p className="leading-relaxed mb-4">
                This wallet demonstrates strong overall creditworthiness with a low probability of default. 
                The subject maintains disciplined leverage management across major DeFi protocols, with a 
                repayment-to-borrow ratio significantly above market average. Historical behavior suggests 
                institutional-grade risk awareness and capital efficiency.
              </p>
              <div className="space-y-2">
                <div className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full mt-2 shrink-0" style={{ background: 'var(--positive)' }} />
                  <p className="text-sm"><strong>Strong repayment behavior</strong> — Consistent debt servicing across all active positions</p>
                </div>
                <div className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full mt-2 shrink-0" style={{ background: 'var(--positive)' }} />
                  <p className="text-sm"><strong>Healthy on-chain history</strong> — Extended wallet age with diversified protocol usage</p>
                </div>
                <div className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full mt-2 shrink-0" style={{ background: 'var(--warning)' }} />
                  <p className="text-sm"><strong>Monitor short-term activity spike</strong> — Recent transaction volume elevated vs. baseline</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── RECENT ACTIVITY TABLE ───────────────────────────────────── */}
        <section className="mb-10">
          <div className="border p-6 rounded card-shadow" style={{ background: 'var(--card)', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium">Recent Activity</h2>
              <StatusBadge type="sample" />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full data-table">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th className="text-left py-2 pr-4">Date</th>
                    <th className="text-left py-2 px-4">Protocol</th>
                    <th className="text-left py-2 px-4">Type</th>
                    <th className="text-right py-2 px-4">Amount</th>
                    <th className="text-right py-2 pl-4">USD Value</th>
                  </tr>
                </thead>
                <tbody>
                  {RECENT_TRANSACTIONS.map((tx, i) => (
                    <tr key={i} style={{ borderBottom: i < RECENT_TRANSACTIONS.length - 1 ? '1px solid var(--border)' : 'none' }}>
                      <td className="py-2.5 pr-4 font-mono" style={{ color: 'var(--muted)' }}>{tx.date}</td>
                      <td className="py-2.5 px-4 font-medium">{tx.protocol}</td>
                      <td className="py-2.5 px-4">
                        <span 
                          className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded"
                          style={{ 
                            backgroundColor: tx.type === "Repay" ? "rgba(22, 101, 52, 0.15)" : tx.type === "Borrow" ? "rgba(185, 28, 28, 0.15)" : "var(--border)",
                            color: tx.type === "Repay" ? "var(--positive)" : tx.type === "Borrow" ? "var(--negative)" : "var(--muted)"
                          }}
                        >
                          {tx.type}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono">{tx.amount}</td>
                      <td className="py-2.5 pl-4 text-right font-mono" style={{ color: 'var(--muted)' }}>{tx.usd}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        </>} {/* end hasResult */}

        {/* ── FOOTER ──────────────────────────────────────────────────── */}
        <footer className="border-t pt-6 mt-10" style={{ borderColor: 'var(--border)' }}>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-xs" style={{ color: 'var(--muted)' }}>
            <div>
              <p className="font-medium mb-1" style={{ color: 'var(--foreground)' }}>ChainScore</p>
              <p>On-chain DeFi credit risk scoring</p>
            </div>
            <div className="flex gap-6">
              <a href="https://github.com/deerws/ChainScore" className="hover:opacity-70 transition-opacity">GitHub</a>
              <a href="https://br.linkedin.com/in/andrepinheiropaes" className="hover:opacity-70 transition-opacity">@andrepinheiropaes</a>
            </div>
          </div>

          {/* Methodological disclaimer */}
          <div className="mt-6 pt-5 border-t" style={{ borderColor: 'var(--border)' }}>
            <p className="text-[10px] uppercase tracking-widest mb-2 font-semibold" style={{ color: 'var(--muted)' }}>
              Methodological Disclaimer
            </p>
            <p className="text-xs leading-relaxed max-w-4xl" style={{ color: 'var(--muted)' }}>
              ChainScore generates a{" "}
              <strong style={{ color: 'var(--foreground)' }}>DeFi liquidation risk score</strong>
              {" "}— a behavioral proxy for credit default probability calibrated on 49,748 Aave V2
              liquidation events (2020–2023). Liquidation risk is not equivalent to traditional credit
              default: it measures the probability of collateral seizure by the protocol due to an
              undercollateralized position, not a missed repayment schedule. Walk-forward validated
              AUC ≈ 0.67 indicates meaningful discriminatory power for relative ranking and pricing
              adjustments.{" "}
              <strong style={{ color: 'var(--foreground)' }}>
                Not suitable for regulated credit decisions or Basel III capital calculations.
              </strong>{" "}
              Sections marked <span style={{ color: 'var(--warning)' }}>Sample Data</span> display
              illustrative values for demonstration; live scores are populated when a wallet is
              analyzed via the API. For full methodology see{" "}
              <code className="text-[10px]" style={{ color: 'var(--muted)' }}>
                notebooks/09_target_variable_analysis.ipynb
              </code>.
            </p>
          </div>

          {/* Status legend */}
          <div className="flex flex-wrap gap-4 mt-4 text-[10px]" style={{ color: 'var(--muted)' }}>
            <span className="flex items-center gap-1.5">
              <StatusBadge type="live" /> Real-time API data
            </span>
            <span className="flex items-center gap-1.5">
              <StatusBadge type="sample" /> Illustrative — hover for details
            </span>
            <span className="flex items-center gap-1.5">
              <StatusBadge type="beta" /> In active development
            </span>
            <span className="flex items-center gap-1.5">
              <StatusBadge type="roadmap" /> Planned feature
            </span>
          </div>
        </footer>
      </div>
    </main>
    </div>
  );
}
