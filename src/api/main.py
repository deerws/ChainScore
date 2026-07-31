"""
ChainScore FastAPI service — serves real-time credit scores for Ethereum wallets.

Endpoints:
    GET  /health                          — liveness check
    POST /v1/score                        — score a single wallet address
    GET  /v1/score/{address}              — same via GET (for quick browser testing)
    POST /v1/batch                        — score up to 20 wallets in one request
    POST /v1/portfolio                    — aggregate risk for up to 100 wallets
    GET  /v1/watch/{address}/stream       — SSE live score stream (60s polling)

Authentication: API key via X-API-Key header (configured in .env).

Run locally:
    .venv/bin/python3 -m uvicorn src.api.main:app --reload --port 8000
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

import json

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.responses import StreamingResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware

from src.api.schemas import (
    AnchorResponse,
    BatchScoreRequest,
    BatchScoreResponse,
    BatchWalletResult,
    HealthResponse,
    OnChainRecord,
    PortfolioRequest,
    PortfolioStats,
    ScoreRequest,
    ScoreResponse,
    ShapFactor,
    TierBreakdown,
    VerifyResponse,
)
from src.blockchain.anchor import AnchorClient
from src.data.ethereum_client import EthereumClient
from src.models.predict import ChainScorePredictor

logger = logging.getLogger(__name__)

# ── Globals loaded at startup ──────────────────────────────────────────────
_client: EthereumClient | None = None
_predictor: ChainScorePredictor | None = None
_ethereum_connected: bool = False
_anchor: AnchorClient | None = None

# ── Score cache (in-memory, 30-min TTL) ───────────────────────────────────
_CACHE_TTL = 1800  # seconds
_score_cache: dict[str, tuple[ScoreResponse, float]] = {}  # key → (result, ts)


def _cache_get(wallet: str) -> ScoreResponse | None:
    key = wallet.lower()
    entry = _score_cache.get(key)
    if entry and time.monotonic() - entry[1] < _CACHE_TTL:
        logger.info("Cache hit for %s", wallet)
        return entry[0]
    if entry:
        del _score_cache[key]
    return None


def _cache_set(wallet: str, result: ScoreResponse) -> None:
    _score_cache[wallet.lower()] = (result, time.monotonic())

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def _check_api_key(key: str | None = Security(api_key_header)) -> str:
    secret = os.getenv("API_KEY_SECRET", "")
    if not secret:
        return "no-auth"  # Auth disabled when secret not configured
    if key != secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models and establish Ethereum connection at startup."""
    global _client, _predictor, _ethereum_connected, _anchor

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    try:
        _client = EthereumClient.from_env()
        _ = _client.get_latest_block()
        _ethereum_connected = True
        logger.info("Ethereum client connected.")
    except Exception as exc:
        logger.warning(f"Ethereum client failed to connect: {exc}")
        _ethereum_connected = False

    try:
        _predictor = ChainScorePredictor()
        _predictor._load()
    except FileNotFoundError as exc:
        logger.warning(f"Models not loaded: {exc}")
        _predictor = None

    try:
        _anchor = AnchorClient()
        logger.info("Blockchain anchoring enabled (Sepolia).")
    except RuntimeError as exc:
        logger.warning(f"Blockchain anchoring disabled: {exc}")
        _anchor = None

    yield

    logger.info("Shutting down ChainScore API.")


# ── App setup ──────────────────────────────────────────────────────────────

_DESCRIPTION = """
ChainScore assigns **0–1000 credit scores** to Ethereum wallets using on-chain behavioral
analysis and a LightGBM model trained on Aave V2 liquidation events.

### Score interpretation
| Range | Risk tier | Credit analogue |
|-------|-----------|-----------------|
| 800–1000 | Very Low | AAA–A |
| 650–799 | Low | BBB |
| 500–649 | Medium | BB |
| 300–499 | High | B |
| 0–299 | Very High | CCC or below |

### Authentication
Pass your API key in the `X-API-Key` header. When no `API_KEY_SECRET` is configured
(local dev), the header is optional.

### Rate limiting
The scoring pipeline fetches live transaction data from Etherscan. Allow ~2–5 s per wallet.
Batch requests score wallets sequentially; bursts above 20 wallets should be split across calls.
"""

_TAGS = [
    {
        "name": "scoring",
        "description": "Score one or many Ethereum wallets.",
    },
    {
        "name": "system",
        "description": "Service health and status.",
    },
]

app = FastAPI(
    title="ChainScore API",
    description=_DESCRIPTION,
    version="1.0.0",
    openapi_tags=_TAGS,
    contact={
        "name": "André Pinheiro Paes",
        "email": "paes.andre33@gmail.com",
        "url": "https://github.com/deerws/ChainScore",
    },
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Service health check",
    description="Returns `ok` when the model is loaded and Ethereum client is reachable; `degraded` otherwise.",
)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if _ethereum_connected and _predictor is not None else "degraded",
        model_loaded=_predictor is not None,
        ethereum_connected=_ethereum_connected,
        cached_wallets=len(_score_cache),
    )


def _build_score_response(wallet: str, include_shap: bool) -> ScoreResponse:
    cached = _cache_get(wallet)
    if cached is not None:
        # Re-use cached result; if caller doesn't want SHAP, strip factors
        if not include_shap:
            return cached.model_copy(update={"top_factors": []})
        return cached

    if _predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Models not loaded. Run training pipeline first.",
        )
    if _client is None or not _ethereum_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ethereum client not connected. Check ALCHEMY_API_KEY.",
        )

    result = _predictor.score_wallet(wallet, _client, use_shap=True)
    valid_until = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")

    response = ScoreResponse(
        wallet_address=result.wallet_address,
        score=result.score,
        risk_tier=result.risk_tier,
        probability_of_default=result.probability_of_default,
        top_factors=[
            ShapFactor(
                feature=f["feature"],
                shap_value=f["shap_value"],
                direction=f["direction"],
            )
            for f in result.top_factors
        ],
        model_version=result.model_version,
        score_valid_until=valid_until,
    )
    _cache_set(wallet, response)

    if not include_shap:
        return response.model_copy(update={"top_factors": []})
    return response


@app.post(
    "/v1/score",
    response_model=ScoreResponse,
    tags=["scoring"],
    summary="Score a single wallet",
    description=(
        "Fetch live on-chain data for the given Ethereum address, run it through the "
        "LightGBM model, and return a 0–1000 ChainScore with calibrated PD. "
        "Optionally includes top SHAP factors explaining the score."
    ),
)
async def score_wallet_post(
    request: ScoreRequest,
    _: str = Depends(_check_api_key),
) -> ScoreResponse:
    return _build_score_response(request.wallet_address, request.include_shap)


@app.get(
    "/v1/score/{wallet_address}",
    response_model=ScoreResponse,
    tags=["scoring"],
    summary="Score a single wallet (GET)",
    description="Identical to `POST /v1/score` but accepts the address as a path parameter — convenient for browser testing and quick curl calls.",
)
async def score_wallet_get(
    wallet_address: str,
    include_shap: bool = True,
    _: str = Depends(_check_api_key),
) -> ScoreResponse:
    if not wallet_address.startswith("0x") or len(wallet_address) != 42:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="wallet_address must be a 42-character hex string starting with 0x",
        )
    return _build_score_response(wallet_address, include_shap)


def _score_wallet_safe(wallet: str, include_shap: bool) -> BatchWalletResult:
    """Score one wallet, catching all errors so the batch never aborts."""
    try:
        resp = _build_score_response(wallet, include_shap)
        return BatchWalletResult(
            wallet_address=wallet,
            score=resp.score,
            risk_tier=resp.risk_tier,
            probability_of_default=resp.probability_of_default,
            top_factors=resp.top_factors,
        )
    except HTTPException as exc:
        return BatchWalletResult(wallet_address=wallet, error=exc.detail)
    except Exception as exc:
        logger.exception("Unexpected error scoring %s", wallet)
        return BatchWalletResult(wallet_address=wallet, error=str(exc))


@app.post(
    "/v1/batch",
    response_model=BatchScoreResponse,
    tags=["scoring"],
    summary="Score multiple wallets (batch)",
    description=(
        "Score up to **20** Ethereum wallets in a single request. "
        "Wallets are scored sequentially to stay within Etherscan rate limits (~5 req/s). "
        "Failed wallets are returned with an `error` field rather than aborting the whole batch. "
        "SHAP factors are disabled by default for batch requests (set `include_shap=true` to enable, but expect slower responses)."
    ),
)
async def batch_score(
    request: BatchScoreRequest,
    _: str = Depends(_check_api_key),
) -> BatchScoreResponse:
    results: list[BatchWalletResult] = []
    for i, wallet in enumerate(request.wallet_addresses):
        result = await asyncio.to_thread(_score_wallet_safe, wallet, request.include_shap)
        results.append(result)
        if i < len(request.wallet_addresses) - 1:
            await asyncio.sleep(0.5)

    succeeded = sum(1 for r in results if r.error is None)
    first_ok = next((r for r in results if r.error is None), None)
    model_version = "lgbm_v1" if first_ok is not None else "unavailable"
    return BatchScoreResponse(
        results=results,
        total=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        model_version=model_version,
    )


@app.post(
    "/v1/portfolio",
    response_model=PortfolioStats,
    tags=["scoring"],
    summary="Portfolio risk aggregation",
    description=(
        "Score up to **100** wallets and return aggregate portfolio risk metrics: "
        "average PD, **VaR 95%** (PD at the 95th-percentile wallet), "
        "**CVaR 95%** (expected shortfall — mean PD of the worst 5%), "
        "tier breakdown, and high-risk concentration. "
        "This is the vocabulary of a credit risk desk applied to DeFi exposure."
    ),
)
async def portfolio_analysis(
    request: PortfolioRequest,
    _: str = Depends(_check_api_key),
) -> PortfolioStats:
    # Score all wallets sequentially (cache helps for repeated calls)
    results: list[BatchWalletResult] = []
    for i, wallet in enumerate(request.wallet_addresses):
        result = await asyncio.to_thread(_score_wallet_safe, wallet, False)
        results.append(result)
        if i < len(request.wallet_addresses) - 1:
            await asyncio.sleep(0.3)

    scored = [r for r in results if r.error is None and r.probability_of_default is not None]
    failed = len(results) - len(scored)

    if not scored:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No wallets could be scored successfully.",
        )

    import numpy as np
    pds = np.array([r.probability_of_default for r in scored])
    scores = np.array([r.score for r in scored])

    # VaR and CVaR
    var_95 = float(np.percentile(pds, 95))
    cvar_threshold = np.percentile(pds, 95)
    tail = pds[pds >= cvar_threshold]
    cvar_95 = float(tail.mean()) if len(tail) > 0 else var_95

    # Tier breakdown
    tier_order = ["very_low", "low", "medium", "high", "very_high"]
    tier_counts: dict[str, list[float]] = {t: [] for t in tier_order}
    for r in scored:
        if r.risk_tier in tier_counts:
            tier_counts[r.risk_tier].append(r.probability_of_default)

    tier_breakdown = [
        TierBreakdown(
            tier=t,
            count=len(pds_list),
            pct=round(len(pds_list) / len(scored) * 100, 1),
            avg_pd=round(float(np.mean(pds_list)), 4) if pds_list else 0.0,
        )
        for t, pds_list in tier_counts.items()
        if len(pds_list) > 0
    ]

    high_risk_count = sum(
        1 for r in scored if r.risk_tier in ("high", "very_high")
    )

    return PortfolioStats(
        n_wallets=len(results),
        n_scored=len(scored),
        n_failed=failed,
        avg_score=round(float(scores.mean()), 1),
        avg_pd=round(float(pds.mean()), 4),
        weighted_pd=round(float(pds.mean()), 4),
        var_95=round(var_95, 4),
        cvar_95=round(cvar_95, 4),
        concentration_high_risk=round(high_risk_count / len(scored), 4),
        tier_breakdown=tier_breakdown,
        model_version="lgbm_v1",
    )


# ── Real-time monitoring (SSE) ─────────────────────────────────────────────

_WATCH_POLL_INTERVAL = 60  # seconds between re-scores


@app.get(
    "/v1/watch/{address}/stream",
    tags=["monitoring"],
    summary="Watch a wallet — live score stream (SSE)",
    description=(
        "Opens a **Server-Sent Events** stream for a wallet address. "
        "Emits the current score immediately on connect, then re-scores every 60 s "
        "and pushes an update event whenever the score or risk tier changes. "
        "Connect with `EventSource` from the browser. "
        "The stream sends a `ping` event every 30 s to keep the connection alive."
    ),
    response_class=StreamingResponse,
)
async def watch_wallet_stream(
    address: str,
    _: str = Depends(_check_api_key),
) -> StreamingResponse:
    address = address.strip()
    if not address.startswith("0x") or len(address) != 42:
        raise HTTPException(status_code=400, detail="Invalid Ethereum address.")

    async def event_generator():
        last_score: int | None = None
        last_tier: str | None = None
        ping_counter = 0

        while True:
            # Score the wallet (uses cache when available)
            result = await asyncio.to_thread(_score_wallet_safe, address, False)

            if result.error:
                payload = json.dumps({"error": result.error, "wallet": address})
                yield f"event: error\ndata: {payload}\n\n"
            else:
                score = result.score
                tier = result.risk_tier
                changed = (score != last_score) or (tier != last_tier)

                event_data = json.dumps({
                    "wallet": address,
                    "score": score,
                    "risk_tier": tier,
                    "probability_of_default": result.probability_of_default,
                    "changed": changed,
                    "polled_at": datetime.utcnow().isoformat() + "Z",
                })

                event_type = "score_update" if changed else "score_unchanged"
                yield f"event: {event_type}\ndata: {event_data}\n\n"

                last_score = score
                last_tier = tier

            # Send ping every ~30s (half the poll interval) to keep connection alive
            await asyncio.sleep(_WATCH_POLL_INTERVAL / 2)
            ping_counter += 1
            yield f"event: ping\ndata: {json.dumps({'seq': ping_counter})}\n\n"

            await asyncio.sleep(_WATCH_POLL_INTERVAL / 2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )


# ── On-chain anchoring ─────────────────────────────────────────────────────

@app.post(
    "/v1/anchor",
    response_model=AnchorResponse,
    tags=["anchoring"],
    summary="Anchor a wallet score on Sepolia",
    description=(
        "Scores the wallet, computes a keccak256 commitment, and calls `anchorScore()` "
        "on the ChainScoreAnchor contract deployed on Sepolia testnet. "
        "Returns the Sepolia transaction hash and an Etherscan link. "
        "The contract address and oracle key must be configured via `CONTRACT_ADDRESS` "
        "and `DEPLOYER_PRIVATE_KEY` environment variables."
    ),
)
async def anchor_score(
    request: ScoreRequest,
    _: str = Depends(_check_api_key),
) -> AnchorResponse:
    if _anchor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Blockchain anchoring not configured. "
                "Set CONTRACT_ADDRESS and DEPLOYER_PRIVATE_KEY in your environment."
            ),
        )

    # Score first (uses cache if available)
    scored = await asyncio.to_thread(_score_wallet_safe, request.wallet_address, False)
    if scored.error or scored.score is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not score wallet: {scored.error}",
        )

    try:
        result = await asyncio.to_thread(
            _anchor.anchor_score, request.wallet_address, scored.score
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Blockchain transaction failed: {exc}",
        )

    return AnchorResponse(
        wallet_address=request.wallet_address,
        score=scored.score,
        **result,
    )


@app.get(
    "/v1/verify/{address}",
    response_model=VerifyResponse,
    tags=["anchoring"],
    summary="Verify a wallet's on-chain score record",
    description=(
        "Reads the ChainScoreAnchor contract on Sepolia and returns the stored commitment "
        "for the given wallet. Does not require any write operation — pure read call. "
        "Pass `score` and `valid_until` as query parameters to also verify the hash matches."
    ),
)
async def verify_score(
    address: str,
    score: int | None = None,
    valid_until: int | None = None,
) -> VerifyResponse:
    if _anchor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain anchoring not configured.",
        )

    address = address.strip()
    if not address.startswith("0x") or len(address) != 42:
        raise HTTPException(status_code=400, detail="Invalid Ethereum address.")

    try:
        record_data = await asyncio.to_thread(_anchor.get_record, address)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Contract read failed: {exc}",
        )

    if record_data is None:
        return VerifyResponse(wallet_address=address, anchored=False, is_valid=None, record=None)

    record = OnChainRecord(**record_data)
    is_valid: bool | None = None

    if score is not None and valid_until is not None:
        try:
            is_valid = await asyncio.to_thread(
                _anchor.verify, address, score, valid_until
            )
        except Exception:
            is_valid = None

    return VerifyResponse(
        wallet_address=address,
        anchored=True,
        is_valid=is_valid,
        record=record,
    )
