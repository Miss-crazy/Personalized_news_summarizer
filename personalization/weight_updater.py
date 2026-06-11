"""
personalization/weight_updater.py
Updates user cluster-weight vectors from feedback signals.

Weight update rule (simplified collaborative-filtering style)
-------------------------------------------------------------
  new_weight = clamp(old_weight + delta * LEARNING_RATE, MIN_WEIGHT, MAX_WEIGHT)
  Then re-normalise so weights sum to 1.0 (probability distribution).

Signals and their deltas
  thumbs_up   → +1.0
  thumbs_down → -1.0
  dwell       → +dwell_seconds / DWELL_NORMALISER  (e.g. 60 s → +0.5)

Cold-start
  New users have all-zero weights. The first few interactions rapidly
  push the distribution away from uniform. The retriever falls back
  to pure similarity for users with no weights yet.
"""

import logging
from config.settings import (
    WEIGHT_LEARNING_RATE,
    WEIGHT_MIN,
    WEIGHT_MAX,
    DWELL_NORMALISER,
)
from storage.user_profiles import (
    get_or_create_profile,
    save_weights,
    log_feedback,
)

logger = logging.getLogger(__name__)


# ── Core update ───────────────────────────────────────────────────────────────

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _normalise(weights: dict) -> dict:
    """
    Re-normalise weights so they sum to 1.0.
    If all weights are zero (new user), returns the dict unchanged
    (the retriever handles the zero-weight case gracefully).
    """
    total = sum(abs(v) for v in weights.values())
    if total == 0:
        return weights
    return {k: v / total for k, v in weights.items()}


def update_weight(user_id: str, cluster_id: int, delta: float) -> dict:
    """
    Apply a raw delta to one cluster weight, clamp, normalise, save.

    Args:
        user_id    : Unique user identifier.
        cluster_id : SQLite cluster id being rated.
        delta      : Signed change to apply before learning rate scaling.

    Returns:
        Updated weights dict {cluster_id: float}.
    """
    profile = get_or_create_profile(user_id)
    weights = profile["weights"]  # {int cluster_id: float}

    old = weights.get(cluster_id, 0.0)
    updated = _clamp(old + delta * WEIGHT_LEARNING_RATE, WEIGHT_MIN, WEIGHT_MAX)
    weights[cluster_id] = updated

    weights = _normalise(weights)
    save_weights(user_id, weights)

    logger.debug(
        "User '%s' cluster %d: %.3f → %.3f (delta=%.3f)",
        user_id, cluster_id, old, updated, delta,
    )
    return weights


# ── Signal handlers ───────────────────────────────────────────────────────────

def handle_thumbs_up(user_id: str, cluster_id: int) -> dict:
    """User explicitly liked a cluster/article."""
    log_feedback(user_id, cluster_id, "thumbs_up", 1.0)
    return update_weight(user_id, cluster_id, delta=1.0)


def handle_thumbs_down(user_id: str, cluster_id: int) -> dict:
    """User explicitly disliked a cluster/article."""
    log_feedback(user_id, cluster_id, "thumbs_down", -1.0)
    return update_weight(user_id, cluster_id, delta=-1.0)


def handle_dwell(user_id: str, cluster_id: int, dwell_seconds: float) -> dict:
    """
    User spent time reading — implicit positive signal.
    Dwell is normalised: DWELL_NORMALISER seconds = delta of +1.0.
    Short reads (< 5s) are ignored to filter accidental hover.
    """
    if dwell_seconds < 5.0:
        logger.debug("Dwell too short (%.1fs) — ignoring.", dwell_seconds)
        return get_or_create_profile(user_id)["weights"]

    delta = dwell_seconds / DWELL_NORMALISER
    log_feedback(user_id, cluster_id, "dwell", dwell_seconds)
    return update_weight(user_id, cluster_id, delta=delta)