"""Read-only product-control equivalence qualification, using synthetic data only.

Qt equivalent of Bank2Odoo d06b35f bank2odoo/ui/window.py:
  _ApprovalIndicatorStyle.pixelMetric lines 100-108
  _FullRowCheckBox.hitButton lines 111-115
  approval setup lines 297-305.
Never imports or runs Bank2Odoo and never implies physical Windows 11.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import QPoint, Qt, QCoreApplication, qVersion
from PySide6.QtGui import QFont, QFontDatabase, QFontInfo, QPalette, QColor, QImage, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication, QProxyStyle, QStyle, QStyleFactory, QStyleOptionButton,
)

from . import lab_runner as lab
from . import whole_form as whole
from . import primary_action as primary
from . import font_runtime

PRODUCT_COMMIT = "d06b35f41ac46936716b186fb1dfac33da983eb9"
STYLES = ("Fusion", "windows11")
FONTS = (font_runtime.FAMILY,)  # canonical; --compare-tahoma is non-default
TREATMENTS = ("native", "unchecked_border")
STATES = ("unchecked", "focus_tab", "checked_space", "unchecked_space",
          "checked_row", "unchecked_row", "disabled")
MIN_INDICATOR = 22
CSV_FIELDS = (
    "candidate", "requested_style", "effective_style", "requested_font",
    "resolved_font", "treatment", "state", "execution", "assessment",
    "proxy_width", "proxy_height", "effective_width", "effective_height",
    "indicator_rect_width", "indicator_rect_height", "metric_preserved",
    "unchecked_pixel_max_contrast", "unchecked_pixel_fraction",
    "unchecked_visible", "checked_distinct", "semantic_ok",
    "focus_visual_change", "role_text_contrast", "role_is_not_glyph_contrast",
    "raw_png", "reason",
)


class ProductEquivalentApprovalStyle(QProxyStyle):
    """Exact product pixelMetric behavior, not an import of product code."""

    def pixelMetric(self, metric, option=None, widget=None):
        native = super().pixelMetric(metric, option, widget)
        if metric in (QStyle.PixelMetric.PM_IndicatorWidth,
                      QStyle.PixelMetric.PM_IndicatorHeight):
            return max(native, MIN_INDICATOR)
        return native


def make_equivalent(cfg, style_name, font, treatment):
    app = QApplication.instance()
    style = QStyleFactory.create(style_name)
    if style is None:
        raise RuntimeError("Missing style " + style_name)
    app.setStyle(style)
    lab.apply_palette(app, cfg, True)
    app.setFont(QFont(font, cfg["font_point_size"]))
    host, controls = lab.build_host(cfg, cfg["variants"][0])
    if font == font_runtime.FAMILY:
        font_runtime.assert_widget_font(host)
        font_runtime.assert_widget_font(controls["approval"])
    cb = controls["approval"]
    # Use the same public product UI string and setup, not real financial data.
    cb.setText(whole.PRODUCT_TEXT)
    cb.setMinimumHeight(52)
    cb.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    cb.setCursor(Qt.CursorShape.PointingHandCursor)
    cb.setAccessibleName("تأیید صریح اطلاعات مالی")
    proxy = ProductEquivalentApprovalStyle(cb.style().objectName())
    cb.setStyle(proxy)
    host._equivalent_style_guard = proxy  # mirror product-owned proxy lifetime
    whole.apply_treatment(cb, treatment, cfg)
    primary.emphasize(controls["button"], "button_qss", "dark")
    host.show()
    QCoreApplication.processEvents()
    QTest.qWait(55)
    return host, controls, proxy


def effective_geometry(cb, proxy):
    opt = QStyleOptionButton()
    opt.initFrom(cb)
    met = {}
    for label, kind in (
        ("width", QStyle.PixelMetric.PM_IndicatorWidth),
        ("height", QStyle.PixelMetric.PM_IndicatorHeight),
    ):
        met["proxy_" + label] = int(proxy.pixelMetric(kind, opt, cb))
        met["effective_" + label] = int(cb.style().pixelMetric(kind, opt, cb))
    rect = whole.indicator_geometry(cb)
    met["indicator_rect_width"] = int(rect.width())
    met["indicator_rect_height"] = int(rect.height())
    met["metric_preserved"] = (
        met["proxy_width"] >= MIN_INDICATOR
        and met["proxy_height"] >= MIN_INDICATOR
        and met["effective_width"] >= MIN_INDICATOR
        and met["effective_height"] >= MIN_INDICATOR
        and rect.width() >= MIN_INDICATOR
        and rect.height() >= MIN_INDICATOR
    )
    return met


def checked_difference(cb):
    cb.setEnabled(True)
    cb.setChecked(False)
    cb.setFocus(Qt.FocusReason.OtherFocusReason)
    QCoreApplication.processEvents()
    unchecked = cb.grab()
    cb.setChecked(True)
    QCoreApplication.processEvents()
    checked = cb.grab()
    rect = whole.indicator_geometry(cb)
    dpr = unchecked.devicePixelRatio()
    physical = lab.QRect(round(rect.x() * dpr), round(rect.y() * dpr),
                         max(1, round(rect.width() * dpr)),
                         max(1, round(rect.height() * dpr)))
    return lab.metrics.difference(
        unchecked.copy(physical), checked.copy(physical)
    )["changed"], unchecked, checked


def capture_case(host, controls, state, out, candidate):
    cb = controls["approval"]
    combo = controls["combo"]
    cb.setEnabled(True)
    cb.setChecked(False)
    host.activateWindow()
    QTest.mouseMove(host, QPoint(5, 5))
    host.setFocus(Qt.FocusReason.OtherFocusReason)
    QCoreApplication.processEvents()
    QTest.qWait(35)
    neutral = cb.grab()
    semantic = True
    focus_visible = None
    if state == "focus_tab":
        combo.setFocus(Qt.FocusReason.TabFocusReason)
        QTest.keyClick(combo, Qt.Key.Key_Tab)
        QCoreApplication.processEvents()
        semantic = cb.hasFocus()
        focus_visible = lab.metrics.difference(neutral, cb.grab())["changed"]
    elif state == "checked_space":
        cb.setFocus()
        before = not cb.isChecked()
        QTest.keyClick(cb, Qt.Key.Key_Space)
        semantic = before and cb.isChecked()
    elif state == "unchecked_space":
        cb.setChecked(True)
        before = cb.isChecked()
        cb.setFocus()
        QTest.keyClick(cb, Qt.Key.Key_Space)
        semantic = before and not cb.isChecked()
    elif state == "checked_row":
        # Click far from label AND far from indicator. Product's hitButton
        # intentionally treats the whole row as interactive.
        QTest.mouseClick(cb, Qt.MouseButton.LeftButton,
                         pos=QPoint(5, cb.height() // 2))
        semantic = cb.isChecked()
    elif state == "unchecked_row":
        cb.setChecked(True)
        QTest.mouseClick(cb, Qt.MouseButton.LeftButton,
                         pos=QPoint(5, cb.height() // 2))
        semantic = not cb.isChecked()
    elif state == "disabled":
        cb.setEnabled(False)
        semantic = not cb.isEnabled()
    QCoreApplication.processEvents()
    QTest.qWait(40)
    full = host.grab()
    name = f"{candidate}_{state}.png"
    whole.full_png(full, out / name)
    return {"semantic": bool(semantic), "shot": full,
            "focus_visible": focus_visible, "raw_png": name}


def save_preview(screenshots, path, title):
    # Reduced reference is generated only after every source frame is saved.
    w, h = 430, 310
    preview = QImage(w * 2, 38 + h * 4, QImage.Format.Format_RGB32)
    preview.fill(QColor("#F6F7F9"))
    painter = QPainter(preview)
    painter.setPen(QColor("#152030"))
    painter.setFont(QFont(font_runtime.FAMILY, 10))
    painter.drawText(8, 25, title + " — reduced, not source pixels")
    for index, state in enumerate(STATES):
        x, y = index % 2 * w, 38 + (index // 2) * h
        painter.drawText(x + 8, y + 17, state)
        painter.drawPixmap(x + 5, y + 24, w - 10, h - 29, screenshots[state])
    painter.end()
    if not preview.save(str(path), "PNG"):
        raise RuntimeError("Unable to save reduced preview: " + str(path))


def run(cfg, out, scale_tag, *, compare_tahoma=False):
    out.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    available = {x.casefold(): x for x in QStyleFactory.keys()}
    font_evidence = font_runtime.initialize_font(app, cfg["font_point_size"])
    installed = {x.casefold(): x for x in QFontDatabase.families()}
    requested_fonts = FONTS + (("Tahoma",) if compare_tahoma else ())
    env = {
        "lab_head": os.getenv("GITHUB_SHA"), "run_id": os.getenv("GITHUB_RUN_ID"),
        "product_ref": PRODUCT_COMMIT, "product_class_imported": False,
        "equivalent_contract": [
            "QProxyStyle.pixelMetric returns max(native,22) for indicator width/height",
            "FullRowCheckBox.hitButton uses rect.contains(pos)",
            "QCheckBox minimum height 52, StrongFocus, RTL and product UI wording",
        ],
        "qt": qVersion(), "pyside": PYSIDE_VERSION, "platform": platform.platform(),
        "qpa": app.platformName(), "scale_tag": scale_tag,
        "qt_scale_factor": os.environ.get("QT_SCALE_FACTOR"),
        "requested_styles": list(STYLES), "available_styles": list(available.values()),
        "requested_fonts": list(requested_fonts), "installed_fonts": list(installed.values()),
        "canonical_font": font_evidence,
        "comparison_mode": "non-default Tahoma comparison" if compare_tahoma else "canonical",
        "physical_windows11_environment": False,
        "os_display_scale_100_125_150": {
            "100": "NOT_EXECUTED", "125": "NOT_EXECUTED",
            "150": "NOT_EXECUTED",
        },
        "per_glyph_fallback_proven": False, "product_ui_executed": False,
        "contrast_basis": "actual Qt indicator pixels vs sampled adjacent surface; QPalette text roles are not glyph pixels",
        "full_resolution_before_previews": True,
        "observations": {},
        "limitations": [
            "Windows-2025 CI not an interactive physical Windows11 desktop",
            "QT_SCALE_FACTOR is synthetic, not Windows Display settings",
            "Product equivalent only in checkbox subclass/proxy, not full application",
            "No per-glyph fallback or subjective visual/accessibility acceptance",
        ],
    }
    rows = []
    for font_request in requested_fonts:
        resolved_font = installed.get(font_request.casefold())
        for style_request in STYLES:
            style_key = available.get(style_request.casefold())
            for treatment in TREATMENTS:
                candidate = (style_request.lower() + "_" +
                             font_request.lower() + "_" + treatment)
                if not resolved_font or not style_key:
                    reason = ("FONT_NOT_INSTALLED" if not resolved_font
                              else "STYLE_NOT_AVAILABLE")
                    for state in STATES:
                        rows.append({
                            "candidate": candidate, "requested_style": style_request,
                            "requested_font": font_request, "treatment": treatment,
                            "state": state, "execution": "NOT_EXECUTED",
                            "assessment": "NOT_PROVEN", "reason": reason,
                        })
                    continue
                host, controls, proxy = make_equivalent(
                    cfg, style_key, resolved_font, treatment
                )
                cb = controls["approval"]
                geom = effective_geometry(cb, proxy)
                text_pal = cb.palette()
                role_ratio = whole.contrast_color(
                    text_pal.color(QPalette.ColorRole.WindowText).name(),
                    text_pal.color(QPalette.ColorRole.Window).name(),
                )
                screenshots = {}
                records = {}
                try:
                    for state in STATES:
                        outcome = capture_case(host, controls, state, out, candidate)
                        screenshots[state] = outcome.pop("shot")
                        records[state] = outcome
                    # Capture the unchecked state under neutral conditions.
                    cb.setEnabled(True)
                    cb.setChecked(False)
                    host.setFocus(Qt.FocusReason.OtherFocusReason)
                    QCoreApplication.processEvents()
                    unchecked_photo = cb.grab()
                    unchecked_indicator = whole.indicator_pixels(cb, unchecked_photo)
                    distinct, unchecked, checked = checked_difference(cb)
                    for name, shot in (("unchecked", unchecked), ("checked", checked)):
                        whole.full_png(
                            shot, out / f"{candidate}_checkbox_{name}.png")
                    # A product-equivalent host's native indicator metric
                    # must survive scoped QSS. If not, the candidate FAILs.
                    for state in STATES:
                        outcome = records[state]
                        semantic_ok = bool(outcome["semantic"])
                        missing_focus = (
                            state == "focus_tab" and
                            outcome["focus_visible"] is not True
                        )
                        if not geom["metric_preserved"] or not semantic_ok:
                            assessment = "FAIL"
                        elif (not unchecked_indicator["visible"] or not distinct
                              or missing_focus or role_ratio < 4.5):
                            assessment = "NOT_PROVEN"
                        else:
                            assessment = "PASS"
                        rows.append({
                            "candidate": candidate, "requested_style": style_request,
                            "effective_style": app.style().objectName(),
                            "requested_font": font_request,
                            "resolved_font": QFontInfo(cb.font()).family(),
                            "treatment": treatment, "state": state,
                            "execution": "EXECUTED", "assessment": assessment,
                            "semantic_ok": semantic_ok,
                            "focus_visual_change": outcome["focus_visible"],
                            "role_text_contrast": role_ratio,
                            "role_is_not_glyph_contrast": True,
                            "unchecked_pixel_max_contrast": unchecked_indicator["max"],
                            "unchecked_pixel_fraction": unchecked_indicator["fraction"],
                            "unchecked_visible": unchecked_indicator["visible"],
                            "checked_distinct": distinct,
                            "raw_png": outcome["raw_png"],
                            "reason": ("METRIC_UNDER_22" if not geom["metric_preserved"]
                                       else "INPUT_SEMANTIC_FAILURE" if not semantic_ok
                                       else "INDICATOR_NOT_VISIBLE" if not unchecked_indicator["visible"]
                                       else "CHECKED_UNCHECKED_NOT_DISTINCT" if not distinct
                                       else "FOCUS_NOT_RENDERED" if missing_focus
                                       else "ROLE_CONTRAST_UNDER_4_5" if role_ratio < 4.5
                                       else ""),
                            **geom,
                        })
                    env["observations"][candidate] = {
                        "geometry": geom, "indicator": unchecked_indicator,
                        "checked_distinct": distinct,
                        "role_text_contrast": role_ratio,
                        "proxy_class": type(proxy).__name__,
                        "effective_style_class": type(cb.style()).__name__,
                        "font_resolved": QFontInfo(cb.font()).family(),
                        "focus_visible": records["focus_tab"]["focus_visible"],
                        "semantics": {key: value["semantic"]
                                      for key, value in records.items()},
                    }
                    # Always save original frames before any reduced preview.
                    save_preview(
                        screenshots, out / f"preview_{candidate}.png", candidate
                    )
                finally:
                    host.close()
                    QCoreApplication.processEvents()
    with (out / "measurements.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(
            {field: row.get(field, "") for field in CSV_FIELDS}
            for row in rows
        )
    (out / "environment.json").write_text(
        json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    counts = {state: sum(row["assessment"] == state for row in rows)
              for state in ("PASS", "FAIL", "NOT_PROVEN")}
    text = [
        "# Bank2Odoo approval control equivalence — Qt synthetic diagnostic",
        f"Lab HEAD: {env['lab_head']}; product ref: {PRODUCT_COMMIT}",
        f"QPA: {env['qpa']}; platform: {env['platform']}; scale: {scale_tag}",
        f"Executed: {sum(row['execution']=='EXECUTED' for row in rows)}; "
        f"NOT_EXECUTED: {sum(row['execution']=='NOT_EXECUTED' for row in rows)}",
        f"Assessments: {counts}", "",
        "## Candidate metric, indicator and focus observations",
    ]
    for candidate, ob in env["observations"].items():
        text.append(
            f"- {candidate}: proxy={ob['geometry']['proxy_width']}x"
            f"{ob['geometry']['proxy_height']}, "
            f"effective={ob['geometry']['effective_width']}x"
            f"{ob['geometry']['effective_height']}, "
            f"rect={ob['geometry']['indicator_rect_width']}x"
            f"{ob['geometry']['indicator_rect_height']}, "
            f"metric_preserved={ob['geometry']['metric_preserved']}, "
            f"unchecked_max={ob['indicator']['max']}:1, "
            f"unchecked_visible={ob['indicator']['visible']}, "
            f"checked_distinct={ob['checked_distinct']}, "
            f"focus_painted={ob['focus_visible']}"
        )
    text += [
        "", "## Non-negotiable limits",
        "- Not physical Windows 11. All 100%, 125%, 150% genuine OS scale cases NOT_EXECUTED.",
        "- No real Bank2Odoo runtime or financial data. Product-equivalent checkbox only.",
        "- Qt glyph pixel contrast, accessibility and perceptual readability NOT_PROVEN.",
        "- Product adoption requires a genuine interactive Windows11 acceptance pass.",
    ]
    (out / "summary.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    print("PRODUCT_EQUIVALENT:", counts,
          "executed=", sum(row["execution"] == "EXECUTED" for row in rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scale-tag", required=True)
    parser.add_argument("--compare-tahoma", action="store_true", help="Explicit non-default system-font comparison")
    args = parser.parse_args()
    cfg, _ = lab.load_config()
    run(cfg, args.output, args.scale_tag, compare_tahoma=args.compare_tahoma)


if __name__ == "__main__":
    main()
