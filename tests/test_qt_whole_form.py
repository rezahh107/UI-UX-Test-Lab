"""Whole-form Persian checkbox diagnostic: falsification and evidence contracts."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtGui import QFont
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QStyleFactory
    from adapters.qt_style_probe import lab_runner as lab
    from adapters.qt_style_probe import primary_action as primary
    from adapters.qt_style_probe import whole_form as whole
    QT = True
except ImportError:
    QT = False


@unittest.skipUnless(QT, "Static UI copy checked on PySide6 Windows CI")
class StaticSourceContracts(unittest.TestCase):
    def test_product_label_is_static_ui_copy_and_synthetic_is_distinct(self):
        self.assertEqual(
            whole.PRODUCT_TEXT, "اطلاعات مالی بالا را شخصاً بررسی و تأیید کرده‌ام."
        )
        self.assertEqual(whole.PRODUCT_REF["commit"],
                         "d06b35f41ac46936716b186fb1dfac33da983eb9")
        self.assertNotEqual(whole.PRODUCT_TEXT,
                            "اطلاعات نمونه را بررسی و تأیید می‌کنم")


@unittest.skipUnless(QT, "Needs PySide6-Essentials on Windows CI")
class WholeFormQtRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.cfg, _ = lab.load_config()

    def setUp(self):
        style = QStyleFactory.create("Fusion")
        self.assertIsNotNone(style)
        self.app.setStyle(style)
        lab.apply_palette(self.app, self.cfg, True)
        self.host, self.controls = lab.build_host(self.cfg, self.cfg["variants"][0])
        primary.emphasize(self.controls["button"], "button_qss", "dark")
        self.host.show()
        QTest.qWait(55)

    def tearDown(self):
        self.host.close()

    def test_checked_unchecked_space_and_full_row_are_real_transitions(self):
        with tempfile.TemporaryDirectory() as folder:
            for state in ("checked_space", "unchecked_space",
                          "checked_row", "unchecked_row"):
                full, cb_shot, metric, ok, keyboard, row, focus = whole.capture_state(
                    self.host, self.controls, state, Path(folder), "test")
                self.assertTrue(ok, state)
                self.assertFalse(full.isNull())
                self.assertFalse(cb_shot.isNull())
                self.assertEqual(bool(keyboard), state.endswith("space"))
                self.assertEqual(bool(row), state.endswith("row"))
                self.assertEqual(self.controls["approval"].isChecked(),
                                 state.startswith("checked"))
                self.assertTrue((Path(folder) / ("test_"+state+".png")).exists())

    def test_ignored_space_fails_semantic_control(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(whole.QTest, "keyClick", return_value=None):
                _, _, _, ok, keyboard, _, _ = whole.capture_state(
                    self.host, self.controls, "checked_space",
                    Path(folder), "noop"
                )
            self.assertFalse(ok)
            self.assertFalse(keyboard)

    def test_matching_qcheckbox_and_qlabel_keep_text_geometry_and_font(self):
        with tempfile.TemporaryDirectory() as folder:
            name = "product_fixture"
            meta, label, checkbox = whole.text_fixture(
                whole.PRODUCT_TEXT, QFont("Tahoma", 11), name, Path(folder)
            )
            self.assertTrue(meta["text_equal"])
            self.assertTrue(meta["dimensions_equal"])
            self.assertTrue(meta["direction_equal"])
            self.assertTrue(meta["font_equal"])
            self.assertFalse(meta["per_glyph_fallback_proven"])
            self.assertEqual(meta["text"], whole.PRODUCT_TEXT)
            self.assertFalse(label.isNull())
            self.assertFalse(checkbox.isNull())
            self.assertTrue((Path(folder)/ (name+"_label.png")).exists())
            self.assertTrue((Path(folder)/ (name+"_checkbox.png")).exists())

    def test_malformed_joining_fixture_is_distinguished(self):
        with tempfile.TemporaryDirectory() as folder:
            controls = whole.negative_controls(
                self.app, self.cfg, Path(folder), QFont("Tahoma", 11)
            )
            self.assertTrue(controls["joining"]["expected_distinguished"])
            self.assertTrue(controls["joining"]["zwnj_inserted_in_word"])
            # Deliberately broken Seen–Yeh joining must be visible to at
            # least one native Qt text renderer, not just string inequality.
            self.assertTrue(
                controls["joining"]["label_visual_changed"] or
                controls["joining"]["checkbox_visual_changed"],
                "Malformed ZWNJ was not visually distinguished by Qt"
            )
            self.assertEqual(
                controls["fixture_info"]["valid"]["text"], whole.PRODUCT_TEXT
            )
            self.assertNotEqual(controls["fixture_info"]["malformed"]["text"],
                                whole.PRODUCT_TEXT)
            self.assertTrue((Path(folder)/"negative_zwnj_checkbox.png").exists())
            self.assertTrue((Path(folder)/"negative_indicator.png").exists())
            self.assertTrue(controls["indicator_detected_as_inadequate"])

    def test_missing_windows11_not_exec_and_matrix_and_full_pngs(self):
        # Model an unavailable style without silently substituting Fusion.
        families = ["Tahoma"]
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            with patch.object(whole.QStyleFactory, "keys",
                              return_value=["Fusion"]), patch.object(
                                  whole.QFontDatabase, "families",
                                  return_value=families):
                whole.run(self.cfg, out, "test-no-windows11")
            with (out/"measurements.csv").open(encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(tuple(reader.fieldnames), whole.FIELDS)
                rows = list(reader)
            self.assertEqual(len(rows), 60)
            missing = [r for r in rows if r["style_requested"]=="windows11"]
            self.assertEqual(len(missing), 30)
            self.assertTrue(all(r["execution"]=="NOT_EXECUTED" and
                                r["measurement"]=="NOT_MEASURED" and
                                r["assessment"]=="INCONCLUSIVE"
                                for r in missing))
            actual = [r for r in rows if r["style_requested"]=="Fusion"]
            self.assertEqual(len(actual), 30)
            self.assertTrue(all(r["execution"]=="EXECUTED" for r in actual))
            self.assertTrue(all((out/r["filename"]).is_file() for r in actual))
            self.assertEqual(len(list(out.glob("contact_sheet_*.png"))), 3)
            self.assertEqual(len(list(out.glob("*_indicator_unchecked.png"))), 3)
            self.assertEqual(len(list(out.glob("*_indicator_checked.png"))), 3)
            meta = json.loads((out/"environment.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["installed_tested_fonts"], ["Tahoma"])
            self.assertTrue(meta["negative_controls"]["indicator_detected_as_inadequate"])
            self.assertFalse(meta["actual_os_display_scale_verified"])
            self.assertTrue((out/"summary.md").exists())


if __name__ == "__main__":
    unittest.main()
