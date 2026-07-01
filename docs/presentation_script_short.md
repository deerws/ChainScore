# ChainScore — Short Presentation Script
**~8 minutes · Read while demoing**

> `[DO]` = action on screen · `[MOCK]` = placeholder data · `[REAL]` = live from model/API

---

## 1. What it is (30 sec)

"ChainScore is an on-chain credit scoring system for Ethereum wallets. DeFi lending is permissionless — no credit checks. When a borrower's collateral drops below the threshold, Aave force-sells it. We use that liquidation history as a default label and build a FICO-style score from public blockchain data."

---

## 2. Show the API running (3 min)

`[DO]` — Start the API:
```bash
source .venv/bin/activate
python -m uvicorn src.api.main:app --reload --port 8000
```

`[DO]` — Open `http://localhost:8000/docs`

"Five endpoints. Let me score a wallet live."

`[DO]` — Run:
```bash
curl -s -X POST http://localhost:8000/v1/score \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "include_shap": true}' \
  | python3 -m json.tool
```

`[REAL]` "This hits Etherscan right now, computes 43 behavioral features, runs them through the calibrated model, and returns a 0–1000 score, a probability of default, and SHAP factors explaining why. Second call for the same wallet is cached — 50ms instead of 3–5 seconds."

`[DO]` — Run the portfolio endpoint:
```bash
curl -s -X POST http://localhost:8000/v1/portfolio \
  -H "Content-Type: application/json" \
  -d '{"wallet_addresses": ["0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B", "0x1db3439a222c519ab44bb1144fc28167b4fa6ee6"]}' \
  | python3 -m json.tool
```

"Portfolio endpoint aggregates risk across wallets — average PD, VaR 95%, CVaR. Credit desk vocabulary applied to DeFi."

---

## 3. Show the dashboard (2 min)

`[DO]` — `cd frontend && bun run dev` → open `http://localhost:3000`

"Institutional-style analyst interface. Enter a wallet address and score it."

`[DO]` — Type a wallet and click Score.

`[REAL]` "Score gauge, risk tier, PD, and SHAP chart — all live from the API."

`[MOCK]` "Wallet stats and protocol table use illustrative values — in production these come from the same indexing pipeline."

`[DO]` — Click Methodology in the nav.

"Methodology page covers the full pipeline: feature families, model choices, evaluation metrics."

---

## 4. Model results (1 min)

`[DO]` — Show `reports/figures/roc_curves.png` and `reports/figures/shap_summary.png`

"Trained on 8,800 labeled wallets — 49,748 Aave liquidation events as default labels. Logistic Regression achieves ROC-AUC 0.671, KS Statistic 0.33, Gini 0.34. No hyperparameter tuning. KS above 0.20 is the industry threshold for meaningful scorecard discrimination.

SHAP shows wallet age and repayment ratio as top signals — exactly what a credit analyst would expect."

---

## 5. Close (30 sec)

"End-to-end: data engineering pipeline, 43-feature behavioral model, calibrated scoring, REST API with caching, institutional dashboard with SHAP explainability, and a Solidity contract for on-chain score auditability — not yet deployed, that's Phase 5.

The methodology is standard credit risk scorecard work applied to blockchain data instead of bank statements."
