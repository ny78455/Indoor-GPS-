"""Baseline and deterministic-seed support for reproduction experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

import hashlib
import json
import platform
import random
import subprocess
import sys

import numpy as np


@dataclass(frozen=True)
class RandomSeedManager:
    """Derives isolated reproducible random streams from one master seed."""

    master_seed: int

    def seed_for(self, stream: str) -> int:
        digest = hashlib.sha256(f"{self.master_seed}:{stream}".encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big") % (2**32)

    def generator(self, stream: str) -> np.random.Generator:
        return np.random.default_rng(self.seed_for(stream))

    def apply_legacy_seeds(self) -> None:
        """Seed legacy module calls; new code should use named generators instead."""
        random.seed(self.seed_for("python"))
        np.random.seed(self.seed_for("numpy"))

    def policy(self) -> Dict[str, int]:
        return {name: self.seed_for(name) for name in ("bits", "noise", "mobility", "geometry", "numpy")}


def _git_commit(repository_root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository_root, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def _dependency_versions() -> Dict[str, str]:
    versions: Dict[str, str] = {}
    try:
        from importlib.metadata import distributions
        versions = {item.metadata["Name"]: item.version for item in distributions() if item.metadata.get("Name")}
    except Exception:
        versions["status"] = "UNAVAILABLE"
    return dict(sorted(versions.items()))


def build_reproducibility_manifest(
    repository_root: str | Path,
    config_hash: str,
    seed_manager: RandomSeedManager,
    experiments: Iterable[str] = (),
    output_hashes: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    root = Path(repository_root).resolve()
    return {
        "paper_identifier": "Yang et al., An Advanced Integrated Visible Light Communication and Localization System, IEEE Trans. Commun. 71(12), 2023",
        "repository_commit": _git_commit(root),
        "config_hash": config_hash,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "node": "not queried by Python runner",
            "dependencies": _dependency_versions(),
        },
        "seed_policy": seed_manager.policy(),
        "experiments": list(experiments),
        "output_hashes": output_hashes or {},
    }


def write_json(path: str | Path, value: Dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
