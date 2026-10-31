"""Repository-owned, fail-closed Qt font bootstrap for normal Lab experiments.

Call after QApplication construction and before any widgets/captures. Explicit
font comparisons may override app.font() *after* canonical registration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase, QFontInfo
from PySide6.QtWidgets import QApplication

FAMILY = "Vazirmatn"
VERSION = "v33.003"
FONT_FILES = {
    "Vazirmatn-Regular.ttf": "b69fd4c680b8f3f225feabcc655a2c585d97627b8f5f5c0f9985e894069f3a56",
    "Vazirmatn-SemiBold.ttf": "3f239d8364c14ee32c46b6839fa197c28958358b82a9673d2c6acc8506d78bc5",
}
FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts" / "vazirmatn" / VERSION


class FontLoadError(RuntimeError):
    """Font evidence is invalid; do not continue with a system substitution."""


def assert_widget_font(widget):
    """Reject an unexpected effective Qt family in canonical (not comparison) UI."""
    requested = widget.font().family()
    effective = QFontInfo(widget.font()).family()
    if requested != FAMILY or effective != FAMILY:
        raise FontLoadError(
            f"Silent font substitution: requested={requested!r}, effective={effective!r}; "
            f"expected bundled {FAMILY} {VERSION}"
        )


def initialize_font(app: QApplication, point_size: int = 11, *,
                    directory: Path | None = None) -> dict:
    if QApplication.instance() is not app:
        raise FontLoadError("A live QApplication is required before font registration")
    path = FONT_DIR if directory is None else Path(directory)
    present_before = FAMILY in QFontDatabase.families()
    # Validate the *whole* asset set before registering any font.
    for name, expected in FONT_FILES.items():
        asset = path / name
        try:
            actual = hashlib.sha256(asset.read_bytes()).hexdigest()
        except OSError as exc:
            raise FontLoadError(f"Bundled font absent/unreadable: {asset}: {exc}") from exc
        if actual != expected:
            raise FontLoadError(
                f"Bundled font integrity failure: {asset.name}; expected {expected}; got {actual}"
            )
    for name in FONT_FILES:
        font_id = QFontDatabase.addApplicationFont(str(path / name))
        if font_id < 0:
            raise FontLoadError(f"Qt font registration failed: {path / name}")
        families = QFontDatabase.applicationFontFamilies(font_id)
        if FAMILY not in families:
            raise FontLoadError(
                f"Unexpected family from {name}: {families!r}; required {FAMILY}"
            )

    styles = QFontDatabase.styles(FAMILY)
    regular = next((s for s in styles if s.casefold() == "regular"), None)
    semibold = next(
        (s for s in styles if s.casefold().replace(" ", "") in ("semibold", "demibold")),
        None,
    )
    if not regular or not semibold:
        raise FontLoadError(f"Required Regular/SemiBold Qt styles unavailable: {styles!r}")
    normal_weight = int(QFontDatabase.weight(FAMILY, regular))
    strong_weight = int(QFontDatabase.weight(FAMILY, semibold))
    if normal_weight != int(QFont.Weight.Normal) or strong_weight < int(QFont.Weight.DemiBold):
        raise FontLoadError(
            f"Unexpected Qt weight registration: Regular={normal_weight}, SemiBold={strong_weight}"
        )
    app.setFont(QFont(FAMILY, point_size))
    assert_widget_font(app)
    return {
        "family": FAMILY, "version": VERSION, "source": 
            "https://github.com/rastikerdar/vazirmatn/releases/tag/v33.003",
        "directory": str(path), "sha256": dict(FONT_FILES),
        "qt_styles": list(styles), "regular_weight": normal_weight,
        "semibold_weight": strong_weight,
        "family_present_before_registration": present_before,
        "qt_application_family": QFontInfo(app.font()).family(),
        "per_glyph_fallback_proven": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Standalone bundled font preflight")
    parser.add_argument("--require-system-absent", action="store_true",
                        help="CI negative precondition: OS must not provide Vazirmatn")
    args = parser.parse_args()
    app = QApplication([])
    before = FAMILY in QFontDatabase.families()
    if args.require_system_absent and before:
        raise FontLoadError("CI cannot prove independence: Vazirmatn already exists in OS Qt database")
    info = initialize_font(app)
    assert_widget_font(app)
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
