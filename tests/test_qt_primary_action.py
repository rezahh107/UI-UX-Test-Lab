"""Synthetic primary-action comparison contract and real Qt widget regressions."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from PySide6.QtCore import Qt, QPoint
    from PySide6.QtGui import QColor, QPixmap
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QStyleFactory
    from adapters.qt_style_probe import lab_runner as lab
    from adapters.qt_style_probe import primary_action as primary
    QT = True
except ImportError:
    QT = False


@unittest.skipUnless(QT, "Needs PySide6-Essentials; exercised on Windows CI")
class PrimaryActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.cfg, _ = lab.load_config()

    def setUp(self):
        self.app.setStyle(QStyleFactory.create("Fusion"))
        lab.apply_palette(self.app, self.cfg, False)
        self.host, self.controls = lab.build_host(self.cfg, self.cfg["variants"][0])
        self.host.show()
        QTest.qWait(65)
        self.button = self.controls["button"]
        self.button.setFixedSize(self.button.size())

    def tearDown(self):
        self.host.close()
        self.app.processEvents()

    def test_three_methods_two_themes_five_states(self):
        self.assertEqual(primary.METHODS, ("font_weight", "palette", "button_qss"))
        self.assertEqual(primary.THEMES, ("light", "dark"))
        self.assertEqual(primary.STATES, ("normal", "focus", "hover", "pressed", "disabled"))

    def test_tokens_and_actual_negative_control(self):
        for name, t in primary.TOKENS.items():
            for foreground, background in (
                (t["foreground"], t["background"]),
                (t["foreground"], t["hover"]),
                (t["foreground"], t["pressed"]),
                (t["disabled_foreground"], t["disabled_background"]),
            ):
                self.assertGreaterEqual(
                    primary.contrast_pair(foreground, background),
                    primary.MIN_CONTRAST,
                    f"{name}: {foreground} / {background}",
                )

    def test_qss_only_targets_the_primary_button(self):
        qss = primary.primary_button_qss(primary.TOKENS["light"])
        for selector in qss.split("}"):
            if selector.strip():
                self.assertTrue(selector.strip().startswith("QPushButton#nativePrimary"),
                                selector)
        original = primary.geometry(self.host, self.button)
        primary.emphasize(self.button, "button_qss", "light")
        QTest.qWait(35)
        self.assertEqual(self.button.text(), self.cfg["fields"]["convert"])
        self.assertEqual(primary.geometry(self.host, self.button), original)
        self.assertFalse(self.controls["card"].styleSheet())
        self.assertFalse(self.controls["approval"].styleSheet())
        self.assertFalse(self.controls["combo"].styleSheet())
        self.assertFalse(self.controls["amount"].styleSheet())

    def test_each_method_preserves_geometry_label_and_font_family(self):
        for method in primary.METHODS:
            with self.subTest(method=method):
                # Build a fresh host per method to avoid leaked palette or QSS.
                host, controls = lab.build_host(self.cfg, self.cfg["variants"][0])
                host.show()
                QTest.qWait(35)
                b = controls["button"]
                b.setFixedSize(b.size())
                geometry = primary.geometry(host, b)
                font_family = b.font().family()
                font_points = b.font().pointSize()
                primary.emphasize(b, method, "light")
                QTest.qWait(35)
                self.assertEqual(primary.geometry(host, b), geometry)
                self.assertEqual(b.text(), self.cfg["fields"]["convert"])
                self.assertEqual(b.font().family(), font_family)
                self.assertEqual(b.font().pointSize(), font_points)
                self.assertEqual(bool(b.styleSheet()), method == "button_qss")
                host.close()

    def test_keyboard_activation_and_tab_focus_for_every_method(self):
        for method in primary.METHODS:
            with self.subTest(method=method):
                host, controls = lab.build_host(self.cfg, self.cfg["variants"][0])
                host.show()
                QTest.qWait(40)
                button = controls["button"]
                button.setFixedSize(button.size())
                primary.emphasize(button, method, "light")
                clicks = []
                button.clicked.connect(lambda checked=False: clicks.append(True))
                button.setFocus()
                QTest.keyClick(button, Qt.Key.Key_Space)
                self.assertEqual(len(clicks), 1)
                controls["approval"].setFocus(Qt.FocusReason.TabFocusReason)
                QTest.keyClick(controls["approval"], Qt.Key.Key_Tab)
                self.assertTrue(button.hasFocus())
                host.close()

    def test_ignored_keyboard_activation_is_detected(self):
        fired = []
        self.button.clicked.connect(lambda checked=False: fired.append(True))
        with patch.object(primary.QTest, "keyClick", return_value=None):
            primary.QTest.keyClick(self.button, Qt.Key.Key_Space)
        self.assertFalse(fired, "Ignored Space cannot count as a keyboard activation")

    def test_focus_press_disabled_capture_preserves_behavior(self):
        primary.emphasize(self.button, "button_qss", "dark")
        idle = self.button.grab()
        shots = {}
        for state in ("focus", "pressed", "disabled"):
            with self.subTest(state=state):
                capture, semantics, rendered, via_tab, method = primary.capture(
                    self.host, self.controls, state, idle, shots
                )
                self.assertFalse(capture.isNull())
                self.assertTrue(semantics, method)
                if state == "focus":
                    self.assertTrue(via_tab)
                if state == "disabled":
                    self.assertFalse(self.button.isEnabled())

    def test_low_contrast_button_fixture_is_detected_and_captured(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            result = primary.negative_button_control(Path(folder))
            self.assertTrue(result["detected"])
            self.assertLess(result["ratio"], primary.MIN_CONTRAST)
            self.assertTrue((Path(folder) / "negative_button.png").is_file())


    @staticmethod
    def colored_pixmap(color):
        image = QPixmap(160, 48)
        image.fill(QColor(color))
        return image

    def test_normal_unchanged_image_cannot_pass_even_with_good_semantics(self):
        native = self.colored_pixmap("#223344")
        emphasized = native.copy()
        rendered = primary.visual_evidence(
            "normal", emphasized, native, None, emphasized, None
        )
        self.assertFalse(rendered)
        self.assertEqual(primary.assess_state(True, True, rendered), "INCONCLUSIVE")
        self.assertEqual(primary.assess_state(True, True, None), "INCONCLUSIVE")

    def test_normal_measured_emphasis_change_passes(self):
        native = self.colored_pixmap("#223344")
        emphasized = self.colored_pixmap("#4a7eb0")
        rendered = primary.visual_evidence(
            "normal", emphasized, native, None, emphasized, None
        )
        self.assertTrue(rendered)
        self.assertEqual(primary.assess_state(True, True, rendered), "PASS")

    def test_disabled_matching_native_disabled_cannot_pass(self):
        native = self.colored_pixmap("#111111")
        native_disabled = self.colored_pixmap("#aaaaaa")
        emphasized_normal = self.colored_pixmap("#2288ee")
        unchanged = native_disabled.copy()
        rendered = primary.visual_evidence(
            "disabled", unchanged, native, native_disabled,
            emphasized_normal, None
        )
        self.assertFalse(rendered)
        self.assertEqual(primary.assess_state(True, True, rendered), "INCONCLUSIVE")

    def test_disabled_matching_enabled_emphasis_cannot_pass(self):
        native = self.colored_pixmap("#111111")
        native_disabled = self.colored_pixmap("#aaaaaa")
        emphasized_normal = self.colored_pixmap("#2288ee")
        unchanged = emphasized_normal.copy()
        rendered = primary.visual_evidence(
            "disabled", unchanged, native, native_disabled,
            emphasized_normal, None
        )
        self.assertFalse(rendered)
        self.assertEqual(primary.assess_state(True, True, rendered), "INCONCLUSIVE")

    def test_disabled_distinct_from_both_references_passes(self):
        native = self.colored_pixmap("#111111")
        native_disabled = self.colored_pixmap("#aaaaaa")
        emphasized_normal = self.colored_pixmap("#2288ee")
        disabled = self.colored_pixmap("#596879")
        rendered = primary.visual_evidence(
            "disabled", disabled, native, native_disabled,
            emphasized_normal, None
        )
        self.assertTrue(rendered)
        self.assertEqual(primary.assess_state(True, True, rendered), "PASS")

    def test_existing_interactive_inconclusive_and_failure_precedence(self):
        for state in ("focus", "hover", "pressed"):
            with self.subTest(state=state):
                pixel = self.colored_pixmap("#334455")
                for observed, expected in ((False, "INCONCLUSIVE"),
                                           (None, "INCONCLUSIVE"),
                                           (True, "PASS")):
                    rendered = primary.visual_evidence(
                        state, pixel, pixel, pixel, pixel, observed
                    )
                    self.assertIs(rendered, observed)
                    self.assertEqual(primary.assess_state(True, True, rendered),
                                     expected)
        self.assertEqual(primary.assess_state(False, True, True), "FAIL")
        self.assertEqual(primary.assess_state(True, False, True), "FAIL")

    def test_native_disabled_reference_is_followed_by_enabled_space_ready_state(self):
        snapshots = {}
        primary.capture(self.host, self.controls, "disabled", None, snapshots)
        self.assertFalse(self.button.isEnabled())
        normal, semantic, _, _, _ = primary.capture(
            self.host, self.controls, "normal", None, snapshots
        )
        self.assertFalse(normal.isNull())
        self.assertTrue(semantic)
        self.assertTrue(self.button.isEnabled())
        fired = []
        self.button.clicked.connect(lambda checked=False: fired.append(True))
        self.button.setFocus(Qt.FocusReason.TabFocusReason)
        QTest.keyClick(self.button, Qt.Key.Key_Space)
        self.assertEqual(fired, [True],
                         "Native reference capture must leave the candidate input-ready")

    def test_missing_windows11_is_not_executed_and_csv_contract_preserved(self):
        # Suppress the font-weight treatment, so the actual Qt capture is a
        # no-op. An end-to-end normal row MUST become inconclusive.
        original_emphasize = primary.emphasize

        def remove_weight_treatment(button, method, theme):
            if method != "font_weight":
                return original_emphasize(button, method, theme)

        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            with patch.object(primary.QStyleFactory, "keys",
                              return_value=["Fusion"]), patch.object(
                                  primary, "emphasize",
                                  side_effect=remove_weight_treatment):
                primary.run(self.cfg, out, "regression-no-windows11")
            with (out / "measurements.csv").open(
                    encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                self.assertEqual(tuple(reader.fieldnames), primary.FIELDS)
                rows = list(reader)
            self.assertEqual(len(rows), 60)
            unavailable = [r for r in rows if r["style_requested"] == "windows11"]
            self.assertEqual(len(unavailable), 30)
            self.assertTrue(all(r["execution"] == "NOT_EXECUTED"
                                and r["measurement"] == "NOT_MEASURED"
                                and r["assessment"] == "INCONCLUSIVE"
                                for r in unavailable))
            actual = [r for r in rows if r["style_requested"] == "Fusion"]
            self.assertEqual(len(actual), 30)
            self.assertTrue(all(r["execution"] == "EXECUTED"
                                and r["measurement"] == "MEASURED"
                                for r in actual))
            no_op_normals = [r for r in actual if r["method"] == "font_weight"
                             and r["state"] == "normal"]
            self.assertEqual(len(no_op_normals), 2)
            self.assertTrue(all(r["rendered"] == "False"
                                and r["assessment"] == "INCONCLUSIVE"
                                and r["normal_emphasis_visual_change"] == "False"
                                for r in no_op_normals))
            self.assertEqual(len(list(out.glob("contact_sheet_*.png"))), 6)
            self.assertTrue((out / "negative_button.png").is_file())
            self.assertTrue((out / "summary.md").is_file())
            env = json.loads((out / "environment.json").read_text(encoding="utf-8"))
            self.assertTrue(env["negative_control"]["detected"])
            self.assertEqual(env["themes"], list(primary.THEMES))
            self.assertEqual(env["methods"], list(primary.METHODS))
            self.assertEqual(env["states"], list(primary.STATES))
            self.assertEqual(len(env["baselines"]), 6)
            for baseline in env["baselines"].values():
                self.assertIn("disabled_vs_native_changed", baseline)
                self.assertIn("disabled_vs_enabled_changed", baseline)


if __name__ == "__main__":
    unittest.main()
