"""Paper configuration loading, provenance handling, and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

import hashlib
import math

import yaml


class ReproductionMode(str, Enum):
    PAPER_EXACT = "PAPER_EXACT"
    PAPER_INFERRED = "PAPER_INFERRED"
    DIGITAL_TWIN_EXTENDED = "DIGITAL_TWIN_EXTENDED"


KNOWN_PROVENANCE = {
    "PAPER_EXPLICIT", "PAPER_DERIVED", "PAPER_INFERRED",
    "SIMULATION_ASSUMPTION", "UNKNOWN", "PAPER_AMBIGUITY",
    "MODEL_EXTENSION",
}


@dataclass(frozen=True)
class ValidationFinding:
    severity: str
    code: str
    message: str
    path: str = ""


@dataclass
class PaperConfigValidation:
    mode: ReproductionMode
    findings: List[ValidationFinding] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationFinding]:
        return [item for item in self.findings if item.severity == "ERROR"]

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def add(self, severity: str, code: str, message: str, path: str = "") -> None:
        self.findings.append(ValidationFinding(severity, code, message, path))

    def to_markdown(self, config_hash: str = "") -> str:
        lines = [
            "# Paper Configuration Validation Report", "",
            f"Mode: `{self.mode.value}`  ",
            f"Configuration hash: `{config_hash}`  ",
            f"Status: **{'PASS' if self.is_valid else 'INCOMPLETE / FAIL'}**", "",
            "| Severity | Code | Configuration path | Finding |",
            "|---|---|---|---|",
        ]
        if not self.findings:
            lines.append("| INFO | NONE | — | No validation findings. |")
        for item in self.findings:
            lines.append(f"| {item.severity} | {item.code} | `{item.path or '—'}` | {item.message} |")
        lines.extend([
            "", "## Interpretation", "",
            "`PAPER_EXACT` rejects critical inferred, assumed, ambiguous, or unknown values. "
            "Other modes retain those values only when their provenance remains explicit.",
        ])
        return "\n".join(lines) + "\n"


def load_paper_config(path: str | Path) -> Dict[str, Any]:
    """Load a canonical YAML configuration and attach a stable content hash."""
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    if not isinstance(config, dict):
        raise ValueError("Paper configuration root must be a mapping.")
    config["_config_path"] = str(source.resolve())
    config["_config_hash"] = hash_config(config)
    return config


def hash_config(config: Mapping[str, Any]) -> str:
    serializable = {key: value for key, value in config.items() if not key.startswith("_")}
    payload = yaml.safe_dump(serializable, sort_keys=True, allow_unicode=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _value(entry: Any) -> Any:
    return entry.get("value") if isinstance(entry, Mapping) and "value" in entry else entry


def _provenance(entry: Any) -> str:
    return str(entry.get("provenance", "UNKNOWN")) if isinstance(entry, Mapping) else "UNKNOWN"


class PaperConfigValidator:
    """Validates canonical paper configs without manufacturing missing values."""

    CRITICAL_PATHS = (
        "room.width_m", "room.length_m", "room.height_m", "receiver.height_m",
        "receiver.area_m2", "receiver.responsivity_a_per_w", "receiver.fov_deg",
        "leds", "communication.bandwidth_hz", "communication.fft_size",
        "communication.ber_max", "localization.start_frequency_hz",
        "localization.spacing_hz", "localization.tone_count",
    )

    def validate(self, config: Mapping[str, Any]) -> PaperConfigValidation:
        try:
            mode = ReproductionMode(str(config.get("reproduction_mode", "PAPER_EXACT")))
        except ValueError as exc:
            raise ValueError("reproduction_mode must be PAPER_EXACT, PAPER_INFERRED, or DIGITAL_TWIN_EXTENDED") from exc
        result = PaperConfigValidation(mode=mode)
        self._check_required(config, result)
        self._check_provenance(config, result)
        self._check_geometry(config, result)
        self._check_communication(config, result)
        self._check_localization(config, result)
        self._check_power(config, result)
        return result

    def _get(self, config: Mapping[str, Any], path: str) -> Any:
        current: Any = config
        for part in path.split("."):
            if not isinstance(current, Mapping) or part not in current:
                return None
            current = current[part]
        return _value(current)

    def _check_required(self, config: Mapping[str, Any], result: PaperConfigValidation) -> None:
        for path in self.CRITICAL_PATHS:
            value = self._get(config, path)
            if value is None or value == "":
                result.add("ERROR", "REP-CFG-001", "Required value is absent; exact reproduction is not supportable.", path)

    def _walk_entries(self, data: Any, prefix: str = "") -> Iterable[Tuple[str, Mapping[str, Any]]]:
        if isinstance(data, Mapping):
            if "value" in data:
                yield prefix, data
            for key, value in data.items():
                if key not in {"value", "provenance", "reference", "units", "note"}:
                    child = f"{prefix}.{key}" if prefix else str(key)
                    yield from self._walk_entries(value, child)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                yield from self._walk_entries(value, f"{prefix}[{index}]")

    def _check_provenance(self, config: Mapping[str, Any], result: PaperConfigValidation) -> None:
        for path, entry in self._walk_entries(config):
            provenance = _provenance(entry)
            if provenance not in KNOWN_PROVENANCE:
                result.add("ERROR", "REP-CFG-002", f"Unknown provenance '{provenance}'.", path)
            if result.mode == ReproductionMode.PAPER_EXACT and provenance in {
                "PAPER_INFERRED", "SIMULATION_ASSUMPTION", "UNKNOWN", "PAPER_AMBIGUITY", "MODEL_EXTENSION",
            }:
                result.add("ERROR", "REP-CFG-003", f"{provenance} is not allowed in PAPER_EXACT.", path)
            elif provenance in {"PAPER_INFERRED", "SIMULATION_ASSUMPTION", "UNKNOWN", "PAPER_AMBIGUITY"}:
                result.add("WARNING", "REP-CFG-004", f"Using documented {provenance}.", path)

    def _check_geometry(self, config: Mapping[str, Any], result: PaperConfigValidation) -> None:
        dimensions = [self._get(config, f"room.{name}") for name in ("width_m", "length_m", "height_m")]
        if any(value is not None and (not isinstance(value, (int, float)) or value <= 0) for value in dimensions):
            result.add("ERROR", "REP-CFG-010", "Room dimensions must be positive metres.", "room")
        leds = config.get("leds", [])
        if leds is not None and (not isinstance(leds, list) or len(leds) < 4):
            result.add("ERROR", "REP-CFG-011", "A-DPDOA reference topology requires four LEDs.", "leds")
        identifiers = []
        for index, led in enumerate(leds or []):
            identifier = _value(led.get("id")) if isinstance(led, Mapping) else None
            position = _value(led.get("position_m")) if isinstance(led, Mapping) else None
            identifiers.append(identifier)
            if not isinstance(position, list) or len(position) != 3 or not all(isinstance(v, (int, float)) for v in position):
                result.add("ERROR", "REP-CFG-012", "LED position must be a three-element coordinate in metres.", f"leds[{index}].position_m")
        if len([value for value in identifiers if value is not None]) != len(set(value for value in identifiers if value is not None)):
            result.add("ERROR", "REP-CFG-013", "LED identifiers must be unique.", "leds")

    def _check_communication(self, config: Mapping[str, Any], result: PaperConfigValidation) -> None:
        bandwidth = self._get(config, "communication.bandwidth_hz")
        fft_size = self._get(config, "communication.fft_size")
        ber_max = self._get(config, "communication.ber_max")
        if bandwidth is not None and (not isinstance(bandwidth, (int, float)) or bandwidth <= 0):
            result.add("ERROR", "REP-CFG-020", "Bandwidth must be a positive value in Hz.", "communication.bandwidth_hz")
        if fft_size is not None and (not isinstance(fft_size, int) or fft_size < 8 or fft_size & (fft_size - 1)):
            result.add("ERROR", "REP-CFG-021", "FFT size must be a power of two of at least 8.", "communication.fft_size")
        if ber_max is not None and (not isinstance(ber_max, (int, float)) or not 0 < ber_max < 1):
            result.add("ERROR", "REP-CFG-022", "BER limit must be in (0, 1).", "communication.ber_max")
        orders = self._get(config, "communication.modulation_orders")
        supported = {2, 4, 16, 64, 256}
        if orders is not None:
            unsupported = [order for order in orders if order not in supported]
            if unsupported:
                result.add("WARNING", "REP-CFG-023", f"Analytical BER oracle has no square-QAM implementation for {unsupported}.", "communication.modulation_orders")

    def _check_localization(self, config: Mapping[str, Any], result: PaperConfigValidation) -> None:
        start = self._get(config, "localization.start_frequency_hz")
        spacing = self._get(config, "localization.spacing_hz")
        count = self._get(config, "localization.tone_count")
        sample_rate = self._get(config, "localization.sample_rate_hz")
        if count is not None and count != 5:
            result.add("ERROR", "REP-CFG-030", "A-DPDOA requires exactly five tones.", "localization.tone_count")
        if start is not None and start <= 0 or spacing is not None and spacing <= 0:
            result.add("ERROR", "REP-CFG-031", "Localization frequencies and spacing must be positive Hz values.", "localization")
        if start is not None and spacing is not None and count is not None and sample_rate is not None:
            maximum = start + (count - 1) * spacing
            if sample_rate < 2 * maximum:
                result.add("ERROR", "REP-CFG-032", "Sample rate violates Nyquist for the highest localization tone.", "localization.sample_rate_hz")
        mapping = self._get(config, "localization.tone_to_led_map")
        if mapping is not None and (not isinstance(mapping, Mapping) or set(map(str, mapping.keys())) != {"1", "2", "3", "4", "5"}):
            result.add("ERROR", "REP-CFG-033", "Tone-to-LED mapping must cover tone IDs 1 through 5.", "localization.tone_to_led_map")

    def _check_power(self, config: Mapping[str, Any], result: PaperConfigValidation) -> None:
        total = self._get(config, "power.total_budget_w")
        reserve = self._get(config, "power.localization_reserve_w")
        per_led = self._get(config, "power.per_led_max_w")
        if total is not None and total <= 0:
            result.add("ERROR", "REP-CFG-040", "Total power budget must be positive W.", "power.total_budget_w")
        if reserve is not None and reserve < 0:
            result.add("ERROR", "REP-CFG-041", "Localization reserve cannot be negative W.", "power.localization_reserve_w")
        if reserve is not None and per_led is not None and reserve > per_led:
            result.add("ERROR", "REP-CFG-042", "Localization reserve exceeds per-LED maximum power.", "power")
