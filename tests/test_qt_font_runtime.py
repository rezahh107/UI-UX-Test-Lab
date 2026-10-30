"""Bundled v33.003 asset integrity and live Qt font substitution controls."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets/fonts/vazirmatn/v33.003"
HASHES = {
    "Vazirmatn-Regular.ttf": "b69fd4c680b8f3f225feabcc655a2c585d97627b8f5f5c0f9985e894069f3a56",
    "Vazirmatn-SemiBold.ttf": "3f239d8364c14ee32c46b6839fa197c28958358b82a9673d2c6acc8506d78bc5",
}
try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QFontInfo, QFontMetrics
    from PySide6.QtWidgets import QApplication, QLabel, QCheckBox, QWidget, QVBoxLayout
    from adapters.qt_style_probe import font_runtime
    from adapters.qt_style_probe import whole_form
    QT = True
except ImportError:
    QT = False


class FontAssets(unittest.TestCase):
    def test_original_pinned_ttf_hashes_and_license(self):
        self.assertEqual(sorted(p.name for p in FONTS.iterdir()), sorted(["OFL.txt", *HASHES]))
        for file, expected in HASHES.items():
            with self.subTest(file=file):
                self.assertEqual(hashlib.sha256((FONTS / file).read_bytes()).hexdigest(), expected)
        self.assertIn("SIL OPEN FONT LICENSE Version 1.1", (FONTS / "OFL.txt").read_text())

    def test_one_canonical_default(self):
        config = json.loads((ROOT / "adapters/qt_style_probe/target.json").read_text())
        self.assertEqual(config["default_font_family"], "Vazirmatn")
        self.assertNotIn("requested_font_families", config)


@unittest.skipUnless(QT, "PySide6 GUI testing runs in the existing Windows workflow")
class FontQtControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_registers_verified_family_and_required_weights(self):
        meta = font_runtime.initialize_font(self.app)
        self.assertEqual(meta["family"], "Vazirmatn")
        self.assertEqual(meta["qt_application_family"], "Vazirmatn")
        self.assertEqual(meta["sha256"], HASHES)
        self.assertGreater(meta["semibold_weight"], meta["regular_weight"])
        font_runtime.assert_widget_font(self.app)

    def test_not_dependent_on_current_directory(self):
        here = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                self.assertEqual(font_runtime.initialize_font(self.app)["directory"], str(FONTS))
            finally:
                os.chdir(here)

    def test_missing_and_corrupted_file_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            with self.assertRaisesRegex(font_runtime.FontLoadError, "absent/unreadable"):
                font_runtime.initialize_font(self.app, directory=directory)
            for name in HASHES:
                (directory / name).write_bytes((FONTS / name).read_bytes())
            (directory / "Vazirmatn-Regular.ttf").write_bytes(b"not a font")
            with self.assertRaisesRegex(font_runtime.FontLoadError, "integrity failure"):
                font_runtime.initialize_font(self.app, directory=directory)

    def test_failed_registration_cannot_pass(self):
        with patch.object(font_runtime, "QFontDatabase") as db:
            db.families.return_value = []
            db.addApplicationFont.return_value = -1
            with self.assertRaisesRegex(font_runtime.FontLoadError, "registration failed"):
                font_runtime.initialize_font(self.app)

    def test_wrong_registered_family_cannot_pass(self):
        with patch.object(font_runtime, "QFontDatabase") as db:
            db.families.return_value = []
            db.addApplicationFont.return_value = 1
            db.applicationFontFamilies.return_value = ["Tahoma"]
            with self.assertRaisesRegex(font_runtime.FontLoadError, "Unexpected family"):
                font_runtime.initialize_font(self.app)

    def test_silent_fallback_rejected(self):
        label = QLabel("آزمایش")
        label.setFont(QFont("Arial", 11))
        with self.assertRaisesRegex(font_runtime.FontLoadError, "substitution"):
            font_runtime.assert_widget_font(label)

    def test_persian_arabic_zwnj_mixed_rtl_and_widget_geometry(self):
        font_runtime.initialize_font(self.app)
        regular = QFont(font_runtime.FAMILY, 11)
        demi = QFont(regular)
        demi.setWeight(QFont.Weight.DemiBold)
        self.assertEqual(QFontInfo(regular).family(), font_runtime.FAMILY)
        self.assertEqual(QFontInfo(demi).family(), font_runtime.FAMILY)
        self.assertGreater(QFontInfo(demi).weight(), QFontInfo(regular).weight())
        host = QWidget()
        host.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(host)
        for text in ("سلام دنیا و نیم‌فاصله", "العربية والفارسیة",
                     "Qt 6 — بانک ۱۲۳ — IRR 12,345.67", whole_form.PRODUCT_TEXT):
            label, checkbox = QLabel(text), QCheckBox(text)
            for widget in (label, checkbox):
                widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                widget.setFixedSize(720, 52)
                layout.addWidget(widget)
                font_runtime.assert_widget_font(widget)
            metrics = QFontMetrics(label.font())
            self.assertGreater(metrics.horizontalAdvance(text), 0)
            self.assertLess(metrics.horizontalAdvance(text), label.width(), text)
            self.assertEqual(label.font().family(), checkbox.font().family())
            self.assertEqual(label.layoutDirection(), checkbox.layoutDirection())
        host.show()
        self.app.processEvents()
        self.assertFalse(host.grab().isNull())
        host.close()
        # Pixel capture and QFontInfo are not proof of per-glyph fallback or readability.


if __name__ == "__main__":
    unittest.main()
