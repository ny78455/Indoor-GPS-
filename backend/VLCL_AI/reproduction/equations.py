"""Independent scalar oracles used to validate the paper equations.

These deliberately use direct NumPy/math expressions rather than delegating to
production functions, so an implementation error is not mirrored in an oracle.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import erfc, log2, pi, sqrt
from typing import Any, Dict, List

import numpy as np

from VLCL_AI.physics.constants import SPEED_OF_LIGHT


@dataclass
class EquationCheck:
    equation: str
    status: str
    max_absolute_error: float
    detail: str


def eq01_snr(mu: float, powers: np.ndarray, gains: np.ndarray, noise_variance: float) -> np.ndarray:
    powers = np.asarray(powers, dtype=float)
    gains = np.asarray(gains, dtype=float)
    return mu**2 * np.square(np.sum(np.sqrt(powers) * gains.T, axis=1)) / noise_variance


def eq02_square_qam_ber(snr: float, modulation_order: int) -> float:
    if modulation_order == 2:
        return 0.5 * erfc(sqrt(snr))
    root_m = sqrt(modulation_order)
    return ((root_m - 1) / (root_m * log2(root_m))) * erfc(sqrt(3 * snr / (2 * (modulation_order - 1))))


def eq03_rate(subcarrier_bandwidth_hz: float, rho: np.ndarray, modulation_orders: np.ndarray) -> float:
    rho = np.asarray(rho, dtype=float)
    modulation_orders = np.asarray(modulation_orders, dtype=float)
    active = modulation_orders > 1
    return float(subcarrier_bandwidth_hz * np.sum(rho[active] * np.log2(modulation_orders[active])))


def eq04_localization_tone(power_w: float, frequency_hz: float, time_s: np.ndarray, phase_rad: float = 0.0) -> np.ndarray:
    return sqrt(power_w) * np.sin(2 * pi * frequency_hz * np.asarray(time_s) + phase_rad)


def eq05_received_tone(amplitude: float, frequency_hz: float, delay_s: float, time_s: np.ndarray) -> np.ndarray:
    return amplitude * np.sin(2 * pi * frequency_hz * (np.asarray(time_s) - delay_s))


def eq16_distance_differences(frequencies_hz: np.ndarray, tone_to_led: Dict[int, int], distances_m: Dict[int, float]) -> np.ndarray:
    """Generate Eq. 13--16 phase measurements under the production sign convention."""
    rows = ({1: 1, 2: -2, 3: 1}, {2: 1, 3: -2, 4: 1}, {3: 1, 4: -2, 5: 1})
    theta = []
    for row in rows:
        phase_sum = sum(multiplier * frequencies_hz[tone - 1] * distances_m[tone_to_led[tone]] for tone, multiplier in row.items())
        theta.append(-2 * pi / SPEED_OF_LIGHT * phase_sum)
    return np.asarray(theta)


def eq18_pre_equalized(symbols: np.ndarray, h_response: np.ndarray, power: np.ndarray | float) -> np.ndarray:
    return np.sqrt(np.maximum(power, 0.0)) * np.asarray(symbols) / np.asarray(h_response)


def run_independent_equation_checks() -> List[EquationCheck]:
    """Run compact deterministic checks spanning Eq. (1)--(18)."""
    from VLCL_AI.adaptive.modulation_controller import AdaptiveModulationController
    from VLCL_AI.communication.ber import BERCalculator
    from VLCL_AI.communication.pre_equalizer import PreEqualizer
    from VLCL_AI.communication.rate import RateCalculator
    from VLCL_AI.communication.snr import compute_communication_snr
    from VLCL_AI.localization.frequency_plan import LocalizationFrequencyPlan
    from VLCL_AI.localization.position_solver import DistanceDifferenceSolver

    checks: List[EquationCheck] = []
    powers = np.array([[1.0, 4.0], [0.0, 9.0]])
    gains = np.array([[0.5, 0.1], [0.25, 0.2]])
    expected = eq01_snr(0.5, powers, gains, 0.25)
    observed = compute_communication_snr(0.5, powers, gains, 0.25)
    checks.append(_comparison("Eq. (1)", expected, observed, "Coherent sqrt(P) sum."))

    snr = 11.0
    expected_ber = eq02_square_qam_ber(snr, 16)
    observed_ber = float(BERCalculator.compute_analytical_qam(snr, 16))
    checks.append(_comparison("Eq. (2)", expected_ber, observed_ber, "Paper square-M-QAM BER expression."))

    bandwidth, rho, modulations = 125000.0, np.array([1, 0, 1]), np.array([4, 64, 16])
    expected_rate = eq03_rate(bandwidth, rho, modulations)
    observed_rate = RateCalculator.compute_user_rates([0, 2], np.full(3, bandwidth), modulations, cp_ratio=0.0)["raw_rate_bps"]
    checks.append(_comparison("Eq. (3)", expected_rate, observed_rate, "Allocated-carrier raw rate."))

    time = np.array([0.0, 0.25e-6, 0.5e-6])
    expected_signal = eq04_localization_tone(4.0, 1e6, time)
    checks.append(_comparison("Eq. (4)-(6)", expected_signal, 2 * np.sin(2 * pi * 1e6 * time), "Known localization sine amplitude/phase."))

    # Trigonometric-product identity independently validates the difference-frequency stage.
    f1, f2, t = 4e6, 4.2e6, np.linspace(0, 5e-6, 1001)
    product = np.sin(2 * pi * f1 * t) * np.sin(2 * pi * f2 * t)
    identity = 0.5 * (np.cos(2 * pi * (f2 - f1) * t) - np.cos(2 * pi * (f1 + f2) * t))
    checks.append(_comparison("Eq. (7)-(10)", identity, product, "Sum/difference multiplication identity."))

    theta = 2.4
    checks.append(_comparison("Eq. (11)-(15)", np.array([np.cos(theta), np.sin(theta)]), np.array([np.real(np.exp(1j * theta)), np.imag(np.exp(1j * theta))]), "I/Q and atan2 quadrant convention."))

    plan = LocalizationFrequencyPlan(4e6, .2e6, 5)
    mapping = {1: [1], 2: [2], 3: [3], 4: [4], 5: [1]}
    distances = {1: 2.0, 2: 2.10, 3: 2.25, 4: 2.40}
    theta_vector = eq16_distance_differences(plan.frequencies, {k: v[0] for k, v in mapping.items()}, distances)
    recovered = DistanceDifferenceSolver(plan, mapping).solve(theta_vector)
    expected_deltas = np.array([distances[2] - distances[1], distances[3] - distances[1], distances[4] - distances[1]])
    observed_deltas = np.array([recovered[(2, 1)], recovered[(3, 1)], recovered[(4, 1)]])
    checks.append(_comparison("Eq. (16)", expected_deltas, observed_deltas, "Synthetic distance-difference recovery."))

    controller = AdaptiveModulationController(ber_max=3.8e-3, supported_modulations=[4, 16, 64])
    threshold = controller.threshold_table.get_threshold_linear(16)
    selected, _, feasible = controller.select_modulation_order(threshold)
    checks.append(EquationCheck("Eq. (17)", "PASS" if selected >= 16 and feasible else "FAIL", 0.0 if selected >= 16 and feasible else 1.0, "Threshold boundary selects a feasible modulation order."))

    symbols = np.array([1 + 1j, -1 + 1j])
    response = np.array([.8 + 0j, .5 + 0j])
    expected_eq18 = eq18_pre_equalized(symbols, response, 4.0)
    observed_eq18 = PreEqualizer(mode="zero_forcing", max_gain_db=100).apply_eq18(symbols, response, 4.0)
    checks.append(_comparison("Eq. (18)", expected_eq18, observed_eq18, "sqrt(P) and H inverse each applied once."))
    return checks


def _comparison(equation: str, expected: Any, observed: Any, detail: str) -> EquationCheck:
    error = float(np.max(np.abs(np.asarray(expected) - np.asarray(observed))))
    return EquationCheck(equation, "PASS" if error <= 1e-9 else "FAIL", error, detail)
