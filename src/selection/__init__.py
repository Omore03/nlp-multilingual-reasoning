"""Demonstration selection for the Urdu/English math-reasoning ICL project.

Public API:
    select_examples(query, pool, k, strategy, seed) -> list[demo_id]
    get_demos(demo_ids, pool) -> list[record]
    describe_selector(strategy) -> dict       (metadata for run logs)
    configure(**settings)                     (encoder, revision, cache dir...)
"""

from .encoders import (
    DEFAULT_ENCODER_ID,
    HashedCharNgramEncoder,
    SentenceTransformerEncoder,
    normalize_urdu,
)
from .select import (
    DEFERRED_STRATEGIES,
    IMPLEMENTED_STRATEGIES,
    SelectionError,
    configure,
    describe_selector,
    get_config,
    get_demos,
    load_jsonl,
    select_examples,
)
from .similarity import EmbeddingCache, rank_pool

__all__ = [
    "DEFAULT_ENCODER_ID",
    "DEFERRED_STRATEGIES",
    "IMPLEMENTED_STRATEGIES",
    "EmbeddingCache",
    "HashedCharNgramEncoder",
    "SelectionError",
    "SentenceTransformerEncoder",
    "configure",
    "describe_selector",
    "get_config",
    "get_demos",
    "load_jsonl",
    "normalize_urdu",
    "rank_pool",
    "select_examples",
]
