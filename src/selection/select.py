"""Common entry point for demonstration selection.

Contract (from the project work plan):

    select_examples(query, pool, k, strategy, seed) -> list[demo_id]

* ``query``: a dev/test record (dict with at least ``id`` and ``question_ur``),
  or a plain Urdu question string.
* ``pool``: list of demo-pool records (dicts with ``id``; similarity also
  needs ``question_ur``). Only the demo pool may be passed here - never dev or
  test records, and answers are never read.
* ``k``: number of demonstrations (2 for the pilot, 4 later).
* ``strategy``: "random" or "similarity" ("diversity" and "complexity" are
  designed but not implemented yet).
* ``seed``: integer from the experiment config. Used by "random"; accepted and
  ignored by "similarity", which is deterministic.

Selection uses the Urdu question for every language condition, so a query
receives the same demonstrations under U-U-U, U-U-E, U-E-E and E-E-E. Call
this once per (query, strategy) and reuse the IDs across the four conditions.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from .encoders import DEFAULT_ENCODER_ID, Encoder, SentenceTransformerEncoder
from .random import select_random
from .similarity import EmbeddingCache, select_similar

IMPLEMENTED_STRATEGIES = ("random", "similarity")
DEFERRED_STRATEGIES = ("diversity", "complexity")


class SelectionError(ValueError):
    """Raised for any invalid input to, or invalid output from, selection."""


# ---------------------------------------------------------------------------
# Configuration (call configure() once from the runner with config values)
# ---------------------------------------------------------------------------

_CONFIG: dict[str, Any] = {
    "encoder_id": DEFAULT_ENCODER_ID,
    "encoder_revision": None,
    "device": None,
    "cache_dir": "cache/embeddings",
    "text_field": "question_ur",
    "per_query_seed": True,
}
_DEFAULT_ENCODER: Encoder | None = None
_CACHES: dict[str, EmbeddingCache] = {}


def configure(**settings: Any) -> None:
    """Override selection settings, e.g. from configs/pilot.yaml.

    Keys: encoder_id, encoder_revision, device, cache_dir, text_field,
    per_query_seed. Resets the loaded encoder and caches.
    """
    global _DEFAULT_ENCODER
    unknown = set(settings) - set(_CONFIG)
    if unknown:
        raise SelectionError(f"Unknown selection setting(s): {sorted(unknown)}")
    _CONFIG.update(settings)
    _DEFAULT_ENCODER = None
    _CACHES.clear()


def get_config() -> dict[str, Any]:
    return dict(_CONFIG)


def get_default_encoder() -> Encoder:
    global _DEFAULT_ENCODER
    if _DEFAULT_ENCODER is None:
        _DEFAULT_ENCODER = SentenceTransformerEncoder(
            model_id=_CONFIG["encoder_id"],
            revision=_CONFIG["encoder_revision"],
            device=_CONFIG["device"],
        )
    return _DEFAULT_ENCODER


def get_cache(encoder: Encoder) -> EmbeddingCache:
    key = encoder.cache_key
    if key not in _CACHES:
        _CACHES[key] = EmbeddingCache(_CONFIG["cache_dir"], key)
    return _CACHES[key]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate_k(k: Any, pool_size: int) -> None:
    if isinstance(k, bool) or not isinstance(k, int):
        raise SelectionError(f"k must be an integer, got {k!r} ({type(k).__name__})")
    if k < 1:
        raise SelectionError(f"k must be at least 1, got {k}")
    if k > pool_size:
        raise SelectionError(f"k={k} is larger than the pool ({pool_size} items)")


def _validate_seed(seed: Any) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise SelectionError(f"seed must be an integer, got {seed!r}")


def _validate_pool(pool: Any, needs_text: str | None) -> list[str]:
    if not isinstance(pool, (list, tuple)):
        raise SelectionError(f"pool must be a list of records, got {type(pool).__name__}")
    if len(pool) == 0:
        raise SelectionError("pool is empty")
    ids: list[str] = []
    for i, rec in enumerate(pool):
        if not isinstance(rec, dict):
            raise SelectionError(f"pool item {i} is not a dict")
        rid = rec.get("id")
        if not isinstance(rid, str) or not rid.strip():
            raise SelectionError(f"pool item {i} has a missing or empty 'id'")
        if needs_text:
            text = rec.get(needs_text)
            if not isinstance(text, str) or not text.strip():
                raise SelectionError(f"pool item {rid!r} has a missing or empty {needs_text!r}")
        ids.append(rid)
    dupes = sorted({x for x in ids if ids.count(x) > 1})
    if dupes:
        raise SelectionError(f"duplicate pool IDs: {dupes}")
    return ids


def _query_key_and_text(query: Any, text_field: str, needs_text: bool) -> tuple[str, str | None, str | None]:
    """Return (stable key for seeding, query text or None, query id or None)."""
    if isinstance(query, str):
        if not query.strip():
            raise SelectionError("query string is empty")
        key = "text:" + hashlib.sha256(query.strip().encode("utf-8")).hexdigest()
        return key, query, None
    if isinstance(query, dict):
        qid = query.get("id")
        if not isinstance(qid, str) or not qid.strip():
            raise SelectionError("query record has a missing or empty 'id'")
        text = query.get(text_field)
        if needs_text and (not isinstance(text, str) or not text.strip()):
            raise SelectionError(f"query {qid!r} has a missing or empty {text_field!r}")
        return f"id:{qid}", text, qid
    raise SelectionError(f"query must be a record (dict) or a string, got {type(query).__name__}")


def _check_output(result: list[str], pool_ids: Sequence[str], k: int, strategy: str) -> None:
    if len(result) != k:
        raise SelectionError(f"{strategy} returned {len(result)} IDs, expected {k}")
    if len(set(result)) != k:
        raise SelectionError(f"{strategy} returned repeated IDs: {result}")
    unknown = [x for x in result if x not in set(pool_ids)]
    if unknown:
        raise SelectionError(f"{strategy} returned IDs not in the pool: {unknown}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def select_examples(
    query: dict | str,
    pool: Sequence[dict],
    k: int,
    strategy: str,
    seed: int,
    *,
    encoder: Encoder | None = None,
    cache: EmbeddingCache | None = None,
) -> list[str]:
    """Select k demonstration IDs from the pool for one query.

    Raises:
        SelectionError: invalid k, seed, pool, query, strategy name, data
            leakage (query ID inside the pool), or invalid selector output.
        NotImplementedError: strategy is "diversity" or "complexity".
    """
    if not isinstance(strategy, str):
        raise SelectionError(f"strategy must be a string, got {strategy!r}")
    strategy = strategy.strip().lower()
    if strategy in DEFERRED_STRATEGIES:
        raise NotImplementedError(
            f"'{strategy}' selection is designed (docs/selection_notes.md) but "
            "not implemented in the pilot stage"
        )
    if strategy not in IMPLEMENTED_STRATEGIES:
        raise SelectionError(
            f"unknown strategy {strategy!r}; choose from {IMPLEMENTED_STRATEGIES}"
        )

    text_field = _CONFIG["text_field"]
    needs_text = strategy == "similarity"
    pool_ids = _validate_pool(pool, text_field if needs_text else None)
    _validate_k(k, len(pool_ids))
    _validate_seed(seed)
    query_key, query_text, query_id = _query_key_and_text(query, text_field, needs_text)

    if query_id is not None and query_id in set(pool_ids):
        raise SelectionError(
            f"query {query_id!r} is inside the demo pool - dev/test items must "
            "never be used as demonstrations"
        )

    if strategy == "random":
        result = select_random(
            pool_ids, k, seed, query_key=query_key, per_query=_CONFIG["per_query_seed"]
        )
    else:  # similarity
        enc = encoder if encoder is not None else get_default_encoder()
        cch = cache if cache is not None else get_cache(enc)
        result = select_similar(query_text, pool, k, enc, cch, text_field)

    _check_output(result, pool_ids, k, strategy)
    return result


def get_demos(demo_ids: Sequence[str], pool: Sequence[dict]) -> list[dict]:
    """Turn selected IDs back into full pool records, in the same order.

    Raises SelectionError for any ID that is not in the pool.
    """
    by_id = {rec["id"]: rec for rec in pool}
    unknown = [d for d in demo_ids if d not in by_id]
    if unknown:
        raise SelectionError(f"unknown demo ID(s): {unknown}")
    return [by_id[d] for d in demo_ids]


def describe_selector(strategy: str, encoder: Encoder | None = None) -> dict:
    """Metadata to store in each inference record / run log."""
    strategy = strategy.strip().lower()
    meta: dict[str, Any] = {
        "selection_strategy": strategy,
        "selection_text_field": _CONFIG["text_field"],
    }
    if strategy == "random":
        meta["per_query_seed"] = _CONFIG["per_query_seed"]
        meta["seed_derivation"] = "sha256('<seed>|id:<query_id>')[:16] -> random.Random"
    elif strategy == "similarity":
        enc = encoder if encoder is not None else get_default_encoder()
        meta.update(enc.info())
        meta["similarity"] = "cosine on L2-normalised vectors, rounded to 6 dp, ties by ID"
    return meta


def load_jsonl(path: str | Path) -> list[dict]:
    """Read a UTF-8 JSONL file into a list of dicts (blank lines skipped)."""
    records = []
    with open(path, encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise SelectionError(f"{path}:{line_no} is not valid JSON: {exc}") from exc
    return records
