"""Synthetic whole-form Fusion/Windows11 dark-palette and Persian checkbox evidence.

Diagnostic Qt QWidget grabs only. No Bank2Odoo import or product data.
Static UI wording was independently verified at Bank2Odoo main d06b35f,
bank2odoo/ui/window.py (self.approved). This is not product execution.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import QPoint, Qt, QCoreApplication, qVersion
from PySide6.QtGui import QColor, QFont, QFontDatabase, QFontInfo, QFontMetrics, QImage, QPainter, QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QLabel, QStyle,
                               QStyleFactory, QStyleOptionButton, QVBoxLayout, QWidget, QPushButton)

from . import lab_runner as lab
from . import primary_action as primary

STYLES = ("windows11", "Fusion")
FONTS = ("Tahoma", "Vazirmatn")
TREATMENTS = ("native", "checkbox_palette", "unchecked_border")
STATES = ("unchecked", "checkbox_focus", "checked_space", "unchecked_space",
          "checked_row", "unchecked_row", "button_focus", "combo_selected",
          "combo_popup", "disabled")
PRODUCT_TEXT = "اطلاعات مالی بالا را شخصاً بررسی و تأیید کرده‌ام."
PRODUCT_REF = {"repo": "rezahh107/Bank2Odoo",
               "commit": "d06b35f41ac46936716b186fb1dfac33da983eb9",
               "path": "bank2odoo/ui/window.py", "line": 297}
INDICATOR_THRESHOLD = 3.0
TEXT_THRESHOLD = 4.5
FIELDS = ("candidate", "style_requested", "style_effective", "font_requested",
          "font_resolved", "treatment", "state", "execution", "measurement",
          "assessment", "semantic_ok", "indicator_contrast_max",
          "indicator_contrast_fraction", "indicator_visible",
          "checked_distinct", "focus_visual_change", "text_role_contrast",
          "button_role_contrast", "disabled_role_contrast", "popup_role_contrast",
          "input_role_contrast", "combo_role_contrast", "disabled_input_role_contrast",
          "keyboard_space", "row_click", "full_size", "dpr",
          "reason", "filename")


def contrast_color(a, b):
    return lab.metrics.contrast(lab.metrics.rgb(a), lab.metrics.rgb(b))


def indicator_geometry(checkbox):
    option = QStyleOptionButton()
    option.initFrom(checkbox)
    return checkbox.style().subElementRect(
        QStyle.SubElement.SE_CheckBoxIndicator, option, checkbox
    )


def indicator_pixels(checkbox, shot):
    """Inspect Qt's actual rendered indicator against the adjacent surface.

    The brightest/darkest pixel alone can be noise; also record the share of
    pixels meeting the 3:1 adjacent-surface threshold. This is NOT text glyph
    contrast and must be reviewed with full-resolution PNG evidence.
    """
    image = shot.toImage().convertToFormat(QImage.Format.Format_RGB32)
    rect = indicator_geometry(checkbox)
    dpr = shot.devicePixelRatio()
    x = max(0, round(rect.x() * dpr))
    y = max(0, round(rect.y() * dpr))
    w = max(1, round(rect.width() * dpr))
    h = max(1, round(rect.height() * dpr))
    # Sampling just outside the indicator on the vertical center line keeps
    # label glyphs out of the reference region for both RTL and LTR controls.
    left = x - max(2, round(5 * dpr))
    right = x + w + max(2, round(5 * dpr))
    neighbor = left if left >= 0 else min(image.width()-1, right)
    bg = image.pixelColor(neighbor, min(image.height()-1, y+h//2))
    background = (bg.red(), bg.green(), bg.blue())
    values = []
    for yy in range(y, min(y+h, image.height())):
        for xx in range(x, min(x+w, image.width())):
            c = image.pixelColor(xx, yy)
            values.append(lab.metrics.contrast(
                (c.red(), c.green(), c.blue()), background
            ))
    if not values:
        return {"max": 0.0, "fraction": 0.0, "visible": False,
                "geometry": [rect.x(), rect.y(), rect.width(), rect.height()],
                "neighbor": bg.name()}
    fraction = sum(v >= INDICATOR_THRESHOLD for v in values) / len(values)
    return {"max": round(max(values), 3), "fraction": round(fraction, 4),
            "visible": fraction >= 0.05,
            "geometry": [rect.x(), rect.y(), rect.width(), rect.height()],
            "neighbor": bg.name()}


def apply_treatment(checkbox, name, cfg):
    if name == "native":
        return
    if name == "checkbox_palette":
        # Local QPalette roles only: may be ignored by the native style.
        p = QPalette(checkbox.palette())
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            p.setColor(group, QPalette.ColorRole.WindowText,
                       QColor(cfg["dark_palette"]["text"]))
            p.setColor(group, QPalette.ColorRole.ButtonText,
                       QColor(cfg["dark_palette"]["text"]))
            p.setColor(group, QPalette.ColorRole.Button,
                       QColor(cfg["dark_palette"]["surface"]))
        checkbox.setPalette(p)
        return
    if name == "unchecked_border":
        # Minimal, bounded alternative only for the unchecked indicator.
        # Existing QCheckBox hitButton/keyboard/checked native painting stays.
        checkbox.setStyleSheet(
            "QCheckBox#nativeApproval::indicator:unchecked {"
            "border: 2px solid #DCE7F0; background-color: #202831; }"
        )
        return
    raise ValueError("Unknown checkbox diagnostic treatment")


def full_png(pixmap, path):
    if pixmap.isNull() or not pixmap.save(str(path), "PNG"):
        raise RuntimeError("Cannot save full-resolution capture: " + str(path))


def contact_sheet(snapshots, out, title):
    w, h = 430, 310
    sheet = QImage(w*2, 38+h*5, QImage.Format.Format_RGB32)
    sheet.fill(QColor("#F6F7F9"))
    p = QPainter(sheet)
    p.setPen(QColor("#152030"))
    p.setFont(QFont("Arial", 10))
    p.drawText(8, 25, title + " — reduced preview only")
    for idx, name in enumerate(STATES):
        x, y = idx % 2*w, 38+(idx//2)*h
        p.drawText(x+8, y+17, name)
        p.drawPixmap(x+5, y+24, w-10, h-29, snapshots[name])
    p.end()
    if not sheet.save(str(out), "PNG"):
        raise RuntimeError("Cannot save contact sheet")


def role_contrasts(controls):
    pal = controls["approval"].palette()
    text = contrast_color(
        pal.color(QPalette.ColorRole.WindowText).name(),
        pal.color(QPalette.ColorRole.Window).name(),
    )
    button = controls["secondary"].palette()
    secondary = contrast_color(
        button.color(QPalette.ColorRole.ButtonText).name(),
        button.color(QPalette.ColorRole.Button).name(),
    )
    disabled = contrast_color(
        button.color(QPalette.ColorGroup.Disabled,
                     QPalette.ColorRole.ButtonText).name(),
        button.color(QPalette.ColorGroup.Disabled,
                     QPalette.ColorRole.Button).name(),
    )
    popup_pal = controls["combo"].view().palette()
    popup = contrast_color(
        popup_pal.color(QPalette.ColorRole.Text).name(),
        popup_pal.color(QPalette.ColorRole.Base).name(),
    )
    input_pal = controls["amount"].palette()
    input_ratio = contrast_color(
        input_pal.color(QPalette.ColorRole.Text).name(),
        input_pal.color(QPalette.ColorRole.Base).name(),
    )
    input_disabled = contrast_color(
        input_pal.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text).name(),
        input_pal.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base).name(),
    )
    combo_pal = controls["combo"].palette()
    combo_ratio = contrast_color(
        combo_pal.color(QPalette.ColorRole.ButtonText).name(),
        combo_pal.color(QPalette.ColorRole.Button).name(),
    )
    return {"text": text, "secondary": secondary,
            "disabled": disabled, "popup": popup, "input": input_ratio,
            "input_disabled": input_disabled, "combo": combo_ratio}


def capture_state(host, controls, state, out, stem):
    cb, button, combo = controls["approval"], controls["button"], controls["combo"]
    button.setEnabled(True)
    button.setDown(False)
    cb.setEnabled(True)
    cb.setChecked(False)
    combo.setCurrentIndex(0)
    host.activateWindow()
    QTest.mouseMove(host, QPoint(5, 5))
    host.setFocus(Qt.FocusReason.OtherFocusReason)
    QCoreApplication.processEvents()
    QTest.qWait(35)
    semantic, keyboard, row = True, False, False
    focus_delta = None
    neutral = cb.grab()
    unfocused_button = button.grab()
    if state == "checkbox_focus":
        combo.setFocus(Qt.FocusReason.TabFocusReason)
        QTest.keyClick(combo, Qt.Key.Key_Tab)
        semantic = cb.hasFocus()
        focus_delta = lab.metrics.difference(neutral, cb.grab())["changed"]
    elif state == "checked_space":
        cb.setFocus()
        before = not cb.isChecked()
        QTest.keyClick(cb, Qt.Key.Key_Space)
        keyboard = before and cb.isChecked()
        semantic = keyboard
    elif state == "unchecked_space":
        cb.setChecked(True)
        before = cb.isChecked()
        cb.setFocus()
        QTest.keyClick(cb, Qt.Key.Key_Space)
        keyboard = before and not cb.isChecked()
        semantic = keyboard
    elif state == "checked_row":
        QTest.mouseClick(cb, Qt.MouseButton.LeftButton,
                         pos=QPoint(5, cb.height() // 2))
        row = cb.isChecked()
        semantic = row
    elif state == "unchecked_row":
        cb.setChecked(True)
        QTest.mouseClick(cb, Qt.MouseButton.LeftButton,
                         pos=QPoint(5, cb.height() // 2))
        row = not cb.isChecked()
        semantic = row
    elif state == "button_focus":
        cb.setFocus(Qt.FocusReason.TabFocusReason)
        QTest.keyClick(cb, Qt.Key.Key_Tab)
        semantic = button.hasFocus()
        # Focus must actually be painted, not merely held in Qt state.
        # Compare a matched pre-Tab target (captured before the event).
        focus_delta = lab.metrics.difference(unfocused_button, button.grab())["changed"]
    elif state == "combo_selected":
        combo.setFocus()
        QTest.keyClick(combo, Qt.Key.Key_Down)
        semantic = combo.currentIndex() == 1
    elif state == "combo_popup":
        combo.showPopup()
        QCoreApplication.processEvents()
        QTest.qWait(75)
        semantic = combo.view().isVisible()
        full_png(combo.view().grab(), out / f"{stem}_{state}_popup.png")
    elif state == "disabled":
        button.setEnabled(False)
        cb.setEnabled(False)
        semantic = not button.isEnabled() and not cb.isEnabled() and not controls["disabled_input"].isEnabled()
    QCoreApplication.processEvents()
    QTest.qWait(45)
    full = host.grab()
    full_png(full, out / f"{stem}_{state}.png")
    checked = cb.grab()
    indicator = indicator_pixels(cb, checked)
    if state == "combo_popup":
        combo.hidePopup()
    return full, checked, indicator, bool(semantic), keyboard, row, focus_delta


def text_fixture(text, font, name, out, checked=False):
    """Same string/font/direction/560x52 bounds in QLabel and QCheckBox."""
    host = QWidget()
    host.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    host.resize(620, 190)
    layout = QVBoxLayout(host)
    label = QLabel(text)
    cb = lab.FullRowCheckBox(text)
    cb.setObjectName("textFixtureApproval")
    for widget in (label, cb):
        widget.setFont(font)
        widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        widget.setFixedSize(560, 52)
        layout.addWidget(widget)
    cb.setChecked(checked)
    host.show()
    QCoreApplication.processEvents()
    QTest.qWait(45)
    label_img = label.grab()
    cb_img = cb.grab()
    full_png(label_img, out / f"{name}_label.png")
    full_png(cb_img, out / f"{name}_checkbox.png")
    metrics = QFontMetrics(font)
    info = {"text": text, "font_requested": font.family(),
            "label_font_resolved": QFontInfo(label.font()).family(),
            "checkbox_font_resolved": QFontInfo(cb.font()).family(),
            "dimensions_equal": label.size() == cb.size(),
            "direction_equal": label.layoutDirection() == cb.layoutDirection(),
            "font_equal": label.font() == cb.font(),
            "text_equal": label.text() == cb.text(),
            "label_advance": metrics.horizontalAdvance(text),
            "label_fits": metrics.horizontalAdvance(text) < label.width()-8,
            "checkbox_fits_estimated": metrics.horizontalAdvance(text) < cb.width()-50,
            "per_glyph_fallback_proven": False}
    host.close()
    return info, label_img, cb_img


def negative_controls(app, cfg, out, font):
    valid = PRODUCT_TEXT
    malformed = valid.replace("بررسی", "بر\u200cرسی", 1)
    if malformed == valid or malformed.replace("بر\u200cرسی", "بررسی", 1) != valid:
        raise RuntimeError("Malformed joining fixture did not differ as expected")
    valid_info, label_valid, checkbox_valid = text_fixture(
        valid, font, "negative_valid", out
    )
    bad_info, label_bad, checkbox_bad = text_fixture(
        malformed, font, "negative_zwnj", out
    )
    joining = {
        "expected_distinguished": malformed != valid,
        "zwnj_inserted_in_word": "بر\u200cرسی" in malformed,
        "label_visual_changed": lab.metrics.difference(label_valid, label_bad)["changed"],
        "checkbox_visual_changed": lab.metrics.difference(checkbox_valid, checkbox_bad)["changed"],
        "limit": "Exact-text invalidity is deterministic; rendered shaping still needs visual review",
    }
    control = lab.FullRowCheckBox("نشانگر عمداً کم‌رنگ")
    control.setObjectName("nativeApproval")
    control.setFont(font)
    control.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    control.setFixedSize(560, 52)
    control.setStyleSheet(
        "QCheckBox#nativeApproval::indicator:unchecked {"
        "border: 1px solid #161B22; background-color: #151A21; }"
    )
    control.show()
    QCoreApplication.processEvents()
    QTest.qWait(45)
    negative_shot = control.grab()
    full_png(negative_shot, out / "negative_indicator.png")
    indicator = indicator_pixels(control, negative_shot)
    control.close()
    return {
        "joining": joining, "fixture_info": {"valid": valid_info, "malformed": bad_info},
        "indicator": indicator,
        # An explicit color contract and Qt-painted pixels are two DIFFERENT
        # observations. Windows11 may override the scoped indicator drawing;
        # do not mislabel a palette/token check as actual pixel evidence.
        "indicator_declared_ratio": contrast_color("#161B22", "#151A21"),
        "indicator_detected_as_inadequate": (
            contrast_color("#161B22", "#151A21") < INDICATOR_THRESHOLD
        ),
        "indicator_rendered_low_contrast": not indicator["visible"],
        "indicator_declared_vs_rendered_agree": not indicator["visible"],
        "limit": "Declared contrast fixture is deterministic; QWidget-grab pixels may not respect Qt QSS and need visual review",
    }


def run(cfg, out, scale_tag):
    out.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    available = {name.casefold(): name for name in QStyleFactory.keys()}
    families = {name.casefold(): name for name in QFontDatabase.families()}
    installed = [families[name.casefold()] for name in FONTS if name.casefold() in families]
    env = {
        "source_sha": os.getenv("GITHUB_SHA"), "run_id": os.getenv("GITHUB_RUN_ID"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "windows_build":
            sys.getwindowsversion().build if sys.platform == "win32" else None,
        "qt": qVersion(), "pyside": PYSIDE_VERSION,
        "qpa": app.platformName(), "available_styles": list(available.values()),
        "requested_fonts": list(FONTS), "installed_tested_fonts": installed,
        "missing_fonts": [f for f in FONTS if f.casefold() not in families],
        "per_glyph_fallback_proven": False,
        "qt_scale_factor": os.getenv("QT_SCALE_FACTOR"),
        "actual_os_display_scale_verified": False, "scale_tag": scale_tag,
        "product_text_source": PRODUCT_REF, "product_text": PRODUCT_TEXT,
        "synthetic_text": cfg["fields"]["approval"],
        "capture": "full-resolution lossless QWidget.grab() saved before reduced previews",
        "thresholds": {"text_role": TEXT_THRESHOLD, "indicator_pixel": INDICATOR_THRESHOLD,
                       "indicator_pixel_fraction_min": 0.05},
        "font_fixtures": {}, "negative_controls": {}, "candidates": {},
        "limitations": ["Qt hosted runner, not physical Windows 11 PC",
                        "QT_SCALE_FACTOR is synthetic, not OS Display scaling",
                        "QFontInfo family does not prove per-glyph fallback",
                        "Palette role contrast is not glyph-pixel contrast",
                        "Simulated QTest events and widget grabs are not physical input/screenshots"],
    }
    rows = []
    # No available requested font means no substituted evidence.
    for font_name in installed:
        font = QFont(font_name, cfg["font_point_size"])
        app.setFont(font)
        for style_name in STYLES:
            for treatment in TREATMENTS:
                candidate = f"{style_name.casefold()}_{font_name.lower()}_{treatment}"
                style_key = available.get(style_name.casefold())
                if style_key is None:
                    for state in STATES:
                        rows.append(dict(candidate=candidate, style_requested=style_name,
                                         font_requested=font_name, treatment=treatment, state=state,
                                         execution="NOT_EXECUTED", measurement="NOT_MEASURED",
                                         assessment="INCONCLUSIVE", reason="QStyle unavailable"))
                    continue
                style = QStyleFactory.create(style_key)
                if style is None:
                    for state in STATES:
                        rows.append(dict(candidate=candidate, style_requested=style_name,
                                         font_requested=font_name, treatment=treatment, state=state,
                                         execution="NOT_EXECUTED", measurement="NOT_MEASURED",
                                         assessment="INCONCLUSIVE", reason="QStyleFactory.create failed"))
                    continue
                app.setStyle(style)
                lab.apply_palette(app, cfg, True)
                app.setFont(font)
                # Text fixtures belong to the same dark QStyle and font
                # context as the associated whole-form experiment.
                if treatment == TREATMENTS[0]:
                    if not env["negative_controls"]:
                        env["negative_controls"] = negative_controls(app, cfg, out, font)
                    for phrase, text in (("synthetic", cfg["fields"]["approval"]),
                                         ("product", PRODUCT_TEXT)):
                        fixture, _, _ = text_fixture(
                            text, font,
                            f"text_{style_name.lower()}_{font_name}_{phrase}", out
                        )
                        env["font_fixtures"][
                            f"{style_name}_{font_name}_{phrase}"
                        ] = fixture
                host, controls = lab.build_host(cfg, cfg["variants"][0])
                secondary_buttons = [
                    b for b in host.findChildren(QPushButton)
                    if b.text() == cfg["fields"]["secondary"]
                ]
                if len(secondary_buttons) != 1:
                    raise RuntimeError("Synthetic secondary button not uniquely found")
                controls["secondary"] = secondary_buttons[0]
                cb = controls["approval"]
                apply_treatment(cb, treatment, cfg)
                primary.emphasize(controls["button"], "button_qss", "dark")
                host.show()
                QCoreApplication.processEvents()
                QTest.qWait(80)
                resolved = QFontInfo(cb.font()).family()
                roles = role_contrasts(controls)
                shots = {}
                infos = {}
                for state in STATES:
                    image, cb_shot, metric, semantic, key, row, focus = capture_state(
                        host, controls, state, out, candidate
                    )
                    shots[state] = image
                    infos[state] = {"metric": metric, "semantic": semantic,
                                    "keyboard": key, "row": row, "focus": focus,
                                    "checked": cb.isChecked()}
                unchecked = infos["unchecked"]["metric"]
                checked = infos["checked_space"]["metric"]
                cb.setEnabled(True)
                cb.setChecked(False)
                QCoreApplication.processEvents()
                raw_unchecked = cb.grab()
                cb.setChecked(True)
                QCoreApplication.processEvents()
                raw_checked = cb.grab()
                # State difference is measured in indicator ROI (not a huge row).
                rect = indicator_geometry(cb)
                scale = raw_checked.devicePixelRatio()
                px_rect = lab.QRect(
                    round(rect.x()*scale), round(rect.y()*scale),
                    max(1, round(rect.width()*scale)),
                    max(1, round(rect.height()*scale))
                )
                distinct = lab.metrics.difference(
                    raw_unchecked.copy(px_rect),
                    raw_checked.copy(px_rect)
                )["changed"]
                contact_sheet(shots, out / f"contact_sheet_{candidate}.png", candidate)
                env["candidates"][candidate] = {
                    "font_requested": font_name, "font_resolved": resolved,
                    "style_effective": app.style().objectName(),
                    "treatment": treatment,
                    "role_contrasts": roles,
                    "unchecked_indicator": unchecked,
                    "checked_indicator": checked,
                    "checked_distinct": distinct,
                    "checkbox_local_qss": cb.styleSheet(),
                    "primary_button_local_qss": controls["button"].styleSheet(),
                    "other_qss_empty": all(not controls[name].styleSheet()
                                           for name in ("combo", "amount", "secondary")),
                    "per_glyph_fallback_proven": False,
                }
                for state in STATES:
                    result = infos[state]
                    semantic = (result["semantic"]
                                and bool(controls["button"].styleSheet())
                                and not controls["card"].styleSheet()
                                and env["candidates"][candidate]["other_qss_empty"])
                    # Indicator unreadability is a distinct blocking concern,
                    # not a successful checkbox semantic test.
                    indicator_visible = unchecked["visible"] and checked["visible"]
                    contrast_ok = all(
                        roles[name] >= TEXT_THRESHOLD
                        for name in ("text", "secondary", "input", "combo", "popup")
                    )
                    disabled_readable = (state != "disabled" or
                                         (roles["disabled"] >= TEXT_THRESHOLD and
                                          roles["input_disabled"] >= TEXT_THRESHOLD))
                    if not semantic or not contrast_ok or not disabled_readable:
                        assessment = "FAIL"
                    elif (not indicator_visible or not distinct or
                          (state in ("checkbox_focus", "button_focus") and
                           result["focus"] is not True)):
                        assessment = "INCONCLUSIVE"
                    else:
                        assessment = "PASS"
                    rows.append(dict(
                        candidate=candidate, style_requested=style_name,
                        style_effective=app.style().objectName(),
                        font_requested=font_name, font_resolved=resolved,
                        treatment=treatment, state=state, execution="EXECUTED",
                        measurement="MEASURED", assessment=assessment,
                        semantic_ok=semantic,
                        indicator_contrast_max=unchecked["max"],
                        indicator_contrast_fraction=unchecked["fraction"],
                        indicator_visible=indicator_visible,
                        checked_distinct=distinct, focus_visual_change=result["focus"],
                        text_role_contrast=roles["text"],
                        button_role_contrast=roles["secondary"],
                        disabled_role_contrast=roles["disabled"],
                        popup_role_contrast=roles["popup"],
                        input_role_contrast=roles["input"],
                        combo_role_contrast=roles["combo"],
                        disabled_input_role_contrast=roles["input_disabled"],
                        keyboard_space=result["keyboard"], row_click=result["row"],
                        full_size=f"{shots[state].width()}x{shots[state].height()}",
                        dpr=shots[state].devicePixelRatio(),
                        reason=("SEMANTIC_OR_ROLE_CONTRAST" if assessment=="FAIL"
                                else "INDICATOR_NOT_VISIBLE" if not indicator_visible
                                else "CHECKED_UNCHECKED_NOT_DISTINCT" if not distinct
                                else "FOCUS_VISUAL_NOT_PROVEN" if assessment=="INCONCLUSIVE"
                                else ""),
                        filename=f"{candidate}_{state}.png",
                    ))
                host.close()
                QCoreApplication.processEvents()
    # Mandatory negative control must be distinguishable in machine checks.
    neg = env["negative_controls"]
    if installed and (not neg["joining"]["expected_distinguished"]
                      or not neg["joining"]["zwnj_inserted_in_word"]
                      or not neg["indicator_detected_as_inadequate"]):
        raise RuntimeError("Synthetic negative control was not distinguished")
    with (out / "measurements.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({k: r.get(k, "") for k in FIELDS} for r in rows)
    (out / "environment.json").write_text(
        json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8")
    assessed = {a:sum(r.get("assessment")==a for r in rows)
                for a in ("PASS", "FAIL", "INCONCLUSIVE")}
    executed = sum(r.get("execution")=="EXECUTED" for r in rows)
    lines = [
        "# Synthetic dark-palette whole-form + approval-checkbox qualification",
        f"Source head: {env['source_sha']}; scale: {scale_tag}",
        f"Styles: {STYLES}; installed fonts: {installed}; unavailable: {env['missing_fonts']}",
        f"Expected rows: {len(STYLES)*len(TREATMENTS)*len(STATES)*len(installed)}",
        f"Executed: {executed}; not executed: {len(rows)-executed}; assessments: {assessed}",
        f"Malformed ZWNJ control distinguished: {neg.get('joining',{}).get('expected_distinguished')}",
        f"Low-indicator-contrast declared control detected: {neg.get('indicator_detected_as_inadequate')}",
        f"Low-indicator Qt pixel contrast: {neg.get('indicator_rendered_low_contrast')}; declared/rendered agreement: {neg.get('indicator_declared_vs_rendered_agree')}",
        "## Per-candidate indicator evidence",
    ] + [
        f"- {name}: unchecked={d['unchecked_indicator']['visible']} "
        f"(max {d['unchecked_indicator']['max']}:1, fraction {d['unchecked_indicator']['fraction']}), "
        f"checked={d['checked_indicator']['visible']}, distinct={d['checked_distinct']}, "
        f"font={d['font_resolved']}"
        for name, d in env["candidates"].items()
    ] + [
        "## Limits",
        "- Full PNGs are Qt widget grabs; contact sheets are resized previews.",
        "- QPalette role contrast is not font/glyph pixel contrast.",
        "- Only installed fonts are tested, per-glyph fallback not established.",
        "- Native Windows 11 hardware and physical 100/125/150% scale are NOT_PROVEN.",
        "- This is synthetic Lab evidence, not Bank2Odoo product acceptance.",
    ]
    (out / "summary.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("WHOLE_FORM:", json.dumps({"executed":executed,
        "not_executed":len(rows)-executed, "assessments":assessed,
        "fonts":installed, "negative_indicator_declared_detected":
        neg.get("indicator_detected_as_inadequate"),
        "negative_indicator_rendered_low_contrast":
        neg.get("indicator_rendered_low_contrast")}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scale-tag", required=True)
    args = parser.parse_args()
    cfg, _ = lab.load_config()
    run(cfg, args.output, args.scale_tag)


if __name__ == "__main__":
    main()
