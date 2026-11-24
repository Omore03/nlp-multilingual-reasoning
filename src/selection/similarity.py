"""Semantic-similarity demonstration selection.

For a query, embed its Urdu question and every pool question (field
``question_ur``), score each pool item by cosine similarity, and return the
top-k IDs.

Determinism
-----------
* Vectors are L2-normalised, so cosine similarity = dot product.
* Scores are rounded to 6 decimals before ranking; this removes tiny
  floating-point differences between machines (CPU vs GPU) that could
  otherwise flip the order of near-equal items.
* Ties are broken by demo ID (ascending).

Caching
-------
Embeddings are stored on disk, one .npz file per encoder+revision, keyed by
the SHA-256 of the normalised text. Consequences:
* nothing is ever encoded twice;
* if a translation is edited, its hash changes and it is re-encoded
  automatically (a stale vector can never be used);
* changing the encoder or its revision uses a different file.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Sequence

import numpy as np

from .encoders import Encoder, normalize_urdu

SCORE_DECIMALS = 6


def text_key(text: str) -> str:
    """SHA-256 of the normalised text; the cache key for one string."""
    return hashlib.sha256(normalize_urdu(text).encode("utf-8")).hexdigest()


class EmbeddingCache:
    """Text-hash -> vector store, optionally persisted to an .npz file.

    Args:
        cache_dir: directory for the .npz file, or None for memory only.
        encoder_key: the encoder's cache_key (names the file).
    """

    def __init__(self, cache_dir: str | Path | None, encoder_key: str) -> None:
        self.encoder_key = encoder_key
        self.path = Path(cache_dir) / f"{encoder_key}.npz" if cache_dir else None
        self._store: dict[str, np.ndarray] = {}
        self.n_encoded = 0  # how many texts this object sent to the encoder
        if self.path is not None and self.path.exists():
            with np.load(self.path, allow_pickle=False) as data:
                for key, vec in zip(data["keys"], data["vectors"]):
                    self._store[str(key)] = vec

    def __len__(self) -> int:
        return len(self._store)

    def get_many(self, texts: Sequence[str], encoder: Encoder) -> np.ndarray:
        """Return vectors for texts, encoding (in one batch) only the misses."""
        keys = [text_key(t) for t in texts]
        missing: dict[str, str] = {}
        for key, text in zip(keys, texts):
            if key not in self._store and key not in missing:
                missing[key] = normalize_urdu(text)
        if missing:
            new_vectors = encoder.encode(list(missing.values()))
            if new_vectors.shape[0] != len(missing):
                raise RuntimeError("Encoder returned the wrong number of vectors")
            for key, vec in zip(missing.keys(), new_vectors):
                self._store[key] = np.asarray(vec, dtype=np.float32)
            self.n_encoded += len(missing)
            self._save()
        dims = {self._store[k].shape for k in keys}
        if len(dims) != 1:
            raise RuntimeError(
                f"Cache {self.path} holds vectors of different sizes {dims}; "
                "delete it and re-run."
            )
        return np.stack([self._store[k] for k in keys])

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        keys = np.array(list(self._store.keys()))
        vectors = np.stack(list(self._store.values())).astype(np.float32)
        # Write to a temp file then rename, so a crash never leaves a broken cache.
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".npz")
        os.close(fd)
        try:
            np.savez(tmp, keys=keys, vectors=vectors)
            os.replace(tmp, self.path)
            os.chmod(self.path, 0o644)  # mkstemp creates owner-only files
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.float64)
    norms = np.linalg.norm(matrix, axis=-1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("Encoder produced an all-zero vector (empty text?)")
    return matrix / norms


def rank_pool(
    query_text: str,
    pool: Sequence[dict],
    encoder: Encoder,
    cache: EmbeddingCache,
    text_field: str = "question_ur",
) -> list[tuple[str, float]]:
    """Score every pool item against the query; best first.

    Returns a list of (demo_id, cosine_score) for the whole pool, sorted by
    score descending, ties broken by ID ascending.
    """
    pool_ids = [rec["id"] for rec in pool]
    pool_vecs = _l2_normalize(cache.get_many([rec[text_field] for rec in pool], encoder))
    query_vec = _l2_normalize(cache.get_many([query_text], encoder))[0]
    scores = np.round(pool_vecs @ query_vec, SCORE_DECIMALS)
    ranked = sorted(zip(pool_ids, scores.tolist()), key=lambda pair: (-pair[1], pair[0]))
    return ranked


def select_similar(
    query_text: str,
    pool: Sequence[dict],
    k: int,
    encoder: Encoder,
    cache: EmbeddingCache,
    text_field: str = "question_ur",
) -> list[str]:
    """Return the IDs of the k pool items most similar to the query."""
    ranked = rank_pool(query_text, pool, encoder, cache, text_field)
    return [demo_id for demo_id, _ in ranked[:k]]
