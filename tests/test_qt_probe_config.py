"""Dependency-free configuration/contract regressions; GUI exercised in Windows CI."""
import json
import unittest
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "adapters" / "qt_style_probe" / "target.json"

class QtStyleProbeConfigurationTests(unittest.TestCase):
    def test_independent_2_by_2_styling_matrix(self):
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(cfg["requested_styles"], ["windows11", "Fusion"])
        self.assertEqual(len(cfg["variants"]), 4)
        self.assertEqual(
            {(c["palette"], c["scoped_qss"]) for c in cfg["variants"]},
            {(False, False), (True, False), (False, True), (True, True)},
        )

    def test_only_fabricated_sample_data_and_scoped_card_config(self):
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(cfg["schema"], "qt-style-probe.lab.v1")
        self.assertEqual(cfg["source"]["path"], "tools/qt_style_probe/probe.py")
        self.assertIn("IRR", cfg["fields"]["amount"])
        self.assertEqual(set(cfg["card_qss"]), {"background", "border"})

if __name__ == "__main__":
    unittest.main()
