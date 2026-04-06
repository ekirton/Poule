"""Tests for poule.paths — data directory helpers.

Spec: specification/prebuilt-distribution.md §4.1

Import paths under test:
  poule.paths.get_data_dir
  poule.paths.get_model_dir
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from Poule.paths import get_data_dir, get_model_dir


# ===========================================================================
# get_data_dir
# ===========================================================================


class TestGetDataDir:
    """get_data_dir respects POULE_DATA_DIR, falls back to ~/poule-home/data."""

    def test_env_var_overrides_default(self):
        with patch.dict("os.environ", {"POULE_DATA_DIR": "/custom/data"}):
            result = get_data_dir()
        assert result == Path("/custom/data")

    def test_default_is_poule_home_data(self):
        with patch.dict("os.environ", {}, clear=True):
            result = get_data_dir()
        assert result == Path.home() / "poule-home" / "data"

    def test_returns_path_object(self):
        result = get_data_dir()
        assert isinstance(result, Path)

    def test_does_not_create_directory(self, tmp_path):
        """get_data_dir must NOT create directories — that's the caller's job."""
        with patch.dict("os.environ", {"POULE_DATA_DIR": str(tmp_path / "nonexistent")}):
            result = get_data_dir()
        assert not result.exists()


# ===========================================================================
# get_model_dir
# ===========================================================================


class TestGetModelDir:
    """get_model_dir returns get_data_dir() / 'models'."""

    def test_is_subdirectory_of_data_dir(self):
        result = get_model_dir()
        assert result == get_data_dir() / "models"

    def test_respects_env_var(self):
        with patch.dict("os.environ", {"POULE_DATA_DIR": "/custom/data"}):
            result = get_model_dir()
        assert result == Path("/custom/data") / "models"

    def test_returns_path_object(self):
        result = get_model_dir()
        assert isinstance(result, Path)

    def test_does_not_create_directory(self, tmp_path):
        """get_model_dir must NOT create directories — that's the caller's job."""
        with patch.dict("os.environ", {"POULE_DATA_DIR": str(tmp_path / "nonexistent")}):
            result = get_model_dir()
        assert not result.exists()
