"""Pytest Fixtures."""

import sys
from pathlib import Path

import pytest


@pytest.fixture()
def driver_name() -> str:
    """Return name of the driver to be tested."""
    return "lima"


@pytest.fixture()
def limactl_stub(tmp_path: Path) -> Path:
    """Return a directory holding a limactl stub, to be prepended to PATH."""
    stub = Path(__file__).parent / "limactl_stub.py"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    limactl = bin_dir / "limactl"
    limactl.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{stub}" "$@"\n')
    limactl.chmod(0o755)
    return bin_dir
