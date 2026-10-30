"""Synthetic primary-action comparison contract and real Qt widget regressions."""
import unittest
from unittest.mock import patch

try:
    from PySide6.QtCore import Qt, QPoint
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


if __name__ == "__main__":
    unittest.main()
