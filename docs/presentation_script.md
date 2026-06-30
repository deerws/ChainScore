# ChainScore — Presentation Script
**Live demo walkthrough · Read aloud while presenting**

> **Legend:**
> - `[DO]` — action to perform on screen
> - `[MOCK]` — this section uses placeholder data; acknowledge it to the audience
> - `[REAL]` — data comes live from the model/API

---

## 1. Opening (30 seconds)

"Good morning, professor. I'm going to walk you through ChainScore — an on-chain credit scoring system for Ethereum wallets.

The core problem is simple: DeFi lending protocols like Aave are permissionless. Anyone can borrow crypto with no identity check. When a borrower's collateral drops below the liquidation threshold, the protocol force-sells their assets — that's a default. ChainScore asks whether we can predict that event before it happens, using only public blockchain data.

The answer is yes. Let me show you how."

---

## 2. Architecture overview (1 minute)

`[DO]` — Open the GitHub repository or show the project folder structure.

"The system has four layers:

**One — Data pipeline.** We collected 49,748 liquidation events from the Aave V2 smart contract on Ethereum Mainnet. Those are our default labels. We paired them with 8,800 wallets that have full transaction histories indexed, giving us a labeled dataset for supervised learning.

**Two — Feature engineering.** For each wallet, we compute 43 behavioral features: how active it is, which DeFi protocols it uses, its repayment habits, gas patterns, and wallet age. Same questions a loan officer would ask — just answered from public blockchain data.

**Three — Machine learning model.** We train a Logistic Regression and a LightGBM model on a temporal train/test split — no data leakage. The score is calibrated via Platt scaling to give reliable probability estimates, not just rankings.

**Four — REST API and dashboard.** The model is served via FastAPI. There's a Next.js institutional dashboard for analysts, and a Solidity smart contract that anchors score hashes on-chain for auditability."

---

## 3. Model performance (1.5 minutes)

`[DO]` — Open `reports/figures/` and show plots, or open the README model performance section.

"Let's talk about the numbers. We're evaluating this exactly the way a credit risk team would.

`[REAL]` **ROC-AUC of 0.671** for Logistic Regression on 8,800 wallets. To put that in context: a random model scores 0.5, and a production consumer credit model typically sits at 0.72–0.80. We're in the right ballpark with zero hyperparameter tuning.

`[REAL]` **KS Statistic of 0.33.** This is the key metric in scorecard-grade credit models — it measures the maximum separation between the default and non-default distributions. Anything above 0.20 is considered meaningful discrimination.

`[REAL]` **Gini Coefficient of 0.34.** Equivalent to 2 × (AUC − 0.5). Industry benchmark for consumer credit is typically 0.40–0.60. We're approaching that range.

`[DO]` — Show the ROC curves plot: `reports/figures/roc_curves.png`

`[DO]` — Show the KS plot: `reports/figures/ks_plot.png`

`[DO]` — Show the SHAP summary: `reports/figures/shap_summary.png`

"The SHAP chart shows which features drive the predictions. Wallet age, repayment-to-borrow ratio, and protocol diversity are the top positive signals — exactly what a credit analyst would expect. This aligns with how FICO scores work: long history and consistent repayment behavior lower your risk tier."

---

## 4. Starting the API (30 seconds)

`[DO]` — Open a terminal and run:
```bash
source .venv/bin/activate
python -m uvicorn src.api.main:app --reload --port 8000
```

"The API starts in a few seconds. It loads the trained models and connects to the Ethereum client. Let me open the Swagger documentation."

`[DO]` — Open browser at `http://localhost:8000/docs`

"Five endpoints. Health check, single wallet scoring, GET version for quick browser tests, batch scoring for up to 20 wallets, and a portfolio endpoint that returns credit-desk vocabulary — average PD, VaR at the 95th percentile, CVaR — expected shortfall — and tier breakdown."

---

## 5. Live API demo (2 minutes)

### Health check
`[DO]` — In Swagger or terminal:
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

"Status OK, model loaded, Ethereum connected. Cache starts empty — zero wallets scored so far."

### Score a wallet (live)
`[DO]` — Run:
```bash
curl -s -X POST http://localhost:8000/v1/score \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "include_shap": true}' \
  | python3 -m json.tool
```

`[REAL]` "This is Vitalik Buterin's public wallet. The API fetches live transaction data from Etherscan right now, computes the 43 features, runs them through the calibrated LightGBM model, and returns a score.

You get: the 0–1000 credit score, the risk tier, the calibrated probability of default, SHAP factors explaining which behaviors drove the score up or down, the model version, and a validity window."

### Batch scoring
`[DO]` — Run:
```bash
curl -s -X POST http://localhost:8000/v1/batch \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_addresses": [
      "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
      "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"
    ]
  }' | python3 -m json.tool
```

"Batch endpoint scores multiple wallets. Failed wallets return an error field instead of aborting the whole request. Second call for the same wallet hits the 30-minute in-memory cache — about 50ms response time instead of 3–5 seconds."

### Portfolio risk
`[DO]` — Run:
```bash
curl -s -X POST http://localhost:8000/v1/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_addresses": [
      "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
      "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B",
      "0x1db3439a222c519ab44bb1144fc28167b4fa6ee6"
    ],
    "name": "Demo portfolio"
  }' | python3 -m json.tool
```

"The portfolio endpoint is designed for the B2B use case: a fintech or digital bank assessing their DeFi exposure. They send a list of wallets and get back: average PD, VaR at the 95th percentile — meaning the PD of the riskiest 5% — CVaR, which is the expected shortfall of that tail, and a tier breakdown. This is the vocabulary of a credit risk desk applied directly to blockchain data."

---

## 6. Dashboard demo (1.5 minutes)

`[DO]` — Open a second terminal:
```bash
cd frontend && bun run dev
```
Then open `http://localhost:3000`

"The dashboard is built for an institutional analyst workflow — dark mode, monospace fonts, the design language of Bloomberg terminals and risk systems."

`[DO]` — Type a wallet address in the search bar and press Score.

`[REAL]` "Score gauge, risk tier badge, probability of default — these come live from the API. The SHAP bar chart updates with the real explanation for that specific wallet."

`[MOCK]` "The wallet stats panel — age, active protocols, total repaid and borrowed — and the protocol exposure table are pre-populated with illustrative values. In production, these would be pulled from the same Etherscan indexing pipeline. I flagged this as a known gap."

`[DO]` — Click "Methodology" in the navigation.

"The about page documents the full methodology: feature families, risk tier definitions, data pipeline, train/test split approach, calibration, and the evaluation metrics — written at the level of detail a credit analyst or quant reviewer would expect."

---

## 7. Smart contract (30 seconds)

`[DO]` — Open `contracts/ChainScoreAnchor.sol`

"The smart contract anchors a cryptographic hash of each score on-chain. Lenders can verify that a score was issued at a specific time without trusting the ChainScore server. The contract is written and tested — deployment to Sepolia testnet is Phase 5, not yet done.

The verification call is one line:
```solidity
bool valid = anchor.verifyScore(wallet, score, validUntil, modelVersion);
```
"

---

## 8. What was delivered (30 seconds)

"To summarize what was built end-to-end:

- A full data engineering pipeline collecting 49,748 on-chain liquidation events and indexing 8,800 wallets with transaction history.
- A 43-feature behavioral scoring pipeline aligned with traditional credit risk methodology.
- Two trained and calibrated models — Logistic Regression and LightGBM — with KS 0.33 and ROC-AUC 0.671.
- A production-grade REST API with five endpoints, in-memory caching, and Swagger documentation.
- An institutional-style Next.js dashboard with live API integration and SHAP explainability.
- A Solidity smart contract for on-chain score auditability.

The smart contract deployment and full replacement of mock dashboard stats with live data are the remaining items in the roadmap."

---

## 9. Q&A prompts (if asked)

**"Why not use identity data?"**
> "DeFi is permissionless by design. There is no identity to query. On-chain behavior is the only signal available — which makes it genuinely novel for credit modeling."

**"How do you prevent Sybil attacks — someone creating a fresh wallet to appear low-risk?"**
> "Wallet age and activity span are two of the top predictive features. A new wallet with no history gets a low score regardless of other signals. It doesn't solve Sybil completely, but it significantly raises the cost."

**"Why Logistic Regression over LightGBM at this scale?"**
> "At 8,800 samples, LR still edges LightGBM on rank-ordering metrics — AUC, KS, Gini. This is well-documented in credit risk literature: gradient boosting tends to surpass linear models only above roughly 10,000 labeled samples. LightGBM wins on calibration — Brier score — which is why we keep both."

**"What's the business model?"**
> "B2B API access. DeFi lending protocols, DAOs, and fintechs targeting DeFi users are the primary customers. Pricing per API call or monthly subscription based on query volume."
