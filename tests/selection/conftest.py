import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from selection import configure, load_jsonl  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def isolated_config(tmp_path):
    """Every test gets default settings and its own empty cache directory."""
    configure(
        encoder_id="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        encoder_revision=None,
        device=None,
        cache_dir=str(tmp_path / "emb_cache"),
        text_field="question_ur",
        per_query_seed=True,
    )
    yield


@pytest.fixture
def mock_pool():
    return load_jsonl(FIXTURES / "mock_demo_pool.jsonl")


@pytest.fixture
def mock_dev():
    return load_jsonl(FIXTURES / "mock_dev.jsonl")
