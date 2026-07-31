#!/usr/bin/env python3
"""
Deploy ChainScoreAnchor.sol to Sepolia testnet.

Prerequisites:
  - SEPOLIA_RPC_URL in .env (Alchemy Sepolia endpoint)
  - DEPLOYER_PRIVATE_KEY in .env (test wallet with Sepolia ETH)
  - pip install py-solc-x  (installs solc compiler automatically)

Usage:
  python scripts/deploy_anchor.py

After deploy, copy CONTRACT_ADDRESS into your .env and Render environment.
Faucet for Sepolia ETH: https://sepoliafaucet.com
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

REPO_ROOT = Path(__file__).parent.parent
SOL_PATH = REPO_ROOT / "contracts" / "ChainScoreAnchor.sol"


def main() -> None:
    rpc = os.getenv("SEPOLIA_RPC_URL", "")
    private_key = os.getenv("DEPLOYER_PRIVATE_KEY", "")

    if not rpc:
        sys.exit("Error: SEPOLIA_RPC_URL not set in .env")
    if not private_key or "your_test_wallet" in private_key:
        sys.exit("Error: DEPLOYER_PRIVATE_KEY not set in .env (add your Sepolia test wallet key)")

    w3 = Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        sys.exit(f"Error: cannot connect to {rpc}")

    account = w3.eth.account.from_key(private_key)
    balance = w3.eth.get_balance(account.address)
    balance_eth = w3.from_wei(balance, "ether")
    print(f"Deployer:  {account.address}")
    print(f"Balance:   {balance_eth:.4f} ETH (Sepolia)")

    if balance_eth < 0.01:
        sys.exit("Error: insufficient Sepolia ETH. Get some at https://sepoliafaucet.com")

    # Compile with py-solc-x
    try:
        from solcx import compile_source, install_solc
    except ImportError:
        sys.exit("Error: run  pip install py-solc-x  first")

    print("Installing solc 0.8.20…")
    install_solc("0.8.20", show_progress=True)

    source = SOL_PATH.read_text()
    print("Compiling ChainScoreAnchor.sol…")
    compiled = compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version="0.8.20",
    )
    contract_id = "<stdin>:ChainScoreAnchor"
    abi = compiled[contract_id]["abi"]
    bytecode = compiled[contract_id]["bin"]

    # Deploy
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(account.address)

    tx = Contract.constructor(account.address).build_transaction({
        "from":     account.address,
        "nonce":    nonce,
        "gasPrice": int(w3.eth.gas_price * 1.2),
        "chainId":  w3.eth.chain_id,
    })
    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    print(f"\nDeployment tx:  https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
    print("Waiting for confirmation…")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    contract_address = receipt["contractAddress"]
    print(f"\n✓ ChainScoreAnchor deployed at: {contract_address}")
    print(f"  Etherscan: https://sepolia.etherscan.io/address/{contract_address}")
    print(f"\nAdd to .env and Render:\n  CONTRACT_ADDRESS={contract_address}")


if __name__ == "__main__":
    main()
