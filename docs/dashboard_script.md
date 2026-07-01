# Dashboard Presentation Script
**~3 minutes · Read while showing http://localhost:3000**

---

`[DO]` — Open http://localhost:3000 with the default wallet already loaded.

"This is the ChainScore analyst dashboard. Let me score a real wallet."

`[DO]` — Paste the wallet address and click Score:
```
0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```
*(This is Vitalik Buterin's public wallet — well known, safe to use as a demo.)*

---

**Gauge:**
"The credit score comes back on a 0–1000 scale — same direction as FICO, higher is safer. The arc fills to the score position and changes color by risk tier."

**KPI cards:**
"Risk tier, probability of default, and the validity window. The model gives a calibrated PD — not just a ranking, an actual probability estimate."

**SHAP chart:**
"This is the explainability layer. Each bar is a feature that pushed the score up or down for this specific wallet. Wallet age and repayment ratio are the top positive signals here — exactly what a credit analyst would expect. This is what separates a scoring model from a black box."

`[DO]` — Click **Methodology** in the nav.

"The methodology page documents the full pipeline: the 43 features, the train/test split approach, the evaluation metrics. Written at the level a quant reviewer would expect."

---

## Wallet addresses for demo

| Wallet | Profile | Expected score |
|---|---|---|
| `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` | Vitalik — very active, long history | High (700–800) |
| `0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B` | Early Ethereum contributor | Medium–High |
| `0x1db3439a222c519ab44bb1144fc28167b4fa6ee6` | Active DeFi user | Medium |

> Use Vitalik's wallet as the primary demo — it's publicly known, loads fast from cache on the second call, and will score well, which makes the gauge visually clear.
