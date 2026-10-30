"""Independent Lab tests of static Bank2Odoo approval-control equivalence.

No product modules are imported; all interactions use QTest and synthetic text.
"""
from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QStyle, QStyleOptionButton
    from adapters.qt_style_probe import lab_runner as lab
    from adapters.qt_style_probe import approval_equivalence as eq
    QT = True
except ImportError:
    QT = False


@unittest.skipUnless(QT, "PySide6-Essentials required; run in existing Windows CI")
class ProductEquivalenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.cfg, _ = lab.load_config()

    def make(self, treatment):
        return eq.make_equivalent(self.cfg, "Fusion", "Tahoma", treatment)

    def test_product_proxy_has_minimum_22_metric_and_full_row_click(self):
        host, controls, proxy = self.make("native")
        try:
            cb = controls["approval"]
            self.assertEqual(cb.text(), eq.whole.PRODUCT_TEXT)
            self.assertGreaterEqual(cb.height(), 52)
            self.assertEqual(cb.focusPolicy(), Qt.FocusPolicy.StrongFocus)
            met = eq.effective_geometry(cb, proxy)
            self.assertGreaterEqual(met["proxy_width"], 22)
            self.assertGreaterEqual(met["proxy_height"], 22)
            self.assertGreaterEqual(met["indicator_rect_width"], 22)
            self.assertGreaterEqual(met["indicator_rect_height"], 22)
            self.assertTrue(met["metric_preserved"])
            clicked = eq.capture_case(host, controls, "checked_row",
                                      Path(self.tmp.name), "native")
            self.assertTrue(clicked["semantic"])
            self.assertTrue(cb.isChecked())
        finally:
            host.close()

    def test_scoped_border_must_not_silently_claim_to_preserve_22px(self):
        host, controls, proxy = self.make("unchecked_border")
        try:
            cb = controls["approval"]
            metrics = eq.effective_geometry(cb, proxy)
            self.assertEqual(cb.objectName(), "nativeApproval")
            self.assertIn("QCheckBox#nativeApproval::indicator:unchecked",
                          cb.styleSheet())
            self.assertFalse(controls["card"].styleSheet())
            # This test records the observable Qt metric even when QSS
            # overrides it. The evaluator must treat <22px as FAIL.
            self.assertIsInstance(metrics["metric_preserved"], bool)
            for key in ("proxy_width", "effective_width", "indicator_rect_width",
                        "proxy_height", "effective_height", "indicator_rect_height"):
                self.assertGreater(metrics[key], 0, key)
        finally:
            host.close()

    def test_space_transition_focus_tab_and_full_row_reset(self):
        host, controls, proxy = self.make("unchecked_border")
        try:
            cb = controls["approval"]
            for state in ("checked_space", "unchecked_space",
                          "checked_row", "unchecked_row", "focus_tab"):
                with self.subTest(state=state):
                    result = eq.capture_case(host, controls, state,
                                             Path(self.tmp.name), state)
                    self.assertTrue(result["semantic"], state)
                    if state.startswith("checked_"):
                        self.assertTrue(cb.isChecked())
                    if state.startswith("unchecked_"):
                        self.assertFalse(cb.isChecked())
                    self.assertTrue(Path(self.tmp.name, result["raw_png"]).exists())
        finally:
            host.close()

    def test_ignored_space_does_not_count_as_valid_transition(self):
        host, controls, proxy = self.make("native")
        try:
            with patch.object(eq.QTest, "keyClick", return_value=None):
                result = eq.capture_case(host, controls, "checked_space",
                                         Path(self.tmp.name), "noop")
            self.assertFalse(result["semantic"])
        finally:
            host.close()

    def test_missing_font_and_os_scenario_are_not_executed(self):
        with tempfile.TemporaryDirectory() as outdir:
            out = Path(outdir)
            with patch.object(eq.QStyleFactory, "keys",
                              return_value=["Fusion"]), patch.object(
                                  eq.QFontDatabase, "families", return_value=["Tahoma"]):
                eq.run(self.cfg, out, "simulated-font-test")
            with (out / "measurements.csv").open(
                encoding="utf-8", newline=""
            ) as f:
                reader = csv.DictReader(f)
                self.assertEqual(tuple(reader.fieldnames), eq.CSV_FIELDS)
                rows = list(reader)
            self.assertEqual(len(rows), 2*2*2*7)
            available = [x for x in rows if x["requested_style"]=="Fusion"
                         and x["requested_font"]=="Tahoma"]
            self.assertEqual(len(available), 14)
            self.assertTrue(all(x["execution"]=="EXECUTED" for x in available))
            unavailable = [x for x in rows if x not in available]
            self.assertEqual(len(unavailable), 42)
            self.assertTrue(all(x["execution"]=="NOT_EXECUTED"
                                and x["assessment"]=="NOT_PROVEN"
                                for x in unavailable))
            self.assertEqual(len(list(out.glob("preview_*.png"))), 2)
            self.assertEqual(len(list(out.glob("*_checkbox_*.png"))), 4)
            meta = json.loads((out/"environment.json").read_text(encoding="utf-8"))
            self.assertFalse(meta["physical_windows11_environment"])
            self.assertEqual(
                set(meta["os_display_scale_100_125_150"].values()), {"NOT_EXECUTED"}
            )
            for row in available:
                self.assertTrue((out/row["raw_png"]).exists())
                self.assertNotEqual(row["assessment"], "")
                if row["assessment"] == "PASS":
                    self.assertTrue(meta["observations"][row["candidate"]][
                        "geometry"]["metric_preserved"])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
