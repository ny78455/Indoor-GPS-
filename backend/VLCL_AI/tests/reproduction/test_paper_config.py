import unittest
from pathlib import Path

from VLCL_AI.reproduction.config import PaperConfigValidator, load_paper_config


class TestPaperConfiguration(unittest.TestCase):
    def test_exact_config_honestly_fails_missing_values(self):
        path = Path(__file__).resolve().parents[2] / "configs" / "paper_exact.yaml"
        result = PaperConfigValidator().validate(load_paper_config(path))
        self.assertFalse(result.is_valid)
        self.assertTrue(any(item.code == "REP-CFG-003" for item in result.errors))
