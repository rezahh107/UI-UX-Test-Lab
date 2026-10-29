"""Regressions for native Qt state transitions and committed visual provenance.

The Qt-specific tests run on Windows CI after pinned PySide6 installation.
Foundation-only Linux CI retains its standard-library environment and skips Qt.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "adapters" / "qt_style_probe" / "source_probe.py"

try:
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtGui import QColor, QImage, QPixmap
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    from adapters.qt_style_probe import lab_runner as probe
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False


class SourceIntegrityTests(unittest.TestCase):
    def test_migrated_upstream_probe_blob_unchanged(self):
        raw = UPSTREAM.read_bytes()
        git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        self.assertEqual(git_blob, "7b554e784774f2eac02140de17d08f4f3cf46ab8")


@unittest.skipUnless(QT_AVAILABLE, "Windows Qt probe requires installed PySide6")
class QtEvidenceIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Windows CI provides native QPA; offscreen local execution remains
        # synthetic and is not a substitute for a physical desktop session.
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.config, _ = probe.load_config()
        self.host, self.controls = probe.build_host(
            self.config, self.config["variants"][0]
        )
        self.host.show()
        QTest.qWait(70)

    def tearDown(self):
        self.host.close()
        self.app.processEvents()

    def test_ignored_space_cannot_pass_uncheck(self):
        approval = self.controls["approval"]
        # A previously untested default-unchecked end state used to PASS
        # even when both Space events were ignored.
        with patch.object(probe.QTest, "keyClick", return_value=None):
            _full, _target, _widget, method, semantic, _focus = probe.capture_state(
                self.host, self.controls, "unchecked"
            )
        self.assertTrue(approval.isChecked(), "Precondition must be genuinely checked")
        self.assertFalse(semantic, "Ignored Space must fail the checked-to-unchecked proof")
        self.assertEqual(probe.assessed_result(semantic, None), "FAIL")
        self.assertIn("Space once", method)

    def test_valid_one_space_unchecks(self):
        _full, _target, _widget, method, semantic, _focus = probe.capture_state(
            self.host, self.controls, "unchecked"
        )
        self.assertTrue(semantic, "A verified checked-to-unchecked transition must pass")
        self.assertFalse(self.controls["approval"].isChecked())
        self.assertEqual(probe.assessed_result(semantic, None), "PASS")
        self.assertIn("Space once", method)

    def test_existing_checked_transition_and_negative_control(self):
        _full, _target, _widget, _method, semantic, _focus = probe.capture_state(
            self.host, self.controls, "checked"
        )
        self.assertTrue(semantic)
        self.assertTrue(self.controls["approval"].isChecked())
        negative = probe.negative_control(self.config, self.app)
        self.assertTrue(negative["detected"])
        self.assertLess(negative["palette_contrast"], 4.5)

    @staticmethod
    def color_pixmap(width, height, color):
        result = QPixmap(width, height)
        result.fill(QColor(color))
        return result

    class FakeHost:
        def __init__(self, frame):
            self.frame = frame
        def grab(self):
            return self.frame.copy()

    class FakeWidget:
        def __init__(self, frame):
            self.frame = frame
            self.fallback_attempted = False
        def setAttribute(self, attribute, enabled):
            assert attribute == Qt.WidgetAttribute.WA_UnderMouse
            self.fallback_attempted = enabled
        def grab(self):
            return self.frame.copy()
        def mapTo(self, _host, _pos):
            return QPoint(18, 12)

    def exercise_hover(self, fallback_color):
        red = self.color_pixmap(120, 90, "#aa2233")
        idle_button = self.color_pixmap(40, 40, "#aa2233")
        fallback_button = self.color_pixmap(40, 40, fallback_color)
        host = self.FakeHost(red)
        widget = self.FakeWidget(fallback_button)
        shots = {state: red.copy() for state in probe.STATES}
        target, rendered, method = probe.record_state_frame(
            host, widget, "hover", red.copy(), idle_button.copy(),
            {"button": idle_button}, "QTest.mouseMove simulated",
            shots,
        )
        return shots, target, rendered, method, widget

    def assert_hover_sheet_color(self, shots, expected):
        # The hover tile is column 1 / row 0. Sample its actual saved PNG,
        # not merely the in-memory target or a metadata label.
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "contact_sheet_test.png"
            probe.make_sheet(shots, "synthetic-check", path)
            image = QImage(str(path))
            self.assertFalse(image.isNull())
            # Full frame 120x90 scales to 424x282; the accepted widget
            # spans logical [18,58)x[12,52). Sample its interior at (30,30).
            x = 440 + 8 + round(424 * 30 / 120)
            y = 48 + 26 + round(282 * 30 / 90)
            self.assertEqual(image.pixelColor(x, y).name(), expected)

    def test_hover_accepted_fallback_is_the_saved_contact_sheet_frame(self):
        shots, target, rendered, method, widget = self.exercise_hover("#22cc55")
        self.assertTrue(widget.fallback_attempted)
        self.assertTrue(rendered)
        self.assertEqual(probe.assessed_result(True, rendered), "PASS")
        self.assertIn("fallback accepted", method)
        self.assertIn("composed accepted widget.grab()", method)
        self.assertEqual(target.toImage().pixelColor(20, 20).name(), "#22cc55")
        self.assertEqual(shots["hover"].toImage().pixelColor(30, 30).name(), "#22cc55")
        self.assert_hover_sheet_color(shots, "#22cc55")

    def test_ineffective_hover_remains_inconclusive_and_unaltered(self):
        shots, target, rendered, method, widget = self.exercise_hover("#aa2233")
        self.assertTrue(widget.fallback_attempted)
        self.assertFalse(rendered)
        self.assertIn("fallback ineffective", method)
        self.assertEqual(probe.assessed_result(True, rendered), "INCONCLUSIVE")
        self.assertEqual(shots["hover"].toImage().pixelColor(30, 30).name(), "#aa2233")
        self.assert_hover_sheet_color(shots, "#aa2233")


if __name__ == "__main__":
    unittest.main()
