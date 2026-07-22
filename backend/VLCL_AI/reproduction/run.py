"""Command-line entry point for deterministic Module 9 validation runs.

Example:
    python -m VLCL_AI.reproduction.run --config configs/paper_exact.yaml --experiment all --seed 42
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .config import PaperConfigValidator, ReproductionMode, hash_config, load_paper_config
from .equations import run_independent_equation_checks
from .manifest import RandomSeedManager, build_reproducibility_manifest, write_json


def _report(equation_results: list[dict], validation: Any, config_hash: str) -> str:
    passed = sum(item["status"] == "PASS" for item in equation_results)
    total = len(equation_results)
    level = "LEVEL A" if passed == total else "NONE"
    status = "PARTIALLY_VALIDATED" if validation.is_valid and passed == total else "NOT_VALIDATED"
    lines = [
        "# Module 9 Reproduction Report", "",
        "## Executive summary", "",
        f"Configuration mode: `{validation.mode.value}`. Equation checks: **{passed}/{total} pass**. ",
        "No claim of numerical paper reproduction is made without paper data and a complete paper configuration.", "",
        "## Equation validation", "", "| Equation | Status | Max absolute error | Evidence |", "|---|---|---:|---|",
    ]
    lines += [f"| {item['equation']} | {item['status']} | {item['max_absolute_error']:.3e} | {item['detail']} |" for item in equation_results]
    lines += [
        "", "## Scientific conclusion", "",
        f"Reproduction level achieved: **{level}** (mathematical checks only).  ",
        f"Module 9 status: **{status}**.  ",
        "Physical experimental equivalence is not inferable from this simulation alone.", "",
        "## Fidelity dashboard", "",
        "| Category | Result |", "|---|---|",
        "| Geometry | Not scored: paper-exact dimensions/coordinates are incomplete. |",
        "| Channel | Not scored: optical power and receiver parameters are incomplete. |",
        "| Communication | Equation-level only; no paper curve data loaded. |",
        "| Localization | Equation-level only; no paper position-error data loaded. |",
        "| Optimization | Not scored: no paper numerical trace/data loaded. |",
        "", "## Reproducibility", "",
        f"Config hash: `{config_hash}`. See `REPRODUCIBILITY_MANIFEST.json` and `PAPER_CONFIG_VALIDATION_REPORT.md` in this run directory.",
    ]
    return "\n".join(lines) + "\n"


def run(config_path: str | Path, experiment: str = "all", seed: int = 42, output_dir: str | Path = "experiments/paper_reproduction/outputs", mode: str | None = None) -> int:
    config = load_paper_config(config_path)
    if mode:
        config["reproduction_mode"] = mode
        config["_config_hash"] = hash_config(config)
    validation = PaperConfigValidator().validate(config)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    seed_manager = RandomSeedManager(seed)
    seed_manager.apply_legacy_seeds()
    (output / "PAPER_CONFIG_VALIDATION_REPORT.md").write_text(validation.to_markdown(config["_config_hash"]), encoding="utf-8")

    checks = []
    if experiment in {"all", "equations"}:
        checks = [asdict(check) for check in run_independent_equation_checks()]
        write_json(output / "raw" / "equation_checks.json", {"checks": checks, "seed_policy": seed_manager.policy()})

    report = _report(checks, validation, config["_config_hash"])
    (output / "MODULE_9_REPRODUCTION_REPORT.md").write_text(report, encoding="utf-8")
    manifest = build_reproducibility_manifest(Path(__file__).resolve().parents[3], config["_config_hash"], seed_manager, [experiment])
    write_json(output / "REPRODUCIBILITY_MANIFEST.json", manifest)
    print("=" * 50)
    print("MODULE 9 — PAPER REPRODUCTION VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Configuration: {validation.mode.value}")
    print(f"Equation tests: {sum(item['status'] == 'PASS' for item in checks)} / {len(checks)} PASS")
    print(f"Configuration validation: {'PASS' if validation.is_valid else 'INCOMPLETE'}")
    print("Reproduction level achieved: LEVEL A" if checks and all(item["status"] == "PASS" for item in checks) else "Reproduction level achieved: NONE")
    print("MODULE_9_STATUS: PARTIALLY_VALIDATED" if validation.is_valid and checks else "MODULE_9_STATUS: NOT_VALIDATED")
    return 0 if validation.is_valid and all(item["status"] == "PASS" for item in checks) else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the VLCL Module 9 reproduction validation.")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "configs" / "paper_exact.yaml"))
    parser.add_argument("--experiment", choices=["all", "equations", "config"], default="all")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="experiments/paper_reproduction/outputs")
    parser.add_argument("--mode", choices=[item.value for item in ReproductionMode])
    arguments = parser.parse_args()
    return run(arguments.config, arguments.experiment, arguments.seed, arguments.output_dir, arguments.mode)


if __name__ == "__main__":
    raise SystemExit(main())
