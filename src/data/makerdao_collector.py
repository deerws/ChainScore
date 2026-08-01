"""
MakerDAO liquidation collector — fetches Bite (v1) and Bark (v2) events.

MakerDAO has two liquidation systems:
  - Liquidations 1.0 (Cat contract): emits `Bite` when a Vault is liquidated
  - Liquidations 2.0 (Dog contract): emits `Bark` (introduced ~May 2021)

Bite event (Cat):
    event Bite(
        bytes32 indexed ilk,        ← collateral type (e.g. ETH-A)
        address indexed urn,        ← the Vault owner (borrower)
        uint256 ink,
        uint256 art,
        uint256 tab,
        address flip,
        uint256 id
    )
    Topic0: 0x99b5620489b6ef926d4518d166b98e1c23a57ef0e7c09e9f6fb4f7ee0c5c55c2
    Cat contract: 0x78F2c2AF65126834c51822F56Be0d7469D7773cD (v1.1, from block 12,317,693)
    Cat contract: 0xa5679C04fc3d9d8b0AaB1F0ab83555b301cA70Ea (v1.0, from block 8,928,152)

Bark event (Dog):
    event Bark(
        bytes32 indexed ilk,
        address indexed urn,        ← the Vault owner (borrower)
        uint256 ink,
        uint256 art,
        uint256 due,
        address clip,
        uint256 indexed id
    )
    Topic0: 0x85258d09b1096b9e36b3b3d6a58b95b8e5e52d92fd4f59f48dfe4b61f78e0d0
    Dog contract: 0x135954d155898D42C90D2a57824C690e0c7BEf1b (from block 12,317,793)

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

# ── MakerDAO constants ─────────────────────────────────────────────────────

# Cat (Liquidations 1.x) — two deployments
CAT_V1_0 = "0xa5679C04fc3d9d8b0AaB1F0ab83555b301cA70Ea"  # blocks 8,928,152–12,317,693
CAT_V1_1 = "0x78F2c2AF65126834c51822F56Be0d7469D7773cD"  # blocks 12,317,693+
BITE_TOPIC = "0x99b5620489b6ef926d4518d166b98e1c23a57ef0e7c09e9f6fb4f7ee0c5c55c2"
CAT_START_BLOCK = 8_928_152

# Dog (Liquidations 2.0)
DOG = "0x135954d155898D42C90D2a57824C690e0c7BEf1b"
BARK_TOPIC = "0x85258d09b1096b9e36b3b3d6a58b95b8e5e52d92fd4f59f48dfe4b61f78e0d0"
DOG_START_BLOCK = 12_317_793

DAI_ADDRESS = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
BLOCK_CHUNK_SIZE = 100_000
PAGE_SIZE = 1_000


def _parse_bite(log: dict) -> dict | None:
    """
    Bite(bytes32 indexed ilk, address indexed urn, ...)
    urn (vault owner = borrower) is topic[2], last 40 hex chars.
    """
    topics = log.get("topics", [])
    if len(topics) < 3:
        return None
    try:
        borrower = Web3.to_checksum_address("0x" + topics[2][-40:])
        return {
            "block_number":    int(log["blockNumber"], 16),
            "timestamp":       int(log["timeStamp"], 16),
            "tx_hash":         log["transactionHash"],
            "log_index":       int(log["logIndex"], 16),
            "borrower":        borrower,
            "collateral_asset": "",  # ilk is bytes32, not a token address
            "debt_asset":      DAI_ADDRESS,
            "protocol":        "makerdao",
        }
    except Exception:
        return None


def _parse_bark(log: dict) -> dict | None:
    """
    Bark(bytes32 indexed ilk, address indexed urn, ...)
    Same layout as Bite — urn is topic[2].
    """
    return _parse_bite(log)  # identical indexed layout


def _fetch_events(
    client: EthereumClient,
    address: str,
    topic0: str,
    start_block: int,
    end_block: int,
    parser,
    label: str,
) -> list[dict]:
    records: list[dict] = []
    current = start_block

    while current < end_block:
        chunk_end = min(current + BLOCK_CHUNK_SIZE, end_block)
        logger.info(f"  {label}: blocks {current:,} → {chunk_end:,}")
        page = 1
        while True:
            try:
                logs = client.get_event_logs(
                    address=address,
                    topic0=topic0,
                    from_block=current,
                    to_block=chunk_end,
                    page=page,
                    offset=PAGE_SIZE,
                )
            except Exception as exc:
                logger.error(f"  {label} page {page} error: {exc}")
                time.sleep(3)
                break

            parsed = [r for r in (parser(l) for l in logs) if r]
            records.extend(parsed)

            if len(logs) < PAGE_SIZE:
                break
            page += 1
            time.sleep(0.25)

        current = chunk_end
        time.sleep(0.25)

    logger.info(f"  {label}: {len(records)} events collected")
    return records


def collect_maker_liquidations(
    client: EthereumClient,
    end_block: int,
    output_path: Path,
) -> pd.DataFrame:
    """Collect Bite (Cat v1.0 + v1.1) and Bark (Dog) events from MakerDAO."""
    all_records: list[dict] = []

    # Cat v1.0 (2019–2021)
    all_records.extend(_fetch_events(
        client, CAT_V1_0, BITE_TOPIC,
        CAT_START_BLOCK, 12_317_693,
        _parse_bite, "Cat v1.0 Bite",
    ))

    # Cat v1.1 (2021–)
    all_records.extend(_fetch_events(
        client, CAT_V1_1, BITE_TOPIC,
        12_317_693, DOG_START_BLOCK,
        _parse_bite, "Cat v1.1 Bite",
    ))

    # Dog (Liquidations 2.0, 2021–)
    all_records.extend(_fetch_events(
        client, DOG, BARK_TOPIC,
        DOG_START_BLOCK, end_block,
        _parse_bark, "Dog Bark",
    ))

    if not all_records:
        logger.warning("No MakerDAO liquidations found.")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    df = df.drop_duplicates(subset=["tx_hash", "log_index"])
    df = df.sort_values("block_number").reset_index(drop=True)

    logger.info(f"Total MakerDAO liquidations: {len(df):,}")
    logger.info(f"Unique Vault owners (default=1): {df['borrower'].nunique():,}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved → {output_path}")
    return df


def main() -> None:
    import argparse
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser(description="Collect MakerDAO liquidation events")
    parser.add_argument("--end-block", type=int, default=None)
    parser.add_argument("--output", type=Path, default=Path("data/raw/makerdao_liquidations.parquet"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    client = EthereumClient.from_env()
    end_block = args.end_block or client.get_latest_block()

    logger.info(f"Collecting MakerDAO liquidations up to block {end_block:,}")
    collect_maker_liquidations(client=client, end_block=end_block, output_path=args.output)


if __name__ == "__main__":
    main()
