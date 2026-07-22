import unittest

from VLCL_AI.adaptive.modulation_controller import AdaptiveModulationController


class TestPaperEquationSeventeen(unittest.TestCase):
    def test_threshold_boundary_is_feasible(self):
        controller = AdaptiveModulationController(ber_max=3.8e-3, supported_modulations=[4, 16, 64])
        threshold = controller.threshold_table.get_threshold_linear(16)
        modulation, ber, feasible = controller.select_modulation_order(threshold)
        self.assertTrue(feasible)
        self.assertGreaterEqual(modulation, 16)
        self.assertLessEqual(ber, 3.8e-3 + 1e-12)
