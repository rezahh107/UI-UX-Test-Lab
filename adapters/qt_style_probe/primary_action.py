"""Synthetic Qt primary-action emphasis comparison; NOT a product UI test.

Reuses the Lab's existing form, native QStyle and measurement primitives.
Only primary QPushButton emphasis differs across candidates.
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
from PySide6.QtGui import QColor, QFont, QFontDatabase, QFontInfo, QGuiApplication, QImage, QPainter, QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStyleFactory

from . import lab_runner as lab

METHODS = ("font_weight", "palette", "button_qss")
THEMES = ("light", "dark")
STATES = ("normal", "focus", "hover", "pressed", "disabled")
MIN_CONTRAST = 4.5

# Synthetic, explicit button-role and QPushButton-only QSS colors.
# Contrast is computed for color pairs, NOT from captured rendered glyph pixels.
TOKENS = {
    "light": {
        "background": "#164B85", "foreground": "#FFFFFF",
        "hover": "#1D5D99", "pressed": "#123B67",
        "disabled_background": "#F1F3F6", "disabled_foreground": "#5E6877",
        "focus_border": "#C17D10",
    },
    "dark": {
        "background": "#86C7F0", "foreground": "#112638",
        "hover": "#A3D6FA", "pressed": "#6CAAD6",
        "disabled_background": "#303B47", "disabled_foreground": "#B7C4CE",
        "focus_border": "#FFE08C",
    },
}
FIELDS = (
    "style_requested", "style_effective", "theme", "method", "state",
    "execution", "measurement", "assessment", "semantic_ok", "rendered",
    "text_contrast_ratio", "contrast_ok", "contrast_basis",
    "rendered_glyph_contrast_proven", "keyboard_space_activated",
    "focus_via_tab", "geometry_constant", "text_constant", "font_family_constant",
    "font_point_size_constant", "font_weight", "local_button_qss_only",
    "normal_emphasis_visual_change", "method_capture", "reason", "filename",
)


def contrast_pair(fg, bg):
    return lab.metrics.contrast(lab.metrics.rgb(fg), lab.metrics.rgb(bg))


def primary_button_qss(tokens):
    selector = "QPushButton#nativePrimary"
    return (
        f"{selector} {{ background-color: {tokens['background']};"
        f" color: {tokens['foreground']}; border: 1px solid {tokens['background']};"
        " border-radius: 5px; }"
        f" {selector}:hover {{ background-color: {tokens['hover']}; }}"
        f" {selector}:pressed {{ background-color: {tokens['pressed']}; }}"
        f" {selector}:focus {{ border: 2px solid {tokens['focus_border']}; }}"
        f" {selector}:disabled {{ background-color: {tokens['disabled_background']};"
        f" color: {tokens['disabled_foreground']};"
        f" border: 1px solid {tokens['disabled_background']}; }}"
    )


def emphasize(button, method, theme):
    token = TOKENS[theme]
    if method == "font_weight":
        f = QFont(button.font())
        f.setWeight(QFont.Weight.DemiBold)
        button.setFont(f)
    elif method == "palette":
        p = QPalette(button.palette())
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            p.setColor(group, QPalette.ColorRole.Button, QColor(token["background"]))
            p.setColor(group, QPalette.ColorRole.ButtonText, QColor(token["foreground"]))
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button,
                   QColor(token["disabled_background"]))
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText,
                   QColor(token["disabled_foreground"]))
        button.setPalette(p)
    elif method == "button_qss":
        button.setStyleSheet(primary_button_qss(token))
    else:
        raise ValueError("Unexpected primary-action method " + str(method))


def button_role_contrast(button, method, theme, state):
    if method == "button_qss":
        token = TOKENS[theme]
        if state == "disabled":
            return (contrast_pair(token["disabled_foreground"], token["disabled_background"]),
                    "explicit scoped QSS color pair")
        surface = token["background"]
        if state == "hover":
            surface = token["hover"]
        if state == "pressed":
            surface = token["pressed"]
        return contrast_pair(token["foreground"], surface), "explicit scoped QSS color pair"
    group = (QPalette.ColorGroup.Disabled if state == "disabled"
             else QPalette.ColorGroup.Active)
    pal = button.palette()
    foreground = pal.color(group, QPalette.ColorRole.ButtonText)
    background = pal.color(group, QPalette.ColorRole.Button)
    return contrast_pair(foreground.name(), background.name()), "QPalette ButtonText/Button roles (may differ from native pixels)"


def geometry(host, button):
    point = button.mapTo(host, QPoint(0, 0))
    return (point.x(), point.y(), button.width(), button.height(),
            host.width(), host.height())


def capture(host, controls, state, baseline, snapshots):
    button, approval = controls["button"], controls["approval"]
    button.setEnabled(True)
    button.setDown(False)
    button.setAttribute(Qt.WidgetAttribute.WA_UnderMouse, False)
    host.activateWindow()
    QTest.mouseMove(host, QPoint(5, 5))
    host.setFocus(Qt.FocusReason.OtherFocusReason)
    QCoreApplication.processEvents()
    QTest.qWait(20)
    semantic = True
    method = "QWidget.grab() simulated"
    focus_via_tab = False
    if state == "focus":
        approval.setFocus(Qt.FocusReason.TabFocusReason)
        QTest.keyClick(approval, Qt.Key.Key_Tab)
        QCoreApplication.processEvents()
        focus_via_tab = button.hasFocus()
        semantic = focus_via_tab
        method += "; QTest.keyClick(Tab from checkbox), button.hasFocus()"
    elif state == "hover":
        QTest.mouseMove(button, button.rect().center())
        method += "; QTest.mouseMove"
    elif state == "pressed":
        QTest.mousePress(button, Qt.MouseButton.LeftButton, pos=button.rect().center())
        semantic = button.isDown()
        method += "; QTest.mousePress, isDown()"
    elif state == "disabled":
        button.setEnabled(False)
        semantic = not button.isEnabled()
        method += "; setEnabled(False), not isEnabled()"
    QCoreApplication.processEvents()
    QTest.qWait(45)
    full, target = host.grab(), button.grab()
    if full.isNull() or target.isNull():
        raise RuntimeError("Null Qt widget capture for " + state)
    if state == "hover":
        target, rendered, method = lab.record_state_frame(
            host, button, state, full, target,
            {"button": baseline}, method, snapshots,
        )
    else:
        snapshots[state] = full
        rendered = (None if state in ("normal", "disabled") else
                    lab.metrics.difference(baseline, target)["changed"])
    if state == "pressed":
        QTest.mouseRelease(button, Qt.MouseButton.LeftButton,
                           pos=button.rect().center())
    return target, semantic, rendered, focus_via_tab, method


def visual_evidence(state, target, native_normal, native_disabled,
                    emphasized_normal, interactive_rendered):
    """Enforce paint evidence via the existing Qt pixmap difference primitive.

    Normal: native vs emphasized, captured with the same reset/focus/pointer.
    Disabled: candidate vs native disabled AND candidate vs enabled emphasis.
    Other interaction states retain the existing capture rendering verdict.
    """
    if state == "normal":
        return lab.metrics.difference(native_normal, target)["changed"]
    if state == "disabled":
        return (lab.metrics.difference(native_disabled, target)["changed"]
                and lab.metrics.difference(emphasized_normal, target)["changed"])
    return interactive_rendered


def assess_state(semantic_ok, readable_pair, rendered):
    if not semantic_ok or not readable_pair:
        return "FAIL"
    # All five primary-action states require positive visual observation.
    # Missing (None) evidence is not proof of rendered emphasis.
    return "PASS" if rendered is True else "INCONCLUSIVE"


def contact_sheet(images, title, path):
    # Full host frames preserve layout, labels and the untouched surrounding UI.
    w, h, cols = 648, 470, 2
    sheet = QImage(cols * w, 35 + 3 * h, QImage.Format.Format_RGB32)
    sheet.fill(QColor("#F5F6F8"))
    painter = QPainter(sheet)
    painter.setPen(QColor("#182638"))
    painter.setFont(QFont("Arial", 10))
    painter.drawText(10, 24, title + " — synthetic QWidget.grab(); not desktop")
    for n, state in enumerate(STATES):
        x, y = (n % cols) * w, 35 + (n // cols) * h
        painter.drawText(x + 6, y + 16, state)
        painter.drawPixmap(x + 4, y + 20, w - 8, h - 26, images[state])
    painter.end()
    if not sheet.save(str(path)):
        raise RuntimeError("Cannot save " + str(path))


def negative_button_control(out):
    # Same button contrast measurement, but an intentionally unreadable pair.
    from PySide6.QtWidgets import QPushButton
    button = QPushButton("دکمهٔ نمونهٔ کم‌کنتراست")
    button.setObjectName("syntheticLowContrast")
    button.setStyleSheet(
        "QPushButton#syntheticLowContrast {background-color:#565656;"
        "color:#555555; border:1px solid #565656;}"
    )
    button.resize(230, 48)
    button.show()
    QCoreApplication.processEvents()
    shot = button.grab()
    if not shot.save(str(out / "negative_button.png")):
        raise RuntimeError("Cannot save negative contrast control capture")
    ratio = contrast_pair("#555555", "#565656")
    button.close()
    return {"ratio": ratio, "threshold": MIN_CONTRAST, "detected":
            not shot.isNull() and ratio < MIN_CONTRAST,
            "fixture": "synthetic QPushButton-only QSS #555555 on #565656",
            "limit": "explicit token pair; not rendered glyph measurement"}


def run(cfg, out, scale_tag):
    app = QApplication.instance() or QApplication([])
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    families = {name.casefold(): name for name in QFontDatabase.families()}
    family = next((families[f.casefold()] for f in cfg["requested_font_families"]
                   if f.casefold() in families), app.font().family())
    app.setFont(QFont(family, cfg["font_point_size"]))
    style_keys = {name.casefold(): name for name in QStyleFactory.keys()}
    env = {
        "source_sha": os.getenv("GITHUB_SHA"),
        "run_id": os.getenv("GITHUB_RUN_ID"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "windows_build": sys.getwindowsversion().build if sys.platform == "win32" else None,
        "python": sys.version, "qt": qVersion(), "pyside6_essentials_target": "6.11.2",
        "pyside6_runtime": PYSIDE_VERSION, "qpa": QGuiApplication.platformName(),
        "qt_scale_factor": os.getenv("QT_SCALE_FACTOR"), "scale_tag": scale_tag,
        "actual_windows_display_scale": None, "real_device_accepted": False,
        "requested_styles": cfg["requested_styles"], "available_styles": list(style_keys.values()),
        "themes": list(THEMES), "methods": list(METHODS), "states": list(STATES),
        "font_family": family, "font_point_size": cfg["font_point_size"],
        "synthetic_tokens": TOKENS, "contrast_threshold": MIN_CONTRAST,
        "contrast_limit": "color-role/token pairs, not actual rendered glyph pixel contrast",
        "capture_method": "QWidget.grab() with QTest synthetic interactions",
        "negative_control": None, "baselines": {},
        "limits": ["No financial/product data",
                   "Synthetic Windows hosted runner, not a real Windows 11 user desktop",
                   "QT_SCALE_FACTOR is not Windows OS display scaling",
                   "QTest input does not establish physical mouse or keyboard behavior",
                   "No actual text glyph pixel contrast, human readability or visual acceptance"],
    }
    rows = []
    for requested in cfg["requested_styles"]:
        style_key = style_keys.get(requested.casefold())
        for theme in THEMES:
            for method in METHODS:
                candidate = f"{requested.casefold()}_{theme}_{method}"
                if style_key is None:
                    for state in STATES:
                        rows.append(dict(style_requested=requested, theme=theme,
                                         method=method, state=state, execution="NOT_EXECUTED",
                                         measurement="NOT_MEASURED", assessment="INCONCLUSIVE",
                                         reason="QStyleFactory key unavailable"))
                    continue
                style = QStyleFactory.create(style_key)
                if style is None:
                    for state in STATES:
                        rows.append(dict(style_requested=requested, theme=theme,
                                         method=method, state=state, execution="NOT_EXECUTED",
                                         measurement="NOT_MEASURED", assessment="INCONCLUSIVE",
                                         reason="QStyleFactory.create returned None"))
                    continue
                app.setStyle(style)
                lab.apply_palette(app, cfg, theme == "dark")
                host, controls = lab.build_host(cfg, cfg["variants"][0])
                button = controls["button"]
                # Fix size to the native no-emphasis geometry before changing
                # weight/palette/QSS: the experiment must not reflow the form.
                host.show()
                QCoreApplication.processEvents()
                QTest.qWait(70)
                button.setFixedSize(button.size())
                native_geom = geometry(host, button)
                # Capture native references with *exactly* the same reset,
                # focus, pointer and button state as the emphasized captures.
                # A direct button.grab() here can preserve stale focus/hover
                # left by previous candidates, yielding a false normal delta.
                native_shots = {}
                native_button, _, _, _, _ = capture(
                    host, controls, "normal", None, native_shots
                )
                native_disabled, _, _, _, _ = capture(
                    host, controls, "disabled", None, native_shots
                )
                native_font = QFontInfo(button.font())
                original_text = button.text()
                emphasize(button, method, theme)
                QCoreApplication.processEvents()
                QTest.qWait(50)
                clicked = []
                button.clicked.connect(lambda checked=False: clicked.append(True))
                button.setFocus(Qt.FocusReason.TabFocusReason)
                QTest.keyClick(button, Qt.Key.Key_Space)
                keyboard_activated = bool(clicked)
                # Reference normal painting for the *same* method.
                screenshots = {}
                try:
                    normal_target, _, _, _, _ = capture(
                        host, controls, "normal", native_button, screenshots
                    )
                    normal_emphasis = visual_evidence(
                        "normal", normal_target, native_button, native_disabled,
                        normal_target, None
                    )
                    geom = geometry(host, button)
                    if geom != native_geom:
                        raise RuntimeError(f"Geometry changed by {candidate}: {native_geom} -> {geom}")
                    for state in STATES:
                        if state == "normal":
                            target, semantic, observed, focus_ok, procedure = (
                                normal_target, True, None, False,
                                "matched native normal reference; QWidget.grab()")
                        else:
                            target, semantic, observed, focus_ok, procedure = capture(
                                host, controls, state, normal_target, screenshots
                            )
                        rendered = visual_evidence(
                            state, target, native_button, native_disabled,
                            normal_target, observed
                        )
                        if state == "disabled":
                            procedure += ("; compare native disabled and"
                                          " emphasized enabled QWidget.grab() references")
                        if state == "disabled":
                            disabled_target = target
                        current_geometry = geometry(host, button)
                        geometry_ok = current_geometry == native_geom
                        family_ok = QFontInfo(button.font()).family() == native_font.family()
                        point_ok = button.font().pointSize() == cfg["font_point_size"]
                        text_ok = button.text() == original_text
                        scoped = (not controls["card"].styleSheet()
                                  and not controls["approval"].styleSheet()
                                  and not controls["combo"].styleSheet()
                                  and not controls["amount"].styleSheet()
                                  and (not button.styleSheet() if method != "button_qss"
                                       else button.styleSheet().startswith("QPushButton#nativePrimary ")))
                        ratio, basis = button_role_contrast(button, method, theme, state)
                        readable_pair = ratio >= MIN_CONTRAST
                        semantic_ok = (semantic and keyboard_activated and geometry_ok
                                       and family_ok and point_ok and text_ok and scoped)
                        assessment = assess_state(
                            semantic_ok, readable_pair, rendered
                        )
                        filename = f"contact_sheet_{candidate}.png"
                        rows.append(dict(
                            style_requested=requested, style_effective=app.style().objectName(),
                            theme=theme, method=method, state=state,
                            execution="EXECUTED", measurement="MEASURED",
                            assessment=assessment, semantic_ok=semantic_ok, rendered=rendered,
                            text_contrast_ratio=ratio, contrast_ok=readable_pair,
                            contrast_basis=basis, rendered_glyph_contrast_proven=False,
                            keyboard_space_activated=keyboard_activated, focus_via_tab=focus_ok,
                            geometry_constant=geometry_ok, text_constant=text_ok,
                            font_family_constant=family_ok, font_point_size_constant=point_ok,
                            font_weight=button.font().weight(),
                            local_button_qss_only=scoped,
                            normal_emphasis_visual_change=normal_emphasis,
                            method_capture=procedure,
                            reason=("LOW_CONTRAST_ROLE_PAIR" if not readable_pair
                                    else "SEMANTIC_OR_INVARIANT_FAIL" if not semantic_ok
                                    else "NOT_RENDERED" if rendered is not True else ""),
                            filename=filename,
                        ))
                    contact_sheet(screenshots, candidate, out / filename)
                    env["baselines"][candidate] = {
                        "native_geometry": native_geom, "native_font": native_font.family(),
                        "method_geometry": geom, "normal_emphasis_changed": normal_emphasis,
                        "disabled_vs_native_changed": lab.metrics.difference(
                            native_disabled, disabled_target)["changed"],
                        "disabled_vs_enabled_changed": lab.metrics.difference(
                            normal_target, disabled_target)["changed"],
                        "keyboard_space_activated": keyboard_activated,
                    }
                finally:
                    host.close()
                    QCoreApplication.processEvents()
    env["negative_control"] = negative_button_control(out)
    if not env["negative_control"]["detected"]:
        raise RuntimeError("Low contrast button negative control was missed")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "measurements.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({k: row.get(k, "") for k in FIELDS} for row in rows)
    (out / "environment.json").write_text(
        json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8")
    executed = [r for r in rows if r["execution"] == "EXECUTED"]
    failed = [r for r in executed if r["assessment"] == "FAIL"]
    unknown = [r for r in executed if r["assessment"] == "INCONCLUSIVE"]
    missing = len(rows) - len(executed)
    lines = [
        f"# Synthetic Qt primary action — {scale_tag}", "",
        f"Commit: {env['source_sha']}",
        f"PySide6 Essentials target: 6.11.2; runtime: {PYSIDE_VERSION}",
        f"QPA: {env['qpa']}; QT_SCALE_FACTOR: {env['qt_scale_factor']}",
        "Matrix: 2 styles × 2 palette themes × 3 methods × 5 states = 60",
        f"Executed/measured: {len(executed)}; not executed: {missing}",
        f"Candidate FAIL: {len(failed)}; INCONCLUSIVE: {len(unknown)}",
        f"Negative low-contrast button detected: {env['negative_control']['detected']}",
        "Text contrast: 4.5:1 threshold on declared QSS or effective QPalette role colors,"
        " NOT rendered text pixels.", "",
        "## Failed and inconclusive rows",
    ] + [f"- {r['style_requested']}/{r['theme']}/{r['method']}/{r['state']}: {r['assessment']} {r.get('reason','')}"
         for r in rows if r["execution"] == "EXECUTED" and r["assessment"] != "PASS"] + [
        "", "## Limits",
        "- This compares simulated Qt control painting, not product UI or a physical desktop.",
        "- Qt native QStyle may ignore palette button roles even with a high calculated ratio.",
        "- Synthetic 125%/150% scale is not real Windows Display scaling.",
        "- Actual rendered glyph contrast, human visual clarity and device keyboard/mouse remain unproven.",
    ]
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PRIMARY_ACTION: executed={len(executed)} missing={missing} failed={len(failed)} inconclusive={len(unknown)} negative={env['negative_control']['detected']}")
    # Variant quality FAIL is evidence, not a failure of the execution harness.
    # Fail the job only for broken evidence integrity or missing negative control.
    if any(r.get("geometry_constant") is False for r in executed):
        raise RuntimeError("Geometry invariance violated")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scale-tag", required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cfg, _ = lab.load_config()
    run(cfg, args.output, args.scale_tag)


if __name__ == "__main__":
    main()
