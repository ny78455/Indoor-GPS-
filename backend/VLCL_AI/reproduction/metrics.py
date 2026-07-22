"""Transparent comparison and Monte-Carlo summary metrics."""

from __future__ import annotations

from typing import Dict, Iterable

import numpy as np


def comparison_metrics(paper_values: Iterable[float], simulated_values: Iterable[float], epsilon: float = 1e-12) -> Dict[str, float | None]:
    paper = np.asarray(list(paper_values), dtype=float)
    simulated = np.asarray(list(simulated_values), dtype=float)
    if paper.shape != simulated.shape or paper.size == 0:
        raise ValueError("Paper and simulated values must be non-empty arrays with identical shapes.")
    residual = simulated - paper
    metrics: Dict[str, float | None] = {
        "mae": float(np.mean(np.abs(residual))),
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "max_absolute_deviation": float(np.max(np.abs(residual))),
        "mean_relative_error": float(np.mean(np.abs(residual) / np.maximum(np.abs(paper), epsilon))),
    }
    if paper.size >= 2 and np.std(paper) > epsilon and np.std(simulated) > epsilon:
        metrics["pearson_correlation"] = float(np.corrcoef(paper, simulated)[0, 1])
        metrics["r_squared"] = float(1 - np.sum(residual**2) / np.sum((paper - np.mean(paper)) ** 2))
    else:
        metrics["pearson_correlation"] = None
        metrics["r_squared"] = None
    return metrics


def monte_carlo_summary(samples: Iterable[float], confidence_z: float = 1.959963984540054) -> Dict[str, float | int]:
    values = np.asarray(list(samples), dtype=float)
    if values.size == 0:
        raise ValueError("At least one Monte Carlo sample is required.")
    deviation = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
    half_width = confidence_z * deviation / np.sqrt(values.size) if values.size > 1 else 0.0
    mean = float(np.mean(values))
    return {
        "runs": int(values.size), "mean": mean, "std": deviation, "median": float(np.median(values)),
        "min": float(np.min(values)), "max": float(np.max(values)),
        "ci95_lower": mean - float(half_width), "ci95_upper": mean + float(half_width),
    }


def zero_error_ber_upper_bound(bits_transmitted: int, confidence: float = 0.95) -> float:
    """One-sided binomial upper confidence bound when zero bit errors are seen."""
    if bits_transmitted <= 0:
        raise ValueError("bits_transmitted must be positive.")
    return float(1 - (1 - confidence) ** (1 / bits_transmitted))
