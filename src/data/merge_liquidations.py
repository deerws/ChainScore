"""
Merge liquidation datasets from Aave V2, Compound V2, and MakerDAO into a
single cross-protocol default label file.

Usage:
    python -m src.data.merge_liquidations

Output:
    data/raw/all_liquidations.parquet  — union of all three protocols
    data/raw/default_labels.parquet    — one row per unique borrower with label=1

The merged file preserves the 'protocol' column so downstream analysis can
study protocol-specific behavior or train protocol-aware models.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

SOURCES = {
    "aave_v2":    Path("data/raw/aave_v2_liquidations.parquet"),
    "compound_v2": Path("data/raw/compound_v2_liquidations.parquet"),
    "makerdao":   Path("data/raw/makerdao_liquidations.parquet"),
}

OUTPUT_ALL    = Path("data/raw/all_liquidations.parquet")
OUTPUT_LABELS = Path("data/raw/default_labels.parquet")

REQUIRED_COLS = ["block_number", "timestamp", "tx_hash", "log_index", "borrower"]


def merge() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    for protocol, path in SOURCES.items():
        if not path.exists():
            logger.warning(f"Missing: {path} — skipping {protocol}")
            continue

        df = pd.read_parquet(path)
        if "protocol" not in df.columns:
            df["protocol"] = protocol

        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            logger.error(f"{protocol}: missing columns {missing} — skipping")
            continue

        logger.info(f"{protocol}: {len(df):,} events, {df['borrower'].nunique():,} unique borrowers")
        frames.append(df[REQUIRED_COLS + ["collateral_asset", "debt_asset", "protocol"]])

    if not frames:
        raise RuntimeError("No liquidation data found. Run the individual collectors first.")

    merged = pd.concat(frames, ignore_index=True)
    merged = merged.drop_duplicates(subset=["tx_hash", "log_index"])
    merged = merged.sort_values("block_number").reset_index(drop=True)

    logger.info(f"\nMerged total: {len(merged):,} liquidation events")
    logger.info(f"Unique borrowers across all protocols: {merged['borrower'].nunique():,}")
    logger.info(f"Protocol breakdown:\n{merged['protocol'].value_counts().to_string()}")

    OUTPUT_ALL.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(OUTPUT_ALL, index=False)
    logger.info(f"Saved all liquidations → {OUTPUT_ALL}")

    # One row per borrower — earliest liquidation wins (first_default_block)
    labels = (
        merged.groupby("borrower")
        .agg(
            first_default_block=("block_number", "min"),
            first_default_ts=("timestamp", "min"),
            liquidation_count=("tx_hash", "count"),
            protocols=("protocol", lambda x: "|".join(sorted(x.unique()))),
        )
        .reset_index()
    )
    labels["label"] = 1
    labels.to_parquet(OUTPUT_LABELS, index=False)
    logger.info(f"Saved default labels → {OUTPUT_LABELS}  ({len(labels):,} unique defaulters)")

    return merged


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    merge()
