"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { usePortfolio } from "../providers/PortfolioProvider";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Famous wallets ──────────────────────────────────────────────────────────

interface Famous {
  name: string;
  address: string;
  description: string;
  longDescription: string;
  category: string;
  initials: string;
  note?: string;
  learnMoreUrl: string;
}

const FAMOUS: Famous[] = [
  {
    name: "Vitalik Buterin",
    address: "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    description: "Ethereum co-founder. Public wallet linked to vitalik.eth.",
    longDescription: "Co-founder of Ethereum and author of the original whitepaper. This public wallet (vitalik.eth) has been used for large charitable donations — most notably $1B+ in Shiba Inu tokens to Covid relief funds in India. Also active in DeFi experimentation and Gitcoin grants.",
    category: "Founder", initials: "VB", note: "vitalik.eth",
    learnMoreUrl: "https://etherscan.io/address/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
  },
  {
    name: "Ethereum Foundation",
    address: "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe",
    description: "Non-profit funding Ethereum R&D, protocol research, and ecosystem grants.",
    longDescription: "The Ethereum Foundation is the primary steward of Ethereum's development. This address holds a major portion of the foundation's ETH reserves and is used for funding core protocol research, client teams (Geth, Prysm, Lighthouse), and ecosystem grants via the ESP program.",
    category: "Foundation", initials: "EF",
    learnMoreUrl: "https://etherscan.io/address/0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe",
  },
  {
    name: "Binance Cold Wallet",
    address: "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8",
    description: "One of Binance's major cold-storage wallets holding billions in user assets.",
    longDescription: "One of Binance's largest known cold storage addresses, historically holding 250,000+ ETH. This is a custodial wallet — the ETH here belongs to Binance users, not Binance itself. Movements from this address are closely watched as on-chain signals of exchange reserve health.",
    category: "Exchange", initials: "BN", note: "Binance 7",
    learnMoreUrl: "https://etherscan.io/address/0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8",
  },
  {
    name: "Coinbase",
    address: "0x71660c4005BA85c37ccec55d0C4493E66Fe775d3",
    description: "Coinbase's primary on-chain storage. High volume reflecting custodial operations.",
    longDescription: "Primary Coinbase custodial address for ETH and ERC-20 assets. Receives high-frequency deposits from retail users and institutional clients. Coinbase is one of the most regulated exchanges globally — on-chain visibility into their reserves is important for proof-of-reserves audits.",
    category: "Exchange", initials: "CB",
    learnMoreUrl: "https://etherscan.io/address/0x71660c4005BA85c37ccec55d0C4493E66Fe775d3",
  },
  {
    name: "Kraken",
    address: "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0",
    description: "Kraken exchange hot wallet. Frequent large transfers typical of custodial flow.",
    longDescription: "Kraken's hot wallet for ETH operations. Hot wallets are connected to the internet and handle day-to-day withdrawals, making them higher-risk than cold storage. Kraken has been transparent about publishing their cold/hot wallet addresses for public verification.",
    category: "Exchange", initials: "KR",
    learnMoreUrl: "https://etherscan.io/address/0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0",
  },
  {
    name: "Punk6529",
    address: "0x6CC5F688a315f3dC28A7781717a9A798a59fDA7b",
    description: "Anonymous NFT collector famous for CryptoPunks holdings and open-metaverse advocacy.",
    longDescription: "One of the most influential anonymous voices in the NFT space. Holds a significant CryptoPunks collection and has been a leading advocate for the open metaverse and decentralized digital identity. Active on Twitter/X with detailed threads on NFT culture, digital ownership, and crypto geopolitics.",
    category: "NFT", initials: "P6", note: "6529.eth",
    learnMoreUrl: "https://etherscan.io/address/0x6CC5F688a315f3dC28A7781717a9A798a59fDA7b",
  },
  {
    name: "Justin Sun",
    address: "0x3DdfA8eC3052539b6C9549F12cEA2C295cfF5296",
    description: "TRON founder and active DeFi participant. Known for large Aave and Compound positions.",
    longDescription: "Founder of TRON blockchain and acquirer of BitTorrent. Known for some of the largest individual DeFi positions — at peak holding over $1B in assets across Aave, Compound, and Curve. His wallet activity is closely tracked as a market signal. Also famously won a charity auction for a lunch with Warren Buffett.",
    category: "DeFi", initials: "JS",
    learnMoreUrl: "https://etherscan.io/address/0x3DdfA8eC3052539b6C9549F12cEA2C295cfF5296",
  },
  {
    name: "Wintermute",
    address: "0x4d9085DED8F6a2f76099c1e5aeD4b94dD73bBBF",
    description: "Algorithmic trading firm and DeFi liquidity provider. One of the top on-chain market makers.",
    longDescription: "London-based algorithmic trading firm and one of the largest DeFi market makers. Provides liquidity across centralized and decentralized venues. In 2022, their DeFi wallet was exploited for ~$160M via a Profanity address vulnerability — a notable case study in operational security for DeFi participants.",
    category: "DeFi", initials: "WM",
    learnMoreUrl: "https://etherscan.io/address/0x4d9085DED8F6a2f76099c1e5aeD4b94dD73bBBF",
  },
];

const CATEGORIES = ["All", "Founder", "Foundation", "Exchange", "DeFi", "NFT"];

const CAT_STYLE: Record<string, { bg: string; text: string }> = {
  Founder:    { bg: "rgba(37,99,235,0.1)",  text: "#2563EB" },
  Foundation: { bg: "rgba(124,58,237,0.1)", text: "#7C3AED" },
  Exchange:   { bg: "rgba(234,88,12,0.1)",  text: "#EA580C" },
  DeFi:       { bg: "rgba(22,163,74,0.1)",  text: "#16A34A" },
  NFT:        { bg: "rgba(219,39,119,0.1)", text: "#DB2777" },
};

// ── Trending wallets ────────────────────────────────────────────────────────

interface TrendingWallet {
  address: string;
  tx_count: number;
  protocols: string[];
  last_seen_ago: string;
}

interface TrendingData {
  wallets: TrendingWallet[];
  fetched_at: string;
  cache_seconds: number;
  total_wallets_found?: number;
  error?: string;
}

const PROTOCOL_COLOR: Record<string, string> = {
  "Aave V2":    "#7C3AED",
  "Compound":   "#16A34A",
  "Uniswap V3": "#DB2777",
};

const REFRESH_INTERVAL = 300; // match backend cache TTL

// ── Shared helpers ──────────────────────────────────────────────────────────

function AddrShort({ addr }: { addr: string }) {
  return <span title={addr}>{addr.slice(0, 8)}…{addr.slice(-6)}</span>;
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function ExplorePage() {
  const [tab, setTab] = useState<"famous" | "trending">("famous");
  const router = useRouter();
  usePortfolio(); // keep context alive on this page

  function handleAnalyze(address: string) {
    localStorage.setItem("cs_auto_analyze", address);
    router.push("/");
  }

  return (
    <main>
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 py-8 sm:py-10">

          {/* Page header */}
          <div className="mb-7">
            <h1 className="text-3xl font-bold mb-1" style={{ color: "var(--foreground)" }}>
              Explore Wallets
            </h1>
            <p className="text-sm" style={{ color: "var(--muted)" }}>
              Browse famous wallets or see who is most active on DeFi protocols right now.
              Click <strong style={{ color: "var(--foreground)" }}>Analyze →</strong> to score any wallet.
            </p>
          </div>

          {/* Tab switcher */}
          <div className="flex gap-1 mb-8 border-b" style={{ borderColor: "var(--border)" }}>
            {(["famous", "trending"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className="px-4 py-2 text-sm font-medium transition-colors relative"
                style={{
                  color: tab === t ? "var(--foreground)" : "var(--muted)",
                  borderBottom: tab === t ? "2px solid var(--primary)" : "2px solid transparent",
                  marginBottom: -1,
                }}
              >
                {t === "famous" ? "Famous Wallets" : (
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: "#16A34A" }} />
                    Trending Now
                  </span>
                )}
              </button>
            ))}
          </div>

          {tab === "famous" ? (
            <FamousTab onAnalyze={handleAnalyze} />
          ) : (
            <TrendingTab onAnalyze={handleAnalyze} />
          )}

          <p className="text-[11px] mt-10 text-center" style={{ color: "var(--muted)" }}>
            Addresses from publicly available blockchain data and community-verified sources.
            ChainScore makes no ownership attribution.
          </p>
        </div>
    </main>
  );
}

// ── Famous Wallets tab ──────────────────────────────────────────────────────

interface RecentActivity {
  txCount: number | null;
  lastSeen: string | null;
  loading: boolean;
}

function FamousTab({ onAnalyze }: { onAnalyze: (addr: string) => void }) {
  const [filter, setFilter] = useState("All");
  const [copied, setCopied] = useState<string | null>(null);
  const [infoWallet, setInfoWallet] = useState<Famous | null>(null);
  const [activity, setActivity] = useState<RecentActivity>({ txCount: null, lastSeen: null, loading: false });

  const filtered = filter === "All" ? FAMOUS : FAMOUS.filter((w) => w.category === filter);

  function handleCopy(address: string) {
    navigator.clipboard.writeText(address).catch(() => {});
    setCopied(address);
    setTimeout(() => setCopied(null), 2000);
  }

  async function openInfo(wallet: Famous) {
    setInfoWallet(wallet);
    setActivity({ txCount: null, lastSeen: null, loading: true });

    try {
      // Yesterday's block range: ~6500 blocks/day
      const latestRes = await fetch(
        `https://api.etherscan.io/v2/api?chainid=1&module=proxy&action=eth_blockNumber&apikey=`
      );
      const latestJson = await latestRes.json();
      const latestBlock = parseInt(latestJson.result, 16);
      const startBlock = latestBlock - 6500;

      const res = await fetch(
        `https://api.etherscan.io/v2/api?chainid=1&module=account&action=txlist` +
        `&address=${wallet.address}&startblock=${startBlock}&endblock=${latestBlock}` +
        `&sort=desc&offset=1&page=1&apikey=`
      );
      const json = await res.json();
      const txs: any[] = Array.isArray(json.result) ? json.result : [];
      const lastTx = txs[0];
      const lastSeen = lastTx
        ? new Date(parseInt(lastTx.timeStamp) * 1000).toLocaleDateString("en-US", {
            month: "short", day: "numeric", year: "numeric",
          })
        : null;
      setActivity({ txCount: txs.length, lastSeen, loading: false });
    } catch {
      setActivity({ txCount: null, lastSeen: null, loading: false });
    }
  }

  function closeInfo() {
    setInfoWallet(null);
    setActivity({ txCount: null, lastSeen: null, loading: false });
  }

  return (
    <>
      {/* Category filters */}
      <div className="flex flex-wrap gap-2 mb-7">
        {CATEGORIES.map((cat) => {
          const active = filter === cat;
          const col = CAT_STYLE[cat];
          return (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className="px-3 py-1 text-xs font-medium rounded-full border transition-colors"
              style={active && col
                ? { background: col.bg, color: col.text, borderColor: col.text }
                : active
                ? { background: "var(--primary)", color: "#fff", borderColor: "var(--primary)" }
                : { background: "transparent", color: "var(--muted)", borderColor: "var(--border)" }
              }
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {filtered.map((wallet) => {
          const col = CAT_STYLE[wallet.category] ?? CAT_STYLE.Founder;
          const isCopied = copied === wallet.address;
          return (
            <div
              key={wallet.address}
              className="border rounded p-5 flex flex-col gap-4 card-shadow"
              style={{ background: "var(--card)", borderColor: "var(--border)" }}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-lg shrink-0 flex items-center justify-center text-sm font-bold text-white"
                  style={{ background: col.text }}
                >
                  {wallet.initials}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>
                      {wallet.name}
                    </p>
                    {wallet.note && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: col.bg, color: col.text }}>
                        {wallet.note}
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] uppercase tracking-wider font-medium" style={{ color: col.text }}>
                    {wallet.category}
                  </span>
                </div>

                {/* Info button */}
                <button
                  onClick={() => openInfo(wallet)}
                  title="About this wallet"
                  className="shrink-0 w-6 h-6 rounded-full border flex items-center justify-center text-[11px] font-bold transition-colors hover:opacity-70"
                  style={{ borderColor: "var(--border)", color: "var(--muted)" }}
                >
                  i
                </button>
              </div>

              <p className="text-xs leading-relaxed flex-1" style={{ color: "var(--muted)" }}>
                {wallet.description}
              </p>

              <div className="space-y-3">
                <div
                  className="px-3 py-2 rounded font-mono text-[11px] flex items-center justify-between gap-2"
                  style={{ background: "var(--background)" }}
                >
                  <span className="truncate" style={{ color: "var(--muted)" }}>
                    <AddrShort addr={wallet.address} />
                  </span>
                  <button
                    onClick={() => handleCopy(wallet.address)}
                    className="shrink-0 text-[10px] transition-opacity hover:opacity-70"
                    style={{ color: isCopied ? "var(--positive)" : "var(--muted)" }}
                  >
                    {isCopied ? "Copied!" : "Copy"}
                  </button>
                </div>
                <button
                  onClick={() => onAnalyze(wallet.address)}
                  className="w-full py-2 text-xs font-semibold rounded transition-opacity hover:opacity-80"
                  style={{ background: "var(--primary)", color: "#fff" }}
                >
                  Analyze →
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Info panel backdrop + panel */}
      {infoWallet && (() => {
        const col = CAT_STYLE[infoWallet.category] ?? CAT_STYLE.Founder;
        return (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
              onClick={closeInfo}
            />

            {/* Panel — bottom sheet on mobile, centered modal on sm+ */}
            <div className="fixed z-50 inset-x-0 bottom-0 sm:inset-0 sm:flex sm:items-center sm:justify-center sm:p-4">
              <div
                className="w-full sm:w-[420px] rounded-t-2xl sm:rounded-2xl p-6 shadow-2xl border"
                style={{ background: "var(--card)", borderColor: "var(--border)" }}
              >
                {/* Header */}
                <div className="flex items-start gap-3 mb-4">
                  <div
                    className="w-11 h-11 rounded-xl shrink-0 flex items-center justify-center text-sm font-bold text-white"
                    style={{ background: col.text }}
                  >
                    {infoWallet.initials}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>
                        {infoWallet.name}
                      </p>
                      {infoWallet.note && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: col.bg, color: col.text }}>
                          {infoWallet.note}
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] uppercase tracking-wider font-medium" style={{ color: col.text }}>
                      {infoWallet.category}
                    </span>
                  </div>
                  <button
                    onClick={closeInfo}
                    className="shrink-0 w-6 h-6 flex items-center justify-center rounded-full text-xs transition-opacity hover:opacity-70"
                    style={{ color: "var(--muted)" }}
                  >
                    ✕
                  </button>
                </div>

                {/* Description */}
                <p className="text-xs leading-relaxed mb-4" style={{ color: "var(--muted)" }}>
                  {infoWallet.longDescription}
                </p>

                {/* Yesterday's activity */}
                <div
                  className="rounded-lg px-3 py-2.5 mb-4 flex items-center gap-3"
                  style={{ background: "var(--background)" }}
                >
                  <div>
                    <p className="text-[10px] uppercase tracking-wider mb-0.5" style={{ color: "var(--muted)" }}>
                      Activity last 24 h
                    </p>
                    {activity.loading ? (
                      <div className="flex items-center gap-1.5">
                        <span className="w-3 h-3 rounded-full border-2 border-current border-t-transparent animate-spin" style={{ color: "var(--primary)" }} />
                        <span className="text-[11px]" style={{ color: "var(--muted)" }}>Fetching…</span>
                      </div>
                    ) : activity.txCount !== null ? (
                      <p className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>
                        {activity.txCount === 0
                          ? "No transactions yesterday"
                          : `${activity.txCount} transaction${activity.txCount !== 1 ? "s" : ""}${activity.lastSeen ? ` · last ${activity.lastSeen}` : ""}`}
                      </p>
                    ) : (
                      <p className="text-[11px]" style={{ color: "var(--muted)" }}>Unavailable</p>
                    )}
                  </div>
                </div>

                {/* Address */}
                <div
                  className="px-3 py-2 rounded font-mono text-[11px] flex items-center justify-between gap-2 mb-4"
                  style={{ background: "var(--background)" }}
                >
                  <span className="truncate" style={{ color: "var(--muted)" }}>
                    {infoWallet.address.slice(0, 10)}…{infoWallet.address.slice(-8)}
                  </span>
                  <button
                    onClick={() => handleCopy(infoWallet.address)}
                    className="shrink-0 text-[10px] transition-opacity hover:opacity-70"
                    style={{ color: copied === infoWallet.address ? "var(--positive)" : "var(--muted)" }}
                  >
                    {copied === infoWallet.address ? "Copied!" : "Copy"}
                  </button>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <a
                    href={infoWallet.learnMoreUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 py-2 text-xs font-medium rounded border text-center transition-opacity hover:opacity-70"
                    style={{ borderColor: "var(--border)", color: "var(--muted)" }}
                  >
                    View on Etherscan ↗
                  </a>
                  <button
                    onClick={() => { closeInfo(); onAnalyze(infoWallet.address); }}
                    className="flex-1 py-2 text-xs font-semibold rounded transition-opacity hover:opacity-80"
                    style={{ background: "var(--primary)", color: "#fff" }}
                  >
                    Analyze →
                  </button>
                </div>
              </div>
            </div>
          </>
        );
      })()}
    </>
  );
}

// ── Trending tab ────────────────────────────────────────────────────────────

function TrendingTab({ onAnalyze }: { onAnalyze: (addr: string) => void }) {
  const [data, setData] = useState<TrendingData | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(REFRESH_INTERVAL);
  const [copied, setCopied] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/v1/trending/wallets`);
      if (!res.ok) throw new Error(`API returned HTTP ${res.status}`);
      const json: TrendingData = await res.json();
      setData(json);
      setFetchError(null);
      setCountdown(REFRESH_INTERVAL);
    } catch (e) {
      setFetchError(
        e instanceof Error ? e.message : "Could not reach API. Is the server running?"
      );
    } finally {
      setLoading(false);
    }
  }

  // Initial load + periodic refresh
  useEffect(() => {
    load();
    const tick = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) { load(); return REFRESH_INTERVAL; }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(tick);
  }, []);

  function handleCopy(address: string) {
    navigator.clipboard.writeText(address).catch(() => {});
    setCopied(address);
    setTimeout(() => setCopied(null), 2000);
  }

  return (
    <div>
      {/* Status bar */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <span className="text-xs" style={{ color: "var(--muted)" }}>
            Wallets active on <strong style={{ color: "var(--foreground)" }}>Aave V2 · Compound · Uniswap V3</strong>
          </span>
          {data?.total_wallets_found && (
            <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: "rgba(37,99,235,0.1)", color: "var(--primary)" }}>
              {data.total_wallets_found} unique wallets found
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {loading && (
            <span className="w-3 h-3 rounded-full border-2 border-current border-t-transparent animate-spin" style={{ color: "var(--primary)" }} />
          )}
          <span className="text-[11px] font-mono" style={{ color: "var(--muted)" }}>
            refresh in {countdown}s
          </span>
          <button
            onClick={load}
            disabled={loading}
            className="text-[11px] px-2 py-1 rounded border transition-opacity hover:opacity-70 disabled:opacity-40"
            style={{ borderColor: "var(--border)", color: "var(--muted)" }}
          >
            ↻ Now
          </button>
        </div>
      </div>

      {/* Network/API error */}
      {fetchError && !data && (
        <div className="border rounded p-6 text-center" style={{ borderColor: "var(--border)", background: "var(--card)" }}>
          <p className="text-sm font-medium mb-1" style={{ color: "var(--negative)" }}>Failed to load trending data</p>
          <p className="text-xs" style={{ color: "var(--muted)" }}>{fetchError}</p>
          <button
            onClick={load}
            className="mt-3 text-xs transition-opacity hover:opacity-70"
            style={{ color: "var(--primary)" }}
          >
            ↻ Retry
          </button>
        </div>
      )}

      {/* Etherscan config error */}
      {data?.error && (
        <div className="border rounded p-6 text-center" style={{ borderColor: "var(--border)", background: "var(--card)" }}>
          <p className="text-sm" style={{ color: "var(--negative)" }}>{data.error}</p>
          <p className="text-xs mt-1" style={{ color: "var(--muted)" }}>Configure ETHERSCAN_API_KEY on the server to enable live data.</p>
        </div>
      )}

      {/* Loading skeleton */}
      {!data && !fetchError && loading && (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="border rounded p-4 animate-pulse" style={{ background: "var(--card)", borderColor: "var(--border)" }}>
              <div className="h-3 rounded w-1/3 mb-2" style={{ background: "var(--border)" }} />
              <div className="h-2 rounded w-1/2" style={{ background: "var(--border)" }} />
            </div>
          ))}
        </div>
      )}

      {/* Wallet list */}
      {data && data.wallets.length > 0 && (
        <div className="space-y-2">
          {data.wallets.map((wallet, i) => {
            const isCopied = copied === wallet.address;
            return (
              <div
                key={wallet.address}
                className="border rounded p-4 flex items-center gap-4 card-shadow"
                style={{ background: "var(--card)", borderColor: "var(--border)" }}
              >
                {/* Rank */}
                <span
                  className="w-6 text-center text-xs font-bold shrink-0"
                  style={{ color: i < 3 ? "var(--primary)" : "var(--muted)" }}
                >
                  #{i + 1}
                </span>

                {/* Address */}
                <div className="flex-1 min-w-0">
                  <span className="font-mono text-sm" style={{ color: "var(--foreground)" }}>
                    <AddrShort addr={wallet.address} />
                  </span>
                </div>

                {/* Protocol tags */}
                <div className="hidden sm:flex items-center gap-1 shrink-0">
                  {wallet.protocols.map((p) => (
                    <span
                      key={p}
                      className="text-[9px] px-1.5 py-0.5 rounded font-medium uppercase tracking-wider"
                      style={{
                        background: PROTOCOL_COLOR[p] ? `${PROTOCOL_COLOR[p]}18` : "var(--background)",
                        color: PROTOCOL_COLOR[p] ?? "var(--muted)",
                      }}
                    >
                      {p}
                    </span>
                  ))}
                </div>

                {/* Tx count */}
                <div className="text-right shrink-0 hidden md:block">
                  <p className="text-sm font-bold" style={{ color: "var(--foreground)" }}>{wallet.tx_count}</p>
                  <p className="text-[10px]" style={{ color: "var(--muted)" }}>txs</p>
                </div>

                {/* Last seen */}
                <div className="text-right shrink-0 hidden lg:block w-20">
                  <p className="text-[11px]" style={{ color: "var(--muted)" }}>{wallet.last_seen_ago}</p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    onClick={() => handleCopy(wallet.address)}
                    className="text-[10px] px-2 py-1 rounded border transition-opacity hover:opacity-70"
                    style={{ borderColor: "var(--border)", color: isCopied ? "var(--positive)" : "var(--muted)" }}
                  >
                    {isCopied ? "✓" : "Copy"}
                  </button>
                  <button
                    onClick={() => onAnalyze(wallet.address)}
                    className="text-[10px] px-2 py-1 rounded font-semibold transition-opacity hover:opacity-80"
                    style={{ background: "var(--primary)", color: "#fff" }}
                  >
                    Analyze →
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty state */}
      {data && data.wallets.length === 0 && !data.error && (
        <div className="border rounded py-16 text-center" style={{ borderColor: "var(--border)" }}>
          <p className="text-sm" style={{ color: "var(--muted)" }}>No recent activity found. Try again in a moment.</p>
        </div>
      )}

      {/* Footer note */}
      {data && (
        <p className="text-[10px] mt-5" style={{ color: "var(--muted)" }}>
          Data fetched from Etherscan. Cache expires every {Math.round(REFRESH_INTERVAL / 60)} min.
          {data.fetched_at && ` Last updated ${new Date(data.fetched_at).toLocaleTimeString()}.`}
        </p>
      )}
    </div>
  );
}
