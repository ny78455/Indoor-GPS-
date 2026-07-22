"""Scientific paper-reproduction utilities for the VLCL digital twin.

This package is deliberately observational: it validates Modules 1--8 and
does not alter their algorithms or calibration parameters.
"""

from .config import PaperConfigValidator, ReproductionMode, load_paper_config
from .manifest import RandomSeedManager, build_reproducibility_manifest

__all__ = [
    "PaperConfigValidator",
    "RandomSeedManager",
    "ReproductionMode",
    "build_reproducibility_manifest",
    "load_paper_config",
]
