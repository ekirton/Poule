"""Platform-specific data directory helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def get_data_dir() -> Path:
    """Return the data directory for poule.

    Resolution order:
    1. ``POULE_DATA_DIR`` environment variable (set by Dockerfile,
       ``bin/poule``, and ``bin/poule-dev``).
    2. ``~/poule-home/data`` (default for host-side development).
    """
    env = os.environ.get("POULE_DATA_DIR")
    if env:
        return Path(env)
    return Path.home() / "poule-home" / "data"


def get_model_dir() -> Path:
    """Return the directory for model checkpoints."""
    return get_data_dir() / "models"
