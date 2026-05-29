"""Polymarket public-read signal provider for decision-support evidence."""

from __future__ import annotations

import json
import re
import ssl
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .common import utc_now


GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
POLYMARKET_SITE_URL = "https://polymarket.com"
ALLOWED_RELEVANCE_TIERS = {"macro_regime", "sector_linked", "ticker_or_company_linked"}
MAX_QUERY_TERMS = 8

DEFAULT_MACRO_QUERY_TERMS = (
    "Federal Reserve",
    "inflation",
    "US dollar",
    "oil price",
    "tariffs China",
    "geopolitical conflict",
)
MACRO_KEYWORDS = {
    "fed",
    "federal reserve",
    "fomc",
    "rate cut",
    "interest rate",
    "inflation",
    "cpi",
    "pce",
    "dollar",
    "usd",
    "dxy",
    "oil",
    "brent",
    "wti",
    "treasury",
    "yield",
    "recession",
    "unemployment",
    "jobs",
    "tariff",
    "tariffs",
    "china",
    "taiwan",
    "war",
    "geopolitical",
    "election",
    "policy",
}
LOW_SIGNAL_KEYWORDS = {
    "nba",
    "nfl",
    "mlb",
    "nhl",
    "ufc",
    "soccer",
    "football",
    "cricket",
    "tennis",
    "grammy",
    "oscar",
    "movie",
    "celebrity",
    "music",
    "album",
    "esports",
    "gaming",
}
PURE_CRYPTO_KEYWORDS = {
    "bitcoin",
    "btc",
    "ethereum",
    "eth",
    "solana",
    "sol",
    "memecoin",
    "crypto",
}


JsonTransport = Callable[[str, float], Any]


@dataclass
class PolymarketSignalResponse:
    context: dict[str, Any]
    source_log: list[dict[str, Any]] = field(default_factory=list)
    source_capability_matrix: list[dict[str, Any]] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class PolymarketMacroSignalProvider:
    """Fetch macro and strongly linked Polymarket signals without trading auth."""

    def __init__(
        self,
        *,
        base_url: str = GAMMA_BASE_URL,
        timeout: float = 4.0,
        transport: JsonTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport or self._urlopen_json

    def capability_matrix(self) -> list[dict[str, Any]]:
        return [
            {
                "source_name": "Polymarket Gamma/CLOB public read APIs",
                "source_type": "public_prediction_market_data",
                "priority": 5,
                "capabilities": [
                    "prediction_market_search",
                    "macro_event_probabilities",
                    "event_volume_liquidity_context",
                    "public_read_only_prices",
                ],
                "status": "available_when_network_allows",
                "last_checked_at": utc_now(),
                "fallback_to": [],
                "limitations": [
                    "Prediction-market evidence only; not a substitute for quotes, filings, announcements, or iFinD data.",
                    "Read-only integration; no login, wallet, order, position, or trading endpoints are used.",
                ],
            }
        ]

    def fetch_context(
        self,
        *,
        ticker: str,
        market: str,
        security_master: dict[str, Any] | None = None,
        query_terms: list[str] | None = None,
        max_markets: int = 5,
        lookback_days: int = 7,
        snapshot_root: Path | None = None,
    ) -> PolymarketSignalResponse:
        retrieved_at = utc_now()
        terms = build_query_terms(ticker, market, security_master, query_terms)
        source_log: list[dict[str, Any]] = []
        errors: list[str] = []
        raw_markets: list[dict[str, Any]] = []

        for term in terms:
            params = {
                "q": term,
                "events_status": "open",
                "limit_per_type": max(1, min(max_markets, 20)),
                "search_profiles": "false",
            }
            endpoint = "/public-search"
            try:
                payload = self._request_json(endpoint, params)
                markets = extract_markets(payload)
                raw_markets.extend(markets)
                source_log.append(
                    {
                        "source_name": "Polymarket Gamma API",
                        "source_type": "public_prediction_market_data",
                        "endpoint_or_interface": f"GET {endpoint}",
                        "parameters": params,
                        "retrieved_at": retrieved_at,
                        "status": "ok",
                        "row_count": len(markets),
                        "missing_fields": [],
                        "limitations": ["Search results are filtered to macro and strongly linked events before use."],
                    }
                )
            except Exception as exc:  # noqa: BLE001 - provider must degrade to source_gap
                errors.append(repr(exc))
                source_log.append(
                    {
                        "source_name": "Polymarket Gamma API",
                        "source_type": "public_prediction_market_data",
                        "endpoint_or_interface": f"GET {endpoint}",
                        "parameters": params,
                        "retrieved_at": retrieved_at,
                        "status": "source_gap",
                        "missing_fields": ["prediction_market_search"],
                        "limitations": [f"Polymarket public search failed for query={term!r}."],
                    }
                )

        if not raw_markets:
            for endpoint in ("/events", "/markets"):
                request_params = {
                    "active": "true",
                    "closed": "false",
                    "limit": max(10, min(max_markets * 5, 100)),
                }
                log_params = {**request_params, "local_filter_terms": terms}
                try:
                    payload = self._request_json(endpoint, request_params)
                    markets = extract_markets(payload)
                    raw_markets.extend(markets)
                    source_log.append(
                        {
                            "source_name": "Polymarket Gamma API",
                            "source_type": "public_prediction_market_data",
                            "endpoint_or_interface": f"GET {endpoint}",
                            "parameters": log_params,
                            "retrieved_at": retrieved_at,
                            "status": "ok",
                            "row_count": len(markets),
                            "missing_fields": [],
                            "limitations": ["Fallback collection results are locally filtered by relevance before use."],
                        }
                    )
                    if raw_markets:
                        break
                except Exception as exc:  # noqa: BLE001 - fallback must not block core decision support
                    errors.append(repr(exc))
                    source_log.append(
                        {
                            "source_name": "Polymarket Gamma API",
                            "source_type": "public_prediction_market_data",
                            "endpoint_or_interface": f"GET {endpoint}",
                            "parameters": log_params,
                            "retrieved_at": retrieved_at,
                            "status": "source_gap",
                            "missing_fields": ["prediction_market_collection"],
                            "limitations": [f"Polymarket fallback collection fetch failed for endpoint={endpoint!r}."],
                        }
                    )

        if errors and not raw_markets:
            context = empty_context(
                status="source_gap",
                retrieved_at=retrieved_at,
                query_terms=terms,
                limitations=[
                    "Polymarket macro/strongly-linked evidence could not be retrieved.",
                    "Core technical and market-data decision support should continue with this source gap disclosed.",
                ],
                source_ref=source_refs_for_polymarket(source_log),
            )
            context["lookback_days"] = lookback_days
            return PolymarketSignalResponse(
                context=context,
                source_log=source_log,
                source_capability_matrix=self.capability_matrix(),
                missing_data=["Polymarket macro/strongly-linked prediction-market context unavailable."],
                errors=errors,
            )

        markets = select_relevant_markets(raw_markets, terms, max_markets)
        if not markets:
            context = empty_context(
                status="no_related_markets",
                retrieved_at=retrieved_at,
                query_terms=terms,
                limitations=[
                    "No macro or strongly related Polymarket markets passed the relevance filter.",
                    "Do not infer prediction-market evidence from low-relevance or entertainment/sports markets.",
                ],
                source_ref=source_refs_for_polymarket(source_log),
            )
            context["lookback_days"] = lookback_days
            return PolymarketSignalResponse(
                context=context,
                source_log=source_log,
                source_capability_matrix=self.capability_matrix(),
                missing_data=["No macro or strongly related Polymarket markets were found."],
                errors=errors,
            )

        previous = load_latest_snapshot(snapshot_root)
        selected = [normalize_market(market, source_refs_for_polymarket(source_log)) for market in markets]
        signal_changes = compute_signal_changes(selected, previous)
        for market in selected:
            change = signal_changes.get(market["market_key"])
            if change:
                market["change"] = change
        save_latest_snapshot(snapshot_root, selected, retrieved_at)

        summary = summarize_context(selected, signal_changes)
        context = {
            "status": "available",
            "retrieved_at": retrieved_at,
            "lookback_days": lookback_days,
            "query_terms": terms,
            "selected_markets": selected,
            "macro_summary": summary,
            "signal_changes": list(signal_changes.values()),
            "relevance_policy": {
                "allowed_tiers": sorted(ALLOWED_RELEVANCE_TIERS),
                "excluded_topics": sorted(LOW_SIGNAL_KEYWORDS),
                "pure_crypto_noise_filtered": True,
                "selection_note": "Use only macro regime, sector-linked, or explicit company/ticker-linked events as auxiliary evidence.",
            },
            "limitations": [
                "Prediction markets may reflect sample bias, low liquidity, wide spreads, or disputed resolution wording.",
                "Polymarket evidence is auxiliary and must not override sourced prices, filings, announcements, or risk controls.",
                "Probabilities are market-implied and not deterministic forecasts.",
            ],
            "source_ref": source_refs_for_polymarket(source_log),
        }
        return PolymarketSignalResponse(
            context=context,
            source_log=source_log,
            source_capability_matrix=self.capability_matrix(),
            missing_data=[],
            errors=errors,
        )

    def _request_json(self, endpoint: str, params: dict[str, Any]) -> Any:
        query = urllib.parse.urlencode(params)
        url = f"{self.base_url}{endpoint}?{query}"
        return self.transport(url, self.timeout)

    @staticmethod
    def _urlopen_json(url: str, timeout: float) -> Any:
        try:
            import certifi  # type: ignore
            import requests  # type: ignore

            response = requests.get(
                url,
                headers={"User-Agent": "financial-codex-workspace/1.0"},
                timeout=timeout,
                verify=certifi.where(),
            )
            response.raise_for_status()
            return response.json()
        except ImportError:
            pass
        request = urllib.request.Request(url, headers={"User-Agent": "financial-codex-workspace/1.0"})
        with urllib.request.urlopen(request, timeout=timeout, context=default_ssl_context()) as response:  # noqa: S310 - fixed public API URL
            raw = response.read().decode("utf-8")
        return json.loads(raw)


def build_query_terms(
    ticker: str,
    market: str,
    security_master: dict[str, Any] | None,
    user_terms: list[str] | None,
) -> list[str]:
    terms: list[str] = []
    terms.extend(user_terms or [])
    terms.extend(DEFAULT_MACRO_QUERY_TERMS)
    if market == "a_share":
        terms.extend(["China policy", "China economy"])
    if security_master:
        for key in ("name", "company_name", "industry", "sector", "group"):
            value = security_master.get(key)
            if isinstance(value, str) and value.strip():
                terms.append(value.strip())
    if ticker:
        terms.append(ticker)
    return dedupe_terms(terms)[:MAX_QUERY_TERMS]


def default_ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001 - certifi is optional
        return ssl.create_default_context()


def dedupe_terms(terms: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for term in terms:
        clean = " ".join(str(term).split())
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(clean)
    return result


def extract_markets(payload: Any) -> list[dict[str, Any]]:
    markets: list[dict[str, Any]] = []
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        candidates = []
        for key in ("markets", "market", "events", "event"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates.extend(value)
            elif isinstance(value, dict):
                candidates.append(value)
    else:
        return []

    for item in candidates:
        if not isinstance(item, dict):
            continue
        nested = item.get("markets")
        if isinstance(nested, list):
            for market in nested:
                if isinstance(market, dict):
                    merged = {**market}
                    for event_key in ("title", "slug", "category"):
                        if event_key not in merged and item.get(event_key):
                            merged[f"event_{event_key}"] = item.get(event_key)
                    markets.append(merged)
            continue
        markets.append(item)
    return markets


def select_relevant_markets(raw_markets: list[dict[str, Any]], query_terms: list[str], max_markets: int) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for market in raw_markets:
        if not market_is_open(market):
            continue
        key = str(market.get("id") or market.get("conditionId") or market.get("slug") or market.get("marketSlug") or "")
        if key and key in seen:
            continue
        relevance = classify_relevance(market, query_terms)
        if relevance["relevance_tier"] is None:
            continue
        if key:
            seen.add(key)
        ranked.append({**market, **relevance})
    ranked.sort(key=lambda item: (item.get("relevance_score") or 0, numeric_value(item.get("volume")) or 0), reverse=True)
    return ranked[: max(1, max_markets)]


def market_is_open(market: dict[str, Any]) -> bool:
    if market.get("closed") is True:
        return False
    if market.get("active") is False:
        return False
    return True


def classify_relevance(market: dict[str, Any], query_terms: list[str]) -> dict[str, Any]:
    text = market_text(market)
    if has_any(text, LOW_SIGNAL_KEYWORDS):
        return {"relevance_tier": None, "relevance_score": 0, "relevance_reason": "low_signal_topic_filtered"}
    has_macro = has_any(text, MACRO_KEYWORDS)
    has_crypto = has_any(text, PURE_CRYPTO_KEYWORDS)
    term_hits = [term for term in query_terms if term.lower() in text and len(term) >= 3]
    if has_crypto and not has_macro and not term_hits:
        return {"relevance_tier": None, "relevance_score": 0, "relevance_reason": "pure_crypto_noise_filtered"}
    if has_macro:
        return {"relevance_tier": "macro_regime", "relevance_score": 90 + min(len(term_hits), 5), "relevance_reason": "matched_macro_regime_keywords"}
    if term_hits:
        tier = "ticker_or_company_linked" if any(re.search(r"\d{6}\.(sh|sz|bj)", term.lower()) for term in term_hits) else "sector_linked"
        return {
            "relevance_tier": tier,
            "relevance_score": 70 + min(len(term_hits), 10),
            "relevance_reason": "matched_query_terms: " + ", ".join(term_hits[:5]),
        }
    return {"relevance_tier": None, "relevance_score": 0, "relevance_reason": "no_macro_or_strong_link"}


def market_text(market: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("question", "title", "description", "slug", "marketSlug", "category", "event_title", "event_slug", "event_category"):
        value = market.get(key)
        if isinstance(value, str):
            parts.append(value)
    tags = market.get("tags")
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, dict):
                parts.append(str(tag.get("label") or tag.get("name") or tag))
            else:
                parts.append(str(tag))
    return " ".join(parts).lower()


def has_any(text: str, keywords: set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def normalize_market(market: dict[str, Any], source_ref: list[str]) -> dict[str, Any]:
    outcomes = decode_jsonish_list(market.get("outcomes"))
    prices = [numeric_value(value) for value in decode_jsonish_list(market.get("outcomePrices"))]
    implied_probability, top_outcome = top_probability(outcomes, prices)
    slug = str(market.get("marketSlug") or market.get("slug") or market.get("event_slug") or "")
    market_key = str(market.get("id") or market.get("conditionId") or slug or market.get("question") or "unknown")
    return {
        "market_key": market_key,
        "market_id": market.get("id"),
        "condition_id": market.get("conditionId"),
        "question": market.get("question") or market.get("title") or market.get("event_title"),
        "slug": slug,
        "url": build_market_url(slug),
        "category": market.get("category") or market.get("event_category"),
        "outcomes": outcomes,
        "outcome_prices": prices,
        "top_outcome": top_outcome,
        "implied_probability": implied_probability,
        "probability_change_24h": first_numeric(market, ("oneDayPriceChange", "priceChange24hr", "priceChange1d")),
        "probability_change_7d": first_numeric(market, ("oneWeekPriceChange", "priceChange7d", "priceChange1wk")),
        "volume": numeric_value(market.get("volume")),
        "liquidity": numeric_value(market.get("liquidity")),
        "open_interest": first_numeric(market, ("openInterest", "open_interest")),
        "end_date": market.get("endDate") or market.get("end_date"),
        "active": market.get("active"),
        "closed": market.get("closed"),
        "resolution_source": market.get("resolutionSource") or market.get("resolution_source"),
        "relevance_tier": market.get("relevance_tier"),
        "relevance_score": market.get("relevance_score"),
        "relevance_reason": market.get("relevance_reason"),
        "source_ref": source_ref,
    }


def decode_jsonish_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return [part.strip() for part in value.split(",") if part.strip()]
        return decoded if isinstance(decoded, list) else [decoded]
    return []


def numeric_value(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None
    return None


def first_numeric(market: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = numeric_value(market.get(key))
        if value is not None:
            return value
    return None


def top_probability(outcomes: list[Any], prices: list[float | None]) -> tuple[float | None, str | None]:
    best_probability: float | None = None
    best_outcome: str | None = None
    for index, price in enumerate(prices):
        if price is None:
            continue
        if best_probability is None or price > best_probability:
            best_probability = price
            best_outcome = str(outcomes[index]) if index < len(outcomes) else None
    return best_probability, best_outcome


def build_market_url(slug: str) -> str | None:
    if not slug:
        return None
    return f"{POLYMARKET_SITE_URL}/event/{slug}"


def load_latest_snapshot(snapshot_root: Path | None) -> dict[str, Any]:
    if snapshot_root is None:
        return {}
    path = snapshot_root / "latest.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    markets = value.get("markets") if isinstance(value, dict) else None
    return markets if isinstance(markets, dict) else {}


def save_latest_snapshot(snapshot_root: Path | None, markets: list[dict[str, Any]], retrieved_at: str) -> None:
    if snapshot_root is None:
        return
    snapshot_root.mkdir(parents=True, exist_ok=True)
    path = snapshot_root / "latest.json"
    payload = {
        "updated_at": retrieved_at,
        "markets": {
            market["market_key"]: {
                "question": market.get("question"),
                "implied_probability": market.get("implied_probability"),
                "volume": market.get("volume"),
                "liquidity": market.get("liquidity"),
                "open_interest": market.get("open_interest"),
                "retrieved_at": retrieved_at,
            }
            for market in markets
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compute_signal_changes(markets: list[dict[str, Any]], previous: dict[str, Any]) -> dict[str, dict[str, Any]]:
    changes: dict[str, dict[str, Any]] = {}
    for market in markets:
        key = market["market_key"]
        baseline = previous.get(key) if isinstance(previous.get(key), dict) else None
        change = {
            "market_key": key,
            "baseline_status": "matched_local_history" if baseline else "no_local_history",
            "probability_delta": delta(market.get("implied_probability"), (baseline or {}).get("implied_probability")),
            "volume_delta": delta(market.get("volume"), (baseline or {}).get("volume")),
            "liquidity_delta": delta(market.get("liquidity"), (baseline or {}).get("liquidity")),
            "open_interest_delta": delta(market.get("open_interest"), (baseline or {}).get("open_interest")),
            "previous_retrieved_at": (baseline or {}).get("retrieved_at"),
        }
        changes[key] = change
    return changes


def delta(current: Any, previous: Any) -> float | None:
    current_value = numeric_value(current)
    previous_value = numeric_value(previous)
    if current_value is None or previous_value is None:
        return None
    return current_value - previous_value


def summarize_context(markets: list[dict[str, Any]], changes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    top = markets[0] if markets else {}
    matched_history = sum(1 for change in changes.values() if change.get("baseline_status") == "matched_local_history")
    return {
        "market_count": len(markets),
        "top_market": top.get("question"),
        "top_outcome": top.get("top_outcome"),
        "top_implied_probability": top.get("implied_probability"),
        "matched_local_history_count": matched_history,
        "summary_text": (
            "Polymarket macro/strongly-linked prediction markets are available as auxiliary evidence."
            if markets
            else "No usable Polymarket evidence is available."
        ),
    }


def empty_context(
    *,
    status: str,
    retrieved_at: str,
    query_terms: list[str],
    limitations: list[str],
    source_ref: list[str],
) -> dict[str, Any]:
    return {
        "status": status,
        "retrieved_at": retrieved_at,
        "query_terms": query_terms,
        "selected_markets": [],
        "macro_summary": {"market_count": 0, "summary_text": "No usable Polymarket evidence is available."},
        "signal_changes": [],
        "relevance_policy": {
            "allowed_tiers": sorted(ALLOWED_RELEVANCE_TIERS),
            "pure_crypto_noise_filtered": True,
        },
        "limitations": limitations,
        "source_ref": source_ref,
    }


def default_prediction_market_context(reason: str = "Polymarket context was not supplied.") -> dict[str, Any]:
    return empty_context(
        status="source_gap",
        retrieved_at=utc_now(),
        query_terms=[],
        limitations=[reason],
        source_ref=[],
    )


def source_refs_for_polymarket(source_log: list[dict[str, Any]]) -> list[str]:
    refs = []
    for index, entry in enumerate(source_log):
        if "polymarket" in str(entry.get("source_name", "")).lower():
            refs.append(f"source_log[{index}]")
    return refs
