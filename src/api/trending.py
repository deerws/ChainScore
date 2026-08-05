"""
Trending wallets — fetches wallets with the most recent DeFi activity
across Aave V2, Compound V2, and Uniswap V3 using the Etherscan API.

Results are cached for CACHE_TTL seconds to avoid rate-limit burns.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

MONITORED_PROTOCOLS: dict[str, str] = {
    "Aave V2":    "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
    "Compound":   "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3b",
    "Uniswap V3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
}

ETHERSCAN_BASE = "https://api.etherscan.io/api"
CACHE_TTL = 300  # 5 minutes — keeps us well within free-tier limits


_cache_result: dict | None = None
_cache_ts: float = 0.0


def _etherscan_tokentx(apikey: str, address: str, offset: int = 200) -> list[dict]:
    try:
        resp = requests.get(
            ETHERSCAN_BASE,
            params={
                "module": "account",
                "action": "tokentx",
                "address": address,
                "page": 1,
                "offset": offset,
                "sort": "desc",
                "apikey": apikey,
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("status") == "1":
            return data.get("result", [])
    except Exception as exc:
        logger.warning("Etherscan tokentx failed for %s: %s", address, exc)
    return []


def _ago(ts: int) -> str:
    diff = int(time.time()) - ts
    if diff < 60:
        return f"{diff}s ago"
    if diff < 3600:
        return f"{diff // 60}m ago"
    if diff < 86400:
        return f"{diff // 3600}h ago"
    return f"{diff // 86400}d ago"


def fetch_trending(n: int = 12) -> dict:
    """Return top-N wallets by recent DeFi transaction count. Cached CACHE_TTL seconds."""
    global _cache_result, _cache_ts

    if _cache_result is not None and time.monotonic() - _cache_ts < CACHE_TTL:
        logger.debug("Trending: serving from cache")
        return _cache_result

    apikey = os.getenv("ETHERSCAN_API_KEY", "")
    if not apikey:
        return {
            "wallets": [],
            "error": "ETHERSCAN_API_KEY not configured",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "cache_seconds": CACHE_TTL,
        }

    wallet_data: dict[str, dict] = {}

    for protocol, contract_addr in MONITORED_PROTOCOLS.items():
        contract_lower = contract_addr.lower()
        txs = _etherscan_tokentx(apikey, contract_addr)

        for tx in txs:
            sender = tx.get("from", "").lower()
            # Skip the contract itself and zero/invalid addresses
            if not sender or sender == contract_lower or len(sender) != 42:
                continue
            if sender not in wallet_data:
                wallet_data[sender] = {
                    "address": sender,
                    "tx_count": 0,
                    "protocols": set(),
                    "last_timestamp": 0,
                }
            wallet_data[sender]["tx_count"] += 1
            wallet_data[sender]["protocols"].add(protocol)
            ts = int(tx.get("timeStamp", 0) or 0)
            if ts > wallet_data[sender]["last_timestamp"]:
                wallet_data[sender]["last_timestamp"] = ts

        time.sleep(0.25)  # respect Etherscan free-tier 5 req/s limit

    top = sorted(wallet_data.values(), key=lambda w: w["tx_count"], reverse=True)[:n]

    wallets_out = [
        {
            "address": w["address"],
            "tx_count": w["tx_count"],
            "protocols": sorted(w["protocols"]),
            "last_seen_ago": _ago(w["last_timestamp"]) if w["last_timestamp"] else "—",
        }
        for w in top
    ]

    result = {
        "wallets": wallets_out,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "cache_seconds": CACHE_TTL,
        "total_wallets_found": len(wallet_data),
    }

    _cache_result = result
    _cache_ts = time.monotonic()
    logger.info("Trending: found %d unique wallets, returning top %d", len(wallet_data), len(wallets_out))
    return result
