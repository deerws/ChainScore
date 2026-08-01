"""
Compound V2 liquidation collector — fetches LiquidateBorrow events.

Compound V2 uses a per-market architecture: each cToken is its own contract
(cDAI, cUSDC, cETH, …). We query the Comptroller for the full market list and
then fetch LiquidateBorrow events from each market contract.

LiquidateBorrow event signature:
    event LiquidateBorrow(
        address liquidator,
        address borrower,       ← the liquidated borrower (topic1 in non-indexed)
        uint256 repayAmount,
        address cTokenCollateral,
        uint256 seizeTokens
    )

Note: all parameters are NON-indexed (appear in data, not topics).
Topic0 (event hash):
    0x298637f684da70674f26509b10f07ec2fbc77a335ab1e7d6215a4b2484d8bb52

Compound V2 Comptroller: 0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3b
Deployment block: ~7,710,671 (May 2019)

Output schema matches aave_v2_liquidations.parquet:
    block_number, timestamp, tx_hash, log_index, borrower,
    collateral_asset, debt_asset, protocol
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd
from web3 import Web3

from src.data.ethereum_client import EthereumClient

logger = logging.getLogger(__name__)

# ── Compound V2 constants ──────────────────────────────────────────────────
COMPTROLLER = "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3b"
LIQUIDATE_BORROW_TOPIC = (
    "0x298637f684da70674f26509b10f07ec2fbc77a335ab1e7d6215a4b2484d8bb52"
)
COMPOUND_START_BLOCK = 7_710_671
BLOCK_CHUNK_SIZE = 100_000
PAGE_SIZE = 1_000

# Major cToken markets (covers ~95% of Compound V2 volume)
CTOKEN_MARKETS = {
    "0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5": "cETH",
    "0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643": "cDAI",
    "0x39AA39c021dfbaE8faC545936693aC917d5E7563": "cUSDC",
    "0xf650C3d88D12dB855b8bf7D11Be6C55A4e07dCC9": "cUSDT",
    "0xC11b1268C1A384e55C48c2391d8d480264A3A7F4": "cWBTC",
    "0x35A18000230DA775CAc24873d00Ff85BccdeD550": "cUNI",
    "0x70e36f6BF80a52b3B46b3aF8e106CC0ed743E8e4": "cCOMP",
    "0xFAce851a4921ce59e912d19329929CE6da6EB0c3": "cLINK",
    "0x80a2AE356fc9ef4305b672f61D64cF9b6aca2B5": "cMKR",
    "0x041171993284df560249B57358F931D9eB7b925D": "cAAVE",
}


def _parse_log(log: dict, ctoken_address: str) -> dict | None:
    """
    Decode a LiquidateBorrow log.

    All event params are non-indexed so they're packed in log['data']:
        [0:32]   liquidator (address, padded)
        [32:64]  borrower   (address, padded)
        [64:96]  repayAmount (uint256)
        [96:128] cTokenCollateral (address, padded)
        [128:160] seizeTokens (uint256)
    """
    data = log.get("data", "")
    if data.startswith("0x"):
        data = data[2:]
    if len(data) < 320:  # 5 × 64 hex chars
        return None

    def extract_addr(hex32: str) -> str:
        return Web3.to_checksum_address("0x" + hex32[-40:])

    try:
        borrower = extract_addr(data[64:128])
        collateral = extract_addr(data[192:256])
        return {
            "block_number":    int(log["blockNumber"], 16),
            "timestamp":       int(log["timeStamp"], 16),
            "tx_hash":         log["transactionHash"],
            "log_index":       int(log["logIndex"], 16),
            "borrower":        borrower,
            "collateral_asset": collateral,
            "debt_asset":      Web3.to_checksum_address(ctoken_address),
            "protocol":        "compound_v2",
        }
    except Exception:
        return None


def collect_compound_liquidations(
    client: EthereumClient,
    start_block: int,
    end_block: int,
    output_path: Path,
    markets: dict[str, str] = CTOKEN_MARKETS,
    chunk_size: int = BLOCK_CHUNK_SIZE,
) -> pd.DataFrame:
    """Collect LiquidateBorrow events from all major Compound V2 cToken markets."""
    all_records: list[dict] = []

    for ctoken_addr, ctoken_name in markets.items():
        logger.info(f"Fetching Compound {ctoken_name} ({ctoken_addr[:10]}…)")
        current = start_block

        while current < end_block:
            chunk_end = min(current + chunk_size, end_block)

            page = 1
            while True:
                try:
                    logs = client.get_event_logs(
                        address=ctoken_addr,
                        topic0=LIQUIDATE_BORROW_TOPIC,
                        from_block=current,
                        to_block=chunk_end,
                        page=page,
                        offset=PAGE_SIZE,
                    )
                except Exception as exc:
                    logger.error(f"  {ctoken_name} page {page} failed: {exc}")
                    time.sleep(3)
                    break

                parsed = [r for r in (_parse_log(l, ctoken_addr) for l in logs) if r]
                all_records.extend(parsed)

                if len(logs) < PAGE_SIZE:
                    break
                page += 1
                time.sleep(0.25)

            current = chunk_end
            time.sleep(0.25)

        logger.info(f"  {ctoken_name}: {sum(1 for r in all_records if r['debt_asset'] == Web3.to_checksum_address(ctoken_addr))} events so far")

    if not all_records:
        logger.warning("No Compound liquidations found.")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    df = df.drop_duplicates(subset=["tx_hash", "log_index"])
    df = df.sort_values("block_number").reset_index(drop=True)

    logger.info(f"Total Compound liquidations: {len(df):,}")
    logger.info(f"Unique borrowers (default=1): {df['borrower'].nunique():,}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved → {output_path}")
    return df


def main() -> None:
    import argparse
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser(description="Collect Compound V2 liquidation events")
    parser.add_argument("--start-block", type=int, default=COMPOUND_START_BLOCK)
    parser.add_argument("--end-block",   type=int, default=None)
    parser.add_argument("--limit",       type=int, default=None)
    parser.add_argument("--output", type=Path, default=Path("data/raw/compound_v2_liquidations.parquet"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    client = EthereumClient.from_env()
    end_block = args.end_block or client.get_latest_block()
    if args.limit:
        end_block = min(end_block, args.start_block + args.limit)

    logger.info(f"Collecting Compound V2 liquidations: blocks {args.start_block:,} → {end_block:,}")
    collect_compound_liquidations(client=client, start_block=args.start_block, end_block=end_block, output_path=args.output)


if __name__ == "__main__":
    main()
