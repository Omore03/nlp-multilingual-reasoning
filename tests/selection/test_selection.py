"""Tests for src/selection.

Run from the repository root:  pytest tests/test_selection.py -v

None of these tests downloads a model. Similarity logic is tested with a fake
encoder that returns hand-chosen vectors (so the correct ranking can be worked
out on paper) and with the offline hashed n-gram encoder.
"""

from __future__ import annotations

import random as stdlib_random
from collections import Counter

import numpy as np
import pytest

from selection import (
    EmbeddingCache,
    HashedCharNgramEncoder,
    SelectionError,
    configure,
    describe_selector,
    get_demos,
    normalize_urdu,
    rank_pool,
    select_examples,
)
from selection.random import derive_seed, select_random


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeEncoder:
    """Returns fixed vectors for known texts and counts how many it encodes."""

    cache_key = "fake-encoder-v1"

    def __init__(self, table: dict[str, list[float]]):
        self.table = {normalize_urdu(k): np.array(v, dtype=np.float32) for k, v in table.items()}
        self.calls = 0
        self.texts_encoded = 0

    def encode(self, texts):
        self.calls += 1
        self.texts_encoded += len(texts)
        return np.stack([self.table[normalize_urdu(t)] for t in texts])

    def info(self):
        return {"encoder_id": "fake", "encoder_revision": "v1"}


def rec(rid, text):
    return {"id": rid, "question_ur": text}


# Hand-checked geometry (query q1 = [1,0,0], q2 = [0,1,0]):
#   id        vector         cos(q1)  cos(q2)
#   demo_05   [2, 0, 0]       1.0      0.0     (not unit length on purpose)
#   demo_02   [0.8, 0.6, 0]   0.8      0.6
#   demo_04   [0, 1, 0]       0.0      1.0
#   demo_01   [0.6, 0, 0.8]   0.6      0.0
#   demo_03   [-1, 0, 0]     -1.0      0.0
# q1 ranking: demo_05, demo_02, demo_01, demo_04, demo_03
# q2 ranking: demo_04, demo_02, then a three-way tie at 0.0 broken by ID:
#             demo_01, demo_03, demo_05
GEOMETRY = {
    "t05": [2.0, 0.0, 0.0],
    "t02": [0.8, 0.6, 0.0],
    "t04": [0.0, 1.0, 0.0],
    "t01": [0.6, 0.0, 0.8],
    "t03": [-1.0, 0.0, 0.0],
    "q1": [1.0, 0.0, 0.0],
    "q2": [0.0, 1.0, 0.0],
}
GEO_POOL = [rec("demo_05", "t05"), rec("demo_02", "t02"), rec("demo_04", "t04"),
            rec("demo_01", "t01"), rec("demo_03", "t03")]


def ids20():
    return [f"demo_{i:02d}" for i in range(1, 21)]


# ---------------------------------------------------------------------------
# Random selector
# ---------------------------------------------------------------------------


def test_random_returns_k_unique_valid_ids(mock_pool, mock_dev):
    pool_ids = {r["id"] for r in mock_pool}
    for q in mock_dev:
        out = select_examples(q, mock_pool, 2, "random", seed=42)
        assert len(out) == 2 and len(set(out)) == 2
        assert set(out) <= pool_ids


def test_random_same_seed_same_result(mock_pool, mock_dev):
    for q in mock_dev:
        a = select_examples(q, mock_pool, 2, "random", seed=42)
        b = select_examples(q, mock_pool, 2, "random", seed=42)
        assert a == b


def test_random_independent_of_pool_file_order(mock_pool, mock_dev):
    shuffled = list(mock_pool)
    stdlib_random.Random(0).shuffle(shuffled)
    for q in mock_dev:
        assert select_examples(q, mock_pool, 2, "random", 7) == select_examples(q, shuffled, 2, "random", 7)


def test_random_seed_changes_result():
    ids = ids20()
    results = {tuple(select_random(ids, 2, seed, query_key="id:dev_01")) for seed in range(20)}
    assert len(results) > 1


def test_random_differs_across_queries_by_default():
    ids = ids20()
    pairs = {tuple(select_random(ids, 2, 42, query_key=f"id:dev_{i:02d}")) for i in range(10)}
    assert len(pairs) > 1


def test_random_per_query_off_gives_same_pair_for_all_queries():
    ids = ids20()
    pairs = {tuple(select_random(ids, 2, 42, query_key=f"id:dev_{i:02d}", per_query=False)) for i in range(10)}
    assert len(pairs) == 1


def test_random_is_roughly_uniform():
    ids = ids20()
    counts = Counter()
    for i in range(2000):
        counts.update(select_random(ids, 2, 123, query_key=f"id:q{i}"))
    # 4000 picks over 20 IDs -> 200 expected each
    assert set(counts) == set(ids)
    assert all(140 <= c <= 260 for c in counts.values()), counts


def test_derive_seed_is_stable():
    # Fixed value guards against accidental changes to the derivation.
    assert derive_seed(42, "id:dev_01") == derive_seed(42, "id:dev_01")
    assert derive_seed(42, "id:dev_01") != derive_seed(43, "id:dev_01")
    assert derive_seed(42, "id:dev_01") != derive_seed(42, "id:dev_02")


def test_random_accepts_plain_string_query(mock_pool):
    text = "ایک کاپی کی قیمت 35 روپے ہے۔"
    assert select_examples(text, mock_pool, 2, "random", 1) == select_examples(text, mock_pool, 2, "random", 1)


def test_random_works_with_k_equal_pool_size(mock_pool):
    out = select_examples({"id": "q"}, mock_pool, len(mock_pool), "random", 0)
    assert sorted(out) == sorted(r["id"] for r in mock_pool)


# ---------------------------------------------------------------------------
# Similarity selector - hand-checked ranking
# ---------------------------------------------------------------------------


def test_similarity_matches_hand_checked_ranking():
    enc = FakeEncoder(GEOMETRY)
    cache = EmbeddingCache(None, enc.cache_key)
    ranked = rank_pool("q1", GEO_POOL, enc, cache)
    assert [rid for rid, _ in ranked] == ["demo_05", "demo_02", "demo_01", "demo_04", "demo_03"]
    assert [s for _, s in ranked] == pytest.approx([1.0, 0.8, 0.6, 0.0, -1.0])


def test_similarity_top_k_via_public_interface():
    enc = FakeEncoder(GEOMETRY)
    q = {"id": "dev_x", "question_ur": "q1"}
    assert select_examples(q, GEO_POOL, 2, "similarity", 0, encoder=enc) == ["demo_05", "demo_02"]
    assert select_examples(q, GEO_POOL, 3, "similarity", 0, encoder=enc) == ["demo_05", "demo_02", "demo_01"]


def test_similarity_ties_broken_by_id():
    enc = FakeEncoder(GEOMETRY)
    cache = EmbeddingCache(None, enc.cache_key)
    ranked = rank_pool("q2", GEO_POOL, enc, cache)
    assert [rid for rid, _ in ranked] == ["demo_04", "demo_02", "demo_01", "demo_03", "demo_05"]


def test_similarity_near_ties_are_treated_as_ties():
    # Scores that differ by less than 1e-6 must be ordered by ID, not by noise.
    enc = FakeEncoder({"a": [1.0, 1e-9, 0.0], "b": [1.0, 0.0, 0.0], "q": [1.0, 0.0, 0.0]})
    cache = EmbeddingCache(None, enc.cache_key)
    pool = [rec("demo_b", "a"), rec("demo_a", "b")]
    assert [rid for rid, _ in rank_pool("q", pool, enc, cache)] == ["demo_a", "demo_b"]


def test_similarity_independent_of_pool_order():
    enc = FakeEncoder(GEOMETRY)
    q = {"id": "dev_x", "question_ur": "q2"}
    reversed_pool = list(reversed(GEO_POOL))
    assert (select_examples(q, GEO_POOL, 3, "similarity", 0, encoder=enc)
            == select_examples(q, reversed_pool, 3, "similarity", 0, encoder=enc))


def test_similarity_ignores_seed():
    enc = FakeEncoder(GEOMETRY)
    q = {"id": "dev_x", "question_ur": "q1"}
    assert (select_examples(q, GEO_POOL, 2, "similarity", 1, encoder=enc)
            == select_examples(q, GEO_POOL, 2, "similarity", 999, encoder=enc))


def test_similarity_with_offline_encoder_on_fixture(mock_pool, mock_dev):
    enc = HashedCharNgramEncoder()
    pool_ids = {r["id"] for r in mock_pool}
    for q in mock_dev:
        out = select_examples(q, mock_pool, 2, "similarity", 42, encoder=enc)
        assert len(out) == 2 and len(set(out)) == 2 and set(out) <= pool_ids
        assert out == select_examples(q, mock_pool, 2, "similarity", 42, encoder=enc)


# ---------------------------------------------------------------------------
# Embedding cache
# ---------------------------------------------------------------------------


def test_cache_avoids_re_encoding_and_persists(tmp_path):
    enc = FakeEncoder(GEOMETRY)
    cache = EmbeddingCache(tmp_path, enc.cache_key)
    rank_pool("q1", GEO_POOL, enc, cache)
    assert enc.texts_encoded == 6  # 5 pool + 1 query
    rank_pool("q1", GEO_POOL, enc, cache)
    assert enc.texts_encoded == 6  # nothing new
    # A fresh cache object reads the file from disk.
    enc2 = FakeEncoder(GEOMETRY)
    cache2 = EmbeddingCache(tmp_path, enc2.cache_key)
    assert len(cache2) == 6
    rank_pool("q2", GEO_POOL, enc2, cache2)
    assert enc2.texts_encoded == 1  # only the new query


def test_cache_re_encodes_edited_text(tmp_path):
    table = dict(GEOMETRY, t05_edited=[2.0, 0.0, 0.0])
    enc = FakeEncoder(table)
    cache = EmbeddingCache(tmp_path, enc.cache_key)
    rank_pool("q1", GEO_POOL, enc, cache)
    edited = [rec("demo_05", "t05_edited")] + GEO_POOL[1:]
    before = enc.texts_encoded
    rank_pool("q1", edited, enc, cache)
    assert enc.texts_encoded == before + 1


def test_cache_files_are_separate_per_encoder(tmp_path):
    a = EmbeddingCache(tmp_path, "encoder_a@rev1")
    b = EmbeddingCache(tmp_path, "encoder_a@rev2")
    assert a.path != b.path


# ---------------------------------------------------------------------------
# Urdu normalisation
# ---------------------------------------------------------------------------


def test_normalize_urdu_maps_arabic_variants_and_digits():
    arabic_forms = "\u0643\u062a\u0627\u0628 \u064a  \u06f1\u06f2"  # Arabic kaf, Arabic yeh, Urdu digits 12
    assert normalize_urdu(arabic_forms) == "\u06a9\u062a\u0627\u0628 \u06cc 12"


def test_normalize_urdu_collapses_whitespace_and_tatweel():
    assert normalize_urdu("  \u0628\u0640\u0640\u0627\u062a\n\n ") == "\u0628\u0627\u062a"


# ---------------------------------------------------------------------------
# Input validation and error handling
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_k", [0, -1, 2.0, "2", True, None])
def test_invalid_k_rejected(mock_pool, bad_k):
    with pytest.raises(SelectionError):
        select_examples({"id": "q"}, mock_pool, bad_k, "random", 0)


def test_k_larger_than_pool_rejected(mock_pool):
    with pytest.raises(SelectionError, match="larger than the pool"):
        select_examples({"id": "q"}, mock_pool, len(mock_pool) + 1, "random", 0)


def test_empty_pool_rejected():
    with pytest.raises(SelectionError, match="empty"):
        select_examples({"id": "q"}, [], 2, "random", 0)


def test_duplicate_pool_ids_rejected(mock_pool):
    with pytest.raises(SelectionError, match="duplicate"):
        select_examples({"id": "q"}, mock_pool + [mock_pool[0]], 2, "random", 0)


def test_pool_record_without_id_rejected(mock_pool):
    with pytest.raises(SelectionError, match="'id'"):
        select_examples({"id": "q"}, mock_pool + [{"question_ur": "x"}], 2, "random", 0)


def test_similarity_requires_urdu_text_in_pool():
    enc = FakeEncoder(GEOMETRY)
    pool = GEO_POOL + [{"id": "demo_99", "question_ur": "  "}]
    with pytest.raises(SelectionError, match="question_ur"):
        select_examples({"id": "q", "question_ur": "q1"}, pool, 2, "similarity", 0, encoder=enc)


def test_similarity_requires_urdu_text_in_query():
    enc = FakeEncoder(GEOMETRY)
    with pytest.raises(SelectionError, match="question_ur"):
        select_examples({"id": "q"}, GEO_POOL, 2, "similarity", 0, encoder=enc)


def test_unknown_strategy_rejected(mock_pool):
    with pytest.raises(SelectionError, match="unknown strategy"):
        select_examples({"id": "q"}, mock_pool, 2, "nearest", 0)


@pytest.mark.parametrize("strategy", ["diversity", "complexity"])
def test_deferred_strategies_raise_not_implemented(mock_pool, strategy):
    with pytest.raises(NotImplementedError):
        select_examples({"id": "q"}, mock_pool, 2, strategy, 0)


def test_strategy_name_is_case_insensitive(mock_pool):
    assert (select_examples({"id": "q"}, mock_pool, 2, " Random ", 3)
            == select_examples({"id": "q"}, mock_pool, 2, "random", 3))


@pytest.mark.parametrize("bad_seed", [None, 1.5, "42", True])
def test_invalid_seed_rejected(mock_pool, bad_seed):
    with pytest.raises(SelectionError, match="seed"):
        select_examples({"id": "q"}, mock_pool, 2, "random", bad_seed)


def test_query_inside_pool_is_leakage(mock_pool):
    with pytest.raises(SelectionError, match="inside the demo pool"):
        select_examples(mock_pool[0], mock_pool, 2, "random", 0)


@pytest.mark.parametrize("bad_query", [None, 5, "", "   ", {"question_ur": "x"}, {"id": ""}])
def test_invalid_query_rejected(mock_pool, bad_query):
    with pytest.raises(SelectionError):
        select_examples(bad_query, mock_pool, 2, "random", 0)


def test_get_demos_returns_records_in_order(mock_pool):
    out = get_demos(["mock_demo_03", "mock_demo_01"], mock_pool)
    assert [r["id"] for r in out] == ["mock_demo_03", "mock_demo_01"]


def test_get_demos_rejects_unknown_id(mock_pool):
    with pytest.raises(SelectionError, match="unknown demo ID"):
        get_demos(["mock_demo_01", "demo_does_not_exist"], mock_pool)


def test_configure_rejects_unknown_setting():
    with pytest.raises(SelectionError):
        configure(encoder_name="x")


def test_describe_selector_metadata():
    rand = describe_selector("random")
    assert rand["selection_strategy"] == "random" and rand["per_query_seed"] is True
    sim = describe_selector("similarity", encoder=FakeEncoder(GEOMETRY))
    assert sim["encoder_id"] == "fake" and "cosine" in sim["similarity"]


# ---------------------------------------------------------------------------
# Acceptance test from the work plan
# ---------------------------------------------------------------------------


def test_acceptance_every_dev_query_gets_two_valid_unique_ids(mock_pool, mock_dev):
    """For every dev query each selector returns exactly 2 valid, unique IDs."""
    enc = HashedCharNgramEncoder()
    pool_ids = {r["id"] for r in mock_pool}
    dev_ids = {q["id"] for q in mock_dev}
    assert pool_ids.isdisjoint(dev_ids)
    for strategy in ("random", "similarity"):
        for q in mock_dev:
            out = select_examples(q, mock_pool, 2, strategy, 42, encoder=enc)
            assert len(out) == 2, (strategy, q["id"], out)
            assert len(set(out)) == 2, (strategy, q["id"], out)
            assert set(out) <= pool_ids, (strategy, q["id"], out)


# ---------------------------------------------------------------------------
# Real-encoder wrapper, exercised with stand-in libraries (no download)
# ---------------------------------------------------------------------------


def test_sentence_transformer_encoder_wrapper(monkeypatch, tmp_path):
    import sys
    import types

    from selection import SentenceTransformerEncoder

    snapshot = tmp_path / "models--x" / "snapshots" / "abc123def"
    snapshot.mkdir(parents=True)
    calls = {}

    def fake_snapshot_download(repo_id, *, revision=None, local_files_only=False, ignore_patterns=None):
        calls["snapshot"] = (repo_id, revision, local_files_only)
        calls["ignore"] = ignore_patterns
        return str(snapshot)

    class FakeST:
        max_seq_length = 4

        def __init__(self, path, *, device=None):
            calls["loaded_from"] = path
            self.tokenizer = lambda text: {"input_ids": text.split()}

        def encode(self, texts, *, batch_size, convert_to_numpy, normalize_embeddings, show_progress_bar):
            calls["normalize"] = normalize_embeddings
            return np.ones((len(texts), 3), dtype=np.float32) / np.sqrt(3)

        def get_sentence_embedding_dimension(self):
            return 3

    monkeypatch.setitem(sys.modules, "huggingface_hub",
                        types.SimpleNamespace(snapshot_download=fake_snapshot_download))
    monkeypatch.setitem(sys.modules, "sentence_transformers",
                        types.SimpleNamespace(SentenceTransformer=FakeST, __version__="6.2.0"))

    enc = SentenceTransformerEncoder("org/model", revision=None)
    assert enc.cache_key == "org_model_abc123def"
    vecs = enc.encode(["one two", "one two three four five six"])
    assert vecs.shape == (2, 3)
    assert calls["loaded_from"] == str(snapshot)
    assert calls["normalize"] is True
    assert "onnx/*" in calls["ignore"]
    assert len(enc.truncated_texts) == 1  # second text has 6 > 4 tokens
    info = enc.info()
    assert info["encoder_revision"] == "abc123def"
    assert info["library_version"] == "6.2.0"
    assert info["n_truncated_texts"] == 1
