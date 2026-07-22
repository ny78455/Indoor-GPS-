import unittest
import numpy as np

from VLCL_AI.localization.frequency_plan import LocalizationFrequencyPlan
from VLCL_AI.localization.position_solver import DistanceDifferenceSolver
from VLCL_AI.reproduction.equations import eq04_localization_tone, eq16_distance_differences


class TestPaperEquationsFourToSixteen(unittest.TestCase):
    def test_eq04_known_sine(self):
        time = np.array([0.0, 0.25e-6, 0.5e-6])
        np.testing.assert_allclose(eq04_localization_tone(4.0, 1e6, time), [0.0, 2.0, 0.0], atol=1e-12)

    def test_eq07_to_eq10_product_identity(self):
        time = np.linspace(0.0, 1e-6, 101)
        first = np.sin(2 * np.pi * 4e6 * time)
        second = np.sin(2 * np.pi * 4.2e6 * time)
        expected = .5 * (np.cos(2 * np.pi * .2e6 * time) - np.cos(2 * np.pi * 8.2e6 * time))
        np.testing.assert_allclose(first * second, expected, atol=1e-12)

    def test_eq11_to_eq15_iq_all_quadrants(self):
        for theta in np.linspace(-3 * np.pi / 4, 3 * np.pi / 4, 4):
            self.assertAlmostEqual(np.arctan2(np.sin(theta), np.cos(theta)), theta, places=12)

    def test_eq16_synthetic_distance_differences(self):
        plan = LocalizationFrequencyPlan(4e6, .2e6)
        mapping = {1: [1], 2: [2], 3: [3], 4: [4], 5: [1]}
        distances = {1: 2.0, 2: 2.1, 3: 2.25, 4: 2.4}
        theta = eq16_distance_differences(plan.frequencies, {key: value[0] for key, value in mapping.items()}, distances)
        actual = DistanceDifferenceSolver(plan, mapping).solve(theta)
        np.testing.assert_allclose([actual[(2, 1)], actual[(3, 1)], actual[(4, 1)]], [.1, .25, .4], atol=1e-10)
