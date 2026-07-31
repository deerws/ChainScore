"""
ChainScore on-chain anchoring — wraps ChainScoreAnchor.sol on Sepolia.

Workflow:
  1. Score a wallet off-chain (ML inference).
  2. Compute score_hash = keccak256(abi.encodePacked(wallet, score, validUntil, modelVersion)).
  3. Call anchorScore() on Sepolia — stores the commitment, emits ScoreAnchored event.
  4. Anyone can call verifyScore() to confirm a claimed score matches the on-chain hash.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from eth_abi.packed import encode_packed
from eth_utils import keccak
from web3 import Web3
from web3.types import TxReceipt

# ── Contract ABI (subset — only functions used by the API) ────────────────

ANCHOR_ABI = [
    {
        "inputs": [
            {"name": "wallet",       "type": "address"},
            {"name": "scoreHash",    "type": "bytes32"},
            {"name": "validUntil",   "type": "uint256"},
            {"name": "modelVersion", "type": "uint16"},
        ],
        "name": "anchorScore",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "wallet",       "type": "address"},
            {"name": "score",        "type": "uint256"},
            {"name": "validUntil",   "type": "uint256"},
            {"name": "modelVersion", "type": "uint16"},
        ],
        "name": "verifyScore",
        "outputs": [{"name": "valid", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "wallet", "type": "address"}],
        "name": "getScore",
        "outputs": [
            {"name": "scoreHash",    "type": "bytes32"},
            {"name": "issuedAt",     "type": "uint256"},
            {"name": "validUntil",   "type": "uint256"},
            {"name": "modelVersion", "type": "uint16"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,  "name": "wallet",       "type": "address"},
            {"indexed": True,  "name": "scoreHash",    "type": "bytes32"},
            {"indexed": False, "name": "validUntil",   "type": "uint256"},
            {"indexed": False, "name": "modelVersion", "type": "uint16"},
            {"indexed": False, "name": "issuer",       "type": "address"},
        ],
        "name": "ScoreAnchored",
        "type": "event",
    },
]

MODEL_VERSION: int = 1
SCORE_VALIDITY_DAYS: int = 30


def compute_score_hash(wallet: str, score: int, valid_until: int, model_version: int = MODEL_VERSION) -> bytes:
    """Replicates keccak256(abi.encodePacked(wallet, score, validUntil, modelVersion))."""
    checksum = Web3.to_checksum_address(wallet)
    packed = encode_packed(
        ["address", "uint256", "uint256", "uint16"],
        [checksum, score, valid_until, model_version],
    )
    return keccak(packed)


class AnchorClient:
    """Thin wrapper around the ChainScoreAnchor contract on Sepolia."""

    def __init__(self) -> None:
        rpc = os.getenv("SEPOLIA_RPC_URL", "")
        contract_addr = os.getenv("CONTRACT_ADDRESS", "")
        self._private_key = os.getenv("DEPLOYER_PRIVATE_KEY", "")

        if not rpc or not contract_addr or contract_addr == "0x" + "0" * 40:
            raise RuntimeError(
                "Blockchain anchoring not configured. "
                "Set SEPOLIA_RPC_URL, CONTRACT_ADDRESS, and DEPLOYER_PRIVATE_KEY in .env."
            )

        self.w3 = Web3(Web3.HTTPProvider(rpc))
        if not self.w3.is_connected():
            raise RuntimeError(f"Cannot connect to Sepolia RPC: {rpc}")

        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_addr),
            abi=ANCHOR_ABI,
        )
        self.oracle = self.w3.eth.account.from_key(self._private_key)
        self.chain_id = self.w3.eth.chain_id  # 11155111 for Sepolia

    # ── Write ────────────────────────────────────────────────────────────

    def anchor_score(self, wallet: str, score: int) -> dict:
        """
        Anchor a score on-chain. Returns tx_hash, score_hash, and valid_until.
        Raises on RPC/tx failure.
        """
        wallet = Web3.to_checksum_address(wallet)
        valid_until = int(time.time()) + SCORE_VALIDITY_DAYS * 86_400

        score_hash = compute_score_hash(wallet, score, valid_until)

        nonce = self.w3.eth.get_transaction_count(self.oracle.address, "pending")
        gas_price = self.w3.eth.gas_price

        tx = self.contract.functions.anchorScore(
            wallet,
            score_hash,
            valid_until,
            MODEL_VERSION,
        ).build_transaction({
            "from":     self.oracle.address,
            "nonce":    nonce,
            "gasPrice": int(gas_price * 1.2),  # 20% tip to avoid stuck tx
            "chainId":  self.chain_id,
        })

        signed = self.w3.eth.account.sign_transaction(tx, self._private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)

        return {
            "tx_hash":     tx_hash.hex(),
            "score_hash":  "0x" + score_hash.hex(),
            "valid_until": valid_until,
            "valid_until_iso": datetime.fromtimestamp(valid_until, tz=timezone.utc).isoformat(),
            "etherscan_url": f"https://sepolia.etherscan.io/tx/{tx_hash.hex()}",
        }

    # ── Read ─────────────────────────────────────────────────────────────

    def get_record(self, wallet: str) -> dict | None:
        """Return the on-chain score record for a wallet, or None if not anchored."""
        wallet = Web3.to_checksum_address(wallet)
        score_hash, issued_at, valid_until, model_version = self.contract.functions.getScore(wallet).call()

        if issued_at == 0:
            return None

        now = int(time.time())
        return {
            "score_hash":     "0x" + score_hash.hex(),
            "issued_at":      issued_at,
            "issued_at_iso":  datetime.fromtimestamp(issued_at, tz=timezone.utc).isoformat(),
            "valid_until":    valid_until,
            "valid_until_iso": datetime.fromtimestamp(valid_until, tz=timezone.utc).isoformat(),
            "model_version":  model_version,
            "is_expired":     now > valid_until,
            "etherscan_url":  f"https://sepolia.etherscan.io/address/{os.getenv('CONTRACT_ADDRESS')}",
        }

    def verify(self, wallet: str, score: int, valid_until: int, model_version: int = MODEL_VERSION) -> bool:
        """Call verifyScore() on-chain — returns True if hash matches and not expired."""
        wallet = Web3.to_checksum_address(wallet)
        return self.contract.functions.verifyScore(wallet, score, valid_until, model_version).call()
