"""Random demonstration selection.

Uniform sampling without replacement from the demo pool, fully reproducible.

Reproducibility rules
---------------------
* Pool IDs are sorted before sampling, so the result never depends on the
  order of lines in demo_pool.jsonl.
* By default each query gets its own derived seed: sha256("<seed>|<query key>").
  This means different dev questions get different random pairs, but the same
  (seed, question) always gets the same pair. Python's built-in hash() is NOT
  used because it is randomised between interpreter runs.
* Set per_query=False to use the base seed directly (every query would then get
  the same pair) - this exists only for experiments that need it.

Note: this module is named random.py as required by the work plan. Inside the
package, ``import random`` still resolves to the standard library because the
package directory itself is never placed on sys.path. Do not run this file
directly as a script.
"""

from __future__ import annotations

import hashlib
import random as _stdlib_random
from typing import Iterable


def derive_seed(seed: int, query_key: str) -> int:
    """Return a stable 64-bit seed for one (base seed, query) pair."""
    digest = hashlib.sha256(f"{seed}|{query_key}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def select_random(
    pool_ids: Iterable[str],
    k: int,
    seed: int,
    query_key: str | None = None,
    per_query: bool = True,
) -> list[str]:
    """Pick k distinct pool IDs uniformly at random.

    Args:
        pool_ids: IDs of all candidate demonstrations (already validated).
        k: number of demonstrations to return.
        seed: base random seed from the experiment config.
        query_key: stable identifier of the query (its ID, or a hash of its
            text). Required when per_query is True.
        per_query: derive a separate seed for each query (default True).

    Returns:
        A list of k unique IDs, in the order they were drawn.
    """
    ids = sorted(pool_ids)
    if per_query:
        if not query_key:
            raise ValueError("per_query=True requires a non-empty query_key")
        effective_seed = derive_seed(seed, query_key)
    else:
        effective_seed = seed
    rng = _stdlib_random.Random(effective_seed)
    return rng.sample(ids, k)
