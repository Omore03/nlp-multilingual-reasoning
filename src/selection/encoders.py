"""Text encoders used by the similarity selector.

An encoder turns a list of strings into a 2-D float array (one row per string).
Every encoder exposes:

* ``cache_key``  - a string that changes whenever the vectors could change
                   (model ID + exact revision). Used to name the cache file.
* ``encode(texts) -> np.ndarray`` of shape (len(texts), dim).
* ``info() -> dict`` - metadata to log with every inference run.

Two implementations:

SentenceTransformerEncoder
    The project encoder. Default model:
    sentence-transformers/paraphrase-multilingual-mpnet-base-v2
    (XLM-RoBERTa based, 768-dim, Urdu listed in its training languages,
    max input 128 tokens). The exact Hugging Face commit hash is resolved on
    first use and recorded in info(); pin it in the config afterwards.

HashedCharNgramEncoder
    OFFLINE STAND-IN FOR TESTS AND DRY RUNS ONLY. It hashes character n-grams
    into a fixed-size vector, so it measures shared spelling, not meaning.
    Never use it for pilot or final results.
"""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from pathlib import Path
from typing import Protocol, Sequence

import numpy as np

log = logging.getLogger(__name__)

DEFAULT_ENCODER_ID = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# Model repos often also hold ONNX / OpenVINO / TensorFlow / Flax copies of the
# weights. Only the PyTorch files are needed, so skip the rest (saves GBs).
DOWNLOAD_IGNORE_PATTERNS = [
    "onnx/*", "openvino/*", "*.onnx", "*.h5", "*.msgpack", "*.ot",
    "tf_model*", "flax_model*", "rust_model*",
]

# ---------------------------------------------------------------------------
# Urdu text normalisation (applied only to the text we embed; data files are
# never modified).
# ---------------------------------------------------------------------------

_CHAR_MAP = {
    "\u064a": "\u06cc",  # Arabic yeh  -> Farsi/Urdu yeh
    "\u0649": "\u06cc",  # alef maksura -> Urdu yeh
    "\u0643": "\u06a9",  # Arabic kaf  -> keheh (Urdu kaf)
    "\u0640": "",        # tatweel (decorative stretching) -> removed
}
# Urdu (U+06F0-06F9) and Arabic-Indic (U+0660-0669) digits -> ASCII digits
for _i in range(10):
    _CHAR_MAP[chr(0x06F0 + _i)] = str(_i)
    _CHAR_MAP[chr(0x0660 + _i)] = str(_i)
_TRANSLATE = str.maketrans(_CHAR_MAP)
_WS = re.compile(r"\s+")


def normalize_urdu(text: str) -> str:
    """Canonical form of a string before embedding.

    Unicode NFC, Arabic letter variants mapped to their Urdu forms, Urdu and
    Arabic-Indic digits mapped to ASCII, tatweel removed, whitespace collapsed.
    """
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_TRANSLATE)
    return _WS.sub(" ", text).strip()


class Encoder(Protocol):
    cache_key: str

    def encode(self, texts: Sequence[str]) -> np.ndarray: ...

    def info(self) -> dict: ...


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)


# ---------------------------------------------------------------------------
# Real encoder
# ---------------------------------------------------------------------------


class SentenceTransformerEncoder:
    """Multilingual sentence-transformers encoder with a pinned revision.

    Args:
        model_id: Hugging Face model ID.
        revision: commit hash to pin. If None, the latest revision is
            downloaded once, its commit hash is recorded in info(), and a
            warning reminds you to pin it.
        device: "cpu", "cuda", or None for automatic choice.
        batch_size: encoding batch size.
        local_files_only: never touch the network (requires a prior download).
    """

    def __init__(
        self,
        model_id: str = DEFAULT_ENCODER_ID,
        revision: str | None = None,
        device: str | None = None,
        batch_size: int = 32,
        local_files_only: bool = False,
    ) -> None:
        self.model_id = model_id
        self.requested_revision = revision
        self.device = device
        self.batch_size = batch_size
        self.local_files_only = local_files_only
        self._local_path: str | None = None
        self._revision: str | None = None
        self._model = None
        self.truncated_texts: list[str] = []

    # -- resolution and loading ------------------------------------------------
    def _resolve(self) -> None:
        """Download (or find in the local HF cache) the pinned snapshot."""
        if self._local_path is not None:
            return
        try:
            from huggingface_hub import snapshot_download
        except ImportError as exc:  # pragma: no cover - depends on install
            raise ImportError(
                "huggingface-hub is required for the real encoder: "
                "pip install -r requirements-selection.txt"
            ) from exc
        path = snapshot_download(
            self.model_id,
            revision=self.requested_revision,
            local_files_only=self.local_files_only,
            ignore_patterns=DOWNLOAD_IGNORE_PATTERNS,
        )
        self._local_path = str(path)
        # The HF cache layout is .../snapshots/<commit_hash>
        self._revision = Path(self._local_path).name
        if self.requested_revision is None:
            log.warning(
                "Encoder revision not pinned. Resolved %s to commit %s - "
                "put this hash in the config as encoder_revision.",
                self.model_id,
                self._revision,
            )

    def _load(self):
        if self._model is None:
            self._resolve()
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover
                raise ImportError(
                    "sentence-transformers is required for the real encoder: "
                    "pip install -r requirements-selection.txt"
                ) from exc
            self._model = SentenceTransformer(self._local_path, device=self.device)
        return self._model

    # -- Encoder interface -----------------------------------------------------
    @property
    def cache_key(self) -> str:
        self._resolve()
        return _slug(f"{self.model_id}@{self._revision}")

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        model = self._load()
        texts = list(texts)
        self._check_truncation(model, texts)
        vectors = model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)

    def _check_truncation(self, model, texts: list[str]) -> None:
        """Record texts longer than the model's input limit (they get cut)."""
        limit = getattr(model, "max_seq_length", None)
        tokenizer = getattr(model, "tokenizer", None)
        if not limit or tokenizer is None:
            return
        for text in texts:
            n_tokens = len(tokenizer(text)["input_ids"])
            if n_tokens > limit:
                self.truncated_texts.append(text)
                log.warning(
                    "Text has %d tokens, above the encoder limit of %d; the "
                    "end will be ignored: %.60s...",
                    n_tokens,
                    limit,
                    text,
                )

    def info(self) -> dict:
        model = self._load()
        try:
            import sentence_transformers

            st_version = sentence_transformers.__version__
        except Exception:  # pragma: no cover
            st_version = "unknown"
        return {
            "encoder_id": self.model_id,
            "encoder_revision": self._revision,
            "library": "sentence-transformers",
            "library_version": st_version,
            "max_seq_length": getattr(model, "max_seq_length", None),
            "embedding_dim": model.get_sentence_embedding_dimension(),
            "normalize_embeddings": True,
            "text_normalization": "normalize_urdu (NFC, Arabic->Urdu letters, digits->ASCII)",
            "n_truncated_texts": len(self.truncated_texts),
        }


# ---------------------------------------------------------------------------
# Offline stand-in (tests / dry runs only)
# ---------------------------------------------------------------------------


class HashedCharNgramEncoder:
    """Deterministic character n-gram hashing encoder. NOT a semantic model.

    Exists so the pipeline can be exercised without downloading anything.
    Similarity under this encoder means "shares spelling", nothing more.
    """

    def __init__(self, dim: int = 2048, ngram_sizes: tuple[int, ...] = (2, 3, 4)):
        self.dim = dim
        self.ngram_sizes = ngram_sizes

    @property
    def cache_key(self) -> str:
        sizes = "-".join(map(str, self.ngram_sizes))
        return f"offline-hashed-char-ngram_v1_dim{self.dim}_n{sizes}"

    def _bucket(self, gram: str) -> int:
        return int(hashlib.md5(gram.encode("utf-8")).hexdigest()[:8], 16) % self.dim

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            padded = f" {normalize_urdu(text)} "
            for n in self.ngram_sizes:
                for i in range(len(padded) - n + 1):
                    out[row, self._bucket(padded[i : i + n])] += 1.0
            out[row] = np.log1p(out[row])
            norm = np.linalg.norm(out[row])
            if norm > 0:
                out[row] /= norm
        return out

    def info(self) -> dict:
        return {
            "encoder_id": "offline-hashed-char-ngram",
            "encoder_revision": self.cache_key,
            "library": "numpy",
            "warning": "test/dry-run encoder only; not semantic",
        }
