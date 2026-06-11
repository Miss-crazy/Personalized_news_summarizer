"""
personalization/feedback_handler.py
Public entry point for all feedback signals.

This is the thin layer that the API (Phase 5) and the frontend call.
It validates inputs, routes to the correct weight_updater function,
and returns a clean response dict.

Supported signals
-----------------
  "thumbs_up"   — explicit positive rating
  "thumbs_down" — explicit negative rating
  "dwell"       — implicit: seconds spent reading (requires dwell_seconds kwarg)
"""

import logging
from personalization.weight_updater import (
    handle_thumbs_up,
    handle_thumbs_down,
    handle_dwell,
)

logger = logging.getLogger(__name__)

VALID_SIGNALS = {"thumbs_up", "thumbs_down", "dwell"}


def process_feedback(
    user_id: str,
    cluster_id: int,
    signal: str,
    dwell_seconds: float = 0.0,
) -> dict:
    """
    Process one feedback event and return an updated-weights summary.

    Args:
        user_id       : Unique identifier for the user (string, e.g. "user_42").
        cluster_id    : The SQLite cluster id the user interacted with.
        signal        : One of 'thumbs_up', 'thumbs_down', 'dwell'.
        dwell_seconds : Required (and used) only when signal == 'dwell'.

    Returns:
        {
          "status":     "ok",
          "user_id":    str,
          "cluster_id": int,
          "signal":     str,
          "weights_updated": int,   # number of non-zero weights now
        }

    Raises:
        ValueError: if signal is not recognised.
    """
    if signal not in VALID_SIGNALS:
        raise ValueError(
            f"Unknown signal '{signal}'. Must be one of: {VALID_SIGNALS}"
        )

    logger.info(
        "Feedback: user=%s cluster=%d signal=%s dwell=%.1fs",
        user_id, cluster_id, signal, dwell_seconds,
    )

    if signal == "thumbs_up":
        weights = handle_thumbs_up(user_id, cluster_id)
    elif signal == "thumbs_down":
        weights = handle_thumbs_down(user_id, cluster_id)
    else:  # dwell
        weights = handle_dwell(user_id, cluster_id, dwell_seconds)

    return {
        "status":          "ok",
        "user_id":         user_id,
        "cluster_id":      cluster_id,
        "signal":          signal,
        "weights_updated": len([v for v in weights.values() if v != 0.0]),
    }