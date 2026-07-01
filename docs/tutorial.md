# ChainScore — Getting Started Tutorial

## Prerequisites

- Python 3.11+ virtual environment set up (`source .venv/bin/activate`)
- `.env` file with `ALCHEMY_API_KEY` and `ETHERSCAN_API_KEY` configured
- Bun or Node 18+ for the frontend

---

## 1. Start the API

```bash
source .venv/bin/activate
python -m uvicorn src.api.main:app --reload --port 8000
```

Expected output:
```
[INFO] Ethereum client connected.
[INFO] Models loaded successfully.
Uvicorn running on http://127.0.0.1:8000
```

If you see `Ethereum client failed to connect`, check that your `ALCHEMY_API_KEY` in `.env` is valid.

Open the interactive docs at **http://localhost:8000/docs**

---

## 2. Score a wallet (API)

**Single wallet — terminal:**
```bash
curl -s -X POST http://localhost:8000/v1/score \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "include_shap": true}' \
  | python3 -m json.tool
```

**Single wallet — browser:**
```
http://localhost:8000/v1/score/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

**Response fields:**

| Field | Description |
|---|---|
| `score` | 0–1000 credit score (higher = safer) |
| `risk_tier` | `very_low` / `low` / `medium` / `high` / `very_high` |
| `probability_of_default` | Calibrated PD (0.0–1.0) |
| `top_factors` | SHAP explanation — which behaviors drove the score |
| `score_valid_until` | Validity window (30 days) |

---

## 3. Batch scoring (up to 20 wallets)

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

Failed wallets return an `error` field — the rest of the batch still completes.

---

## 4. Portfolio risk analysis (up to 100 wallets)

```bash
curl -s -X POST http://localhost:8000/v1/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_addresses": [
      "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
      "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B",
      "0x1db3439a222c519ab44bb1144fc28167b4fa6ee6"
    ],
    "name": "My portfolio"
  }' | python3 -m json.tool
```

Returns: `avg_pd`, `var_95` (PD at 95th percentile), `cvar_95` (expected shortfall), and a tier breakdown.

---

## 5. Start the dashboard

Open a second terminal (keep the API running):

```bash
cd frontend
bun install   # first time only
bun run dev
```

Open **http://localhost:3000**

**How to use:**
1. Paste any Ethereum wallet address (e.g. `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`) into the search bar
2. Click **Score**
3. The gauge, risk tier, PD, and SHAP chart update with live data from the API
4. Click **Methodology** in the nav to read the full technical documentation

> The dashboard requires the API to be running on `http://localhost:8000`.

---

## 6. Score a wallet from the CLI

```bash
source .venv/bin/activate
python -m src.models.predict 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

---

## 7. Run the full training pipeline (optional)

Only needed if you want to retrain the models from scratch:

```bash
python -m src.data.liquidation_collector          # collect default labels
python -m src.data.cohort_collector               # sample non-default wallets
python -m src.data.wallet_indexer \               # index transaction histories
    --wallet-list data/raw/wallet_list_full.json \
    --checkpoint  data/raw/indexer_checkpoint.json \
    --output-dir  data/raw/wallets
python -m src.features.builder                    # build feature matrix
python -m src.models.train                        # train + calibrate models
python -m src.models.evaluate                     # generate evaluation plots
```

Pre-trained models are already in `models/` — steps 1–6 can be skipped for a demo.

---

## Score interpretation

| Score | Risk tier | PD range | Credit analogue |
|:---:|---|:---:|---|
| 800–1000 | Very Low | < 20% | AAA – A |
| 650–799 | Low | 20–35% | BBB |
| 500–649 | Medium | 35–50% | BB |
| 300–499 | High | 50–70% | B |
| 0–299 | Very High | > 70% | CCC or below |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Ethereum client failed to connect` | Check `ALCHEMY_API_KEY` in `.env` |
| `Models not loaded` | Run `python -m src.models.train` first |
| Dashboard shows no score | Confirm API is running on port 8000 |
| Slow first response (3–5s) | Normal — Etherscan fetch. Repeated calls hit the 30-min cache (~50ms) |
