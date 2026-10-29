"""Windows Qt Widgets experiment, adapted from the Bank2Odoo diagnostic probe.

The upstream probe is retained as source_probe.py; its color/geometry/pixel
measurement primitives are used here. No product code, bank data, or Odoo access.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import QPoint, QRect, Qt, qVersion, QCoreApplication
from PySide6.QtGui import QColor, QFont, QFontDatabase, QFontInfo, QGuiApplication, QImage, QPainter, QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStyle, QStyleFactory, QStyleOptionButton, QVBoxLayout, QWidget,
)
from . import source_probe as metrics

CONFIG = Path(__file__).with_name("target.json")
STATES = ("idle", "focus", "hover", "pressed", "checked", "unchecked",
          "disabled", "invalid", "combo_selected", "combo_popup")
FIELDS = ("candidate", "style_requested", "style_effective", "variant", "state",
          "execution", "measurement", "assessment", "rendered", "method",
          "semantic_ok", "reason", "logical_geometry", "physical_pixels",
          "dpr", "palette_text_surface_contrast", "palette_text_card_contrast",
          "host_exceeds_screen", "rendered_card_pixel",
          "card_qss_local", "filename")


class FullRowCheckBox(QCheckBox):
    """Extend native checkbox hit area, leaving native indicator and keyboard intact."""

    def hitButton(self, pos):  # noqa: N802 - Qt virtual override
        return self.rect().contains(pos)


def load_config(path: Path = CONFIG):
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    if obj.get("schema") != "qt-style-probe.lab.v1":
        raise ValueError("Unexpected target configuration schema")
    if [s.casefold() for s in obj["requested_styles"]] != ["windows11", "fusion"]:
        raise ValueError("Only windows11 and Fusion are in scope")
    expected = {(False, False), (True, False), (False, True), (True, True)}
    actual = {(v["palette"], v["scoped_qss"]) for v in obj["variants"]}
    if len(obj["variants"]) != 4 or actual != expected or len({v["id"] for v in obj["variants"]}) != 4:
        raise ValueError("Palette and card QSS must form the complete independent 2x2 matrix")
    if obj["window_width"] < 600 or obj["window_height"] < 400:
        raise ValueError("Window dimensions too small to expose intended controls")
    return obj, hashlib.sha256(raw).hexdigest()


def apply_palette(app, cfg, enabled):
    # Qt restores palettes when changing styles; reset for every candidate.
    palette = QPalette(app.style().standardPalette())
    if enabled:
        color = cfg["dark_palette"]
        values = {
            QPalette.ColorRole.Window: color["window"],
            QPalette.ColorRole.Base: color["surface"],
            QPalette.ColorRole.AlternateBase: color["window"],
            QPalette.ColorRole.WindowText: color["text"],
            QPalette.ColorRole.Text: color["text"],
            QPalette.ColorRole.Button: color["button"],
            QPalette.ColorRole.ButtonText: color["button_text"],
            QPalette.ColorRole.Highlight: color["highlight"],
            QPalette.ColorRole.HighlightedText: color["highlight_text"],
        }
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            for role, value in values.items():
                palette.setColor(group, role, QColor(value))
        for role, value in values.items():
            palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(value))
        for role, value in (
            (QPalette.ColorRole.Button, color["disabled_bg"]),
            (QPalette.ColorRole.ButtonText, color["disabled_text"]),
            (QPalette.ColorRole.Text, color["disabled_text"]),
            (QPalette.ColorRole.WindowText, color["disabled_text"]),
        ):
            palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(value))
    app.setPalette(palette)


def build_host(cfg, variant):
    labels = cfg["fields"]
    host = QWidget()
    host.setObjectName("labHost")
    host.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    host.setWindowTitle("Qt Native Style Diagnostic — Synthetic")
    host.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    host.resize(cfg["window_width"], cfg["window_height"])
    outer = QVBoxLayout(host)
    outer.setContentsMargins(22, 22, 22, 22)
    outer.setSpacing(14)
    title = QLabel(labels["title"])
    title.setObjectName("probeTitle")
    outer.addWidget(title)
    card = QFrame()
    card.setObjectName("probeSurface")
    card.setFrameShape(QFrame.Shape.StyledPanel)
    grid = QGridLayout(card)
    grid.setContentsMargins(20, 18, 20, 18)
    grid.setHorizontalSpacing(18)
    grid.setVerticalSpacing(13)

    bank = QLineEdit(labels["bank"])
    journal = QLineEdit(labels["journal"])
    amount = QLineEdit(labels["amount"])
    amount.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    amount.setObjectName("mixedTechnicalValue")
    combo = QComboBox()
    combo.addItems(("ریال - IRR", "تومان - TOMAN", "واحد آزمایشی"))
    combo.setObjectName("nativeCombo")
    grid.addWidget(QLabel("نام بانک"), 0, 0)
    grid.addWidget(bank, 0, 1)
    grid.addWidget(QLabel("دفتر مالی"), 0, 2)
    grid.addWidget(journal, 0, 3)
    grid.addWidget(QLabel("مبلغ نمونه"), 1, 0)
    grid.addWidget(amount, 1, 1)
    grid.addWidget(QLabel("واحد مالی"), 1, 2)
    grid.addWidget(combo, 1, 3)
    approval = FullRowCheckBox(labels["approval"])
    approval.setObjectName("nativeApproval")
    approval.setMinimumHeight(52)
    approval.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    grid.addWidget(approval, 2, 0, 1, 4)

    buttons = QHBoxLayout()
    button = QPushButton(labels["convert"])
    button.setObjectName("nativePrimary")
    button.setMinimumHeight(42)
    secondary = QPushButton(labels["secondary"])
    secondary.setMinimumHeight(42)
    disabled_button = QPushButton("دکمه غیرفعال")
    disabled_button.setEnabled(False)
    disabled_input = QLineEdit("ورودی غیرفعال")
    disabled_input.setEnabled(False)
    buttons.addWidget(button)
    buttons.addWidget(secondary)
    buttons.addWidget(disabled_button)
    grid.addLayout(buttons, 3, 0, 1, 4)
    grid.addWidget(disabled_input, 4, 0, 1, 2)
    status = QLabel(labels["status"])
    error = QLabel(labels["error"])
    error.setObjectName("errorFeedback")
    error.setVisible(False)
    error_palette = QPalette(error.palette())
    error_palette.setColor(QPalette.ColorRole.WindowText, QColor(cfg["dark_palette"]["error"]))
    error.setPalette(error_palette)
    grid.addWidget(status, 5, 0, 1, 2)
    grid.addWidget(error, 5, 2, 1, 2)
    outer.addWidget(card)
    outer.addStretch(1)

    if variant["scoped_qss"]:
        token = cfg["card_qss"]
        # Deliberately ONLY the card surface selector. Not child native controls.
        card.setStyleSheet(
            "QFrame#probeSurface {"
            f"background-color: {token['background']};"
            f"border: 1px solid {token['border']}; border-radius: 8px; }}"
        )
    return host, {
        "card": card, "button": button, "approval": approval,
        "combo": combo, "amount": amount, "error": error,
        "disabled_button": disabled_button, "disabled_input": disabled_input,
        "status": status,
    }


def capture_state(host, controls, state):
    button = controls["button"]
    approval = controls["approval"]
    combo = controls["combo"]
    amount = controls["amount"]
    error = controls["error"]
    # Reset every state; the order does not leak a prior checked or invalid state.
    button.setEnabled(True)
    button.setDown(False)
    approval.setEnabled(True)
    approval.setChecked(False)
    amount.setEnabled(True)
    combo.setCurrentIndex(0)
    error.hide()
    host.activateWindow()
    QTest.mouseMove(host, QPoint(5, 5))
    host.setFocus(Qt.FocusReason.OtherFocusReason)
    QCoreApplication.processEvents()
    QTest.qWait(30)
    method = "widget.grab()"
    semantic = True
    focus_actual = None
    popup = None
    target = button

    if state == "focus":
        # Synthetic keyboard traversal, not a direct assignment of focus.
        approval.setFocus(Qt.FocusReason.TabFocusReason)
        QTest.keyClick(approval, Qt.Key.Key_Tab)
        QCoreApplication.processEvents()
        focus_actual = button.hasFocus()
        semantic = focus_actual
        method = "QTest.keyClick(Tab from approval), hasFocus(), widget.grab()"
    elif state == "hover":
        QTest.mouseMove(button, button.rect().center())
        method = "QTest.mouseMove simulated; widget.grab()"
    elif state == "pressed":
        QTest.mousePress(button, Qt.MouseButton.LeftButton, pos=button.rect().center())
        semantic = button.isDown()
        method = "QTest.mousePress simulated; isDown(); widget.grab()"
    elif state == "checked":
        approval.setFocus(Qt.FocusReason.TabFocusReason)
        # Click away from the native indicator: verify the whole row hit region.
        QTest.mouseClick(approval, Qt.MouseButton.LeftButton,
                         pos=QPoint(5, approval.height() // 2))
        row_click_ok = approval.isChecked()
        approval.setChecked(False)
        QTest.keyClick(approval, Qt.Key.Key_Space)
        semantic = row_click_ok and approval.isChecked()
        target = approval
        method = "QTest.mouseClick(full row) + keyClick(Space); isChecked(); widget.grab()"
    elif state == "unchecked":
        approval.setFocus(Qt.FocusReason.TabFocusReason)
        QTest.keyClick(approval, Qt.Key.Key_Space)
        QTest.keyClick(approval, Qt.Key.Key_Space)
        semantic = not approval.isChecked()
        target = approval
        method = "QTest.keyClick(Space twice); isChecked(); widget.grab()"
    elif state == "disabled":
        button.setEnabled(False)
        semantic = not button.isEnabled() and not controls["disabled_input"].isEnabled()
        method = "setEnabled(False), isEnabled(), widget.grab()"
    elif state == "invalid":
        error.show()
        QCoreApplication.processEvents()
        target = error
        actual = error.mapTo(host, QPoint(0, 0))
        semantic = error.isVisible() and host.rect().contains(QRect(actual, error.size()))
        method = "invalid-feedback visible and within host; widget.grab()"
    elif state == "combo_selected":
        combo.setFocus()
        QTest.keyClick(combo, Qt.Key.Key_Down)
        semantic = combo.currentIndex() == 1
        target = combo
        method = "QTest.keyClick(Down); currentIndex(); widget.grab()"
    elif state == "combo_popup":
        combo.showPopup()
        QCoreApplication.processEvents()
        QTest.qWait(60)
        semantic = combo.view().isVisible()
        popup = combo.view().grab()
        target = combo
        method = "QComboBox.showPopup(); view.isVisible(); view.grab()"
    QCoreApplication.processEvents()
    QTest.qWait(40)
    image = host.grab()
    target_image = popup if state == "combo_popup" else target.grab()
    if image.isNull() or target_image.isNull():
        raise RuntimeError("Qt widget.grab() returned a null image: " + state)
    if state == "pressed":
        QTest.mouseRelease(button, Qt.MouseButton.LeftButton, pos=button.rect().center())
    if state == "combo_popup":
        combo.hidePopup()
    return image, target_image, target, method, bool(semantic), focus_actual


def compare_targets(state, target_shot, base, widget):
    # Preserve the upstream RGB threshold, but compare checkbox INDICATOR,
    # not an entire 52px-wide row: a 10px checkmark can be <0.1% of row pixels.
    if state in ("idle", "unchecked", "combo_popup", "invalid"):
        return None  # semantic and view visibility are checked independently
    key = "approval" if state == "checked" else (
        "combo" if state == "combo_selected" else "button")
    before = base[key]
    if state == "checked":
        option = QStyleOptionButton()
        option.initFrom(widget)
        logical = widget.style().subElementRect(
            QStyle.SubElement.SE_CheckBoxIndicator, option, widget)
        dpr = target_shot.devicePixelRatio()
        physical = QRect(round(logical.x() * dpr), round(logical.y() * dpr),
                         max(1, round(logical.width() * dpr)),
                         max(1, round(logical.height() * dpr)))
        before, target_shot = before.copy(physical), target_shot.copy(physical)
    return metrics.difference(before, target_shot)["changed"]


def make_sheet(images, candidate, out):
    tile_w, tile_h = 440, 315
    cols = 2
    rows = (len(STATES) + cols - 1) // cols
    sheet = QImage(cols * tile_w, 48 + rows * tile_h, QImage.Format.Format_RGB32)
    sheet.fill(QColor("#F5F6F8"))
    painter = QPainter(sheet)
    painter.setPen(QColor("#1C2939"))
    painter.setFont(QFont("Arial", 10))
    painter.drawText(12, 28, candidate + " — Qt widget.grab(), NOT physical desktop")
    for i, state in enumerate(STATES):
        x, y = (i % cols) * tile_w, 48 + (i // cols) * tile_h
        painter.setPen(QColor("#1C2939"))
        painter.drawText(x + 10, y + 19, state)
        shot = images[state]
        painter.drawPixmap(x + 8, y + 26, tile_w - 16, tile_h - 33, shot)
    painter.end()
    if not sheet.save(str(out)):
        raise RuntimeError("Could not save contact sheet")


def negative_control(cfg, app):
    t = cfg["negative_control"]
    foreground = metrics.rgb(t["foreground"])
    background = metrics.rgb(t["background"])
    ratio = metrics.contrast(foreground, background)
    # A deliberately near-identical actual QLabel palette pair, verified by
    # the same deterministic color-contrast measurement as the normal rows.
    label = QLabel("متن عمداً ناخوانا")
    p = QPalette(label.palette())
    p.setColor(QPalette.ColorRole.WindowText, QColor(t["foreground"]))
    p.setColor(QPalette.ColorRole.Window, QColor(t["background"]))
    label.setPalette(p)
    label.setAutoFillBackground(True)
    label.resize(260, 55)
    label.show()
    QCoreApplication.processEvents()
    shot = label.grab()
    detected = ratio < float(t["max_contrast"]) and not shot.isNull()
    label.close()
    return {"injected": "known low contrast QLabel", "foreground": t["foreground"],
            "background": t["background"], "palette_contrast": ratio,
            "capture_non_null": not shot.isNull(), "detected": detected,
            "limit": "Explicit palette-pair contrast, not actual glyph-pixel analysis"}


def run(config, config_hash, out, scale_tag):
    app = QApplication([])
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    fonts = {f.casefold(): f for f in QFontDatabase.families()}
    requested_font = next((f for f in config["requested_font_families"]
                           if f.casefold() in fonts), app.font().family())
    app.setFont(QFont(requested_font, config["font_point_size"]))
    screen = app.primaryScreen()
    if screen is None:
        raise RuntimeError("No Qt primary screen")
    available = QStyleFactory.keys()
    choices = {x.casefold(): x for x in available}
    env = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "os_release": platform.release(),
        "os_version": platform.version(),
        "windows_build": sys.getwindowsversion().build if sys.platform == "win32" else None,
        "python": sys.version, "qt": qVersion(), "pyside6": PYSIDE_VERSION,
        "qpa_effective": QGuiApplication.platformName(),
        "qpa_requested": os.getenv("QT_QPA_PLATFORM"),
        "available_styles": available,
        "requested_font": requested_font, "resolved_font": QFontInfo(app.font()).family(),
        "font_points": config["font_point_size"],
        "screen_geometry_logical": [screen.geometry().x(), screen.geometry().y(),
                                    screen.geometry().width(), screen.geometry().height()],
        "screen_dpr": screen.devicePixelRatio(),
        "window_logical_size": [config["window_width"], config["window_height"]],
        "qt_scale_factor": os.getenv("QT_SCALE_FACTOR"),
        "scale_tag": scale_tag,
        "display_scale_class": "synthetic_QT_SCALE_FACTOR" if os.getenv("QT_SCALE_FACTOR") else "runner_native_unverified",
        "actual_windows_display_scale": None,
        "color_scheme_reported": str(app.styleHints().colorScheme()),
        "system_theme_verified": False,
        "capture_method": "QWidget.grab() and QComboBox.view().grab(); no desktop capture",
        "run_id": os.getenv("GITHUB_RUN_ID"), "source_sha": os.getenv("GITHUB_SHA"),
        "source_probe": config["source"], "target_config_sha256": config_hash,
        "variants": {}, "negative_controls": {},
        "limits": ["Not accountant Windows 11 desktop",
                   "Qt synthetic scale is not Windows display scaling",
                   "Keyboard/pointer events are QTest simulated, not physical input",
                   "QPalette role contrast is not rendered-glyph contrast"],
    }
    records = []
    for requested in config["requested_styles"]:
        for variant in config["variants"]:
            candidate = requested.casefold() + "_" + variant["id"]
            key = choices.get(requested.casefold())
            if key is None:
                env["variants"][candidate] = {"execution": "NOT_EXECUTED", "reason": "QStyleFactory key unavailable"}
                for state in STATES:
                    records.append(dict(candidate=candidate, style_requested=requested,
                        style_effective="", variant=variant["id"], state=state,
                        execution="NOT_EXECUTED", measurement="NOT_MEASURED",
                        assessment="INCONCLUSIVE", reason="Style unavailable"))
                continue
            style = QStyleFactory.create(key)
            if style is None:
                env["variants"][candidate] = {"execution": "NOT_EXECUTED", "reason": "QStyleFactory.create returned None"}
                for state in STATES:
                    records.append(dict(candidate=candidate, style_requested=requested,
                        style_effective="", variant=variant["id"], state=state,
                        execution="NOT_EXECUTED", measurement="NOT_MEASURED",
                        assessment="INCONCLUSIVE", reason="Style could not be created"))
                continue
            app.setStyle(style)
            apply_palette(app, config, variant["palette"])
            host, w = build_host(config, variant)
            try:
                host.show()
                QCoreApplication.processEvents()
                QTest.qWait(80)
                actual_style = app.style().objectName()
                palette = app.palette()
                color_fg = palette.color(QPalette.ColorRole.Text)
                color_bg = palette.color(QPalette.ColorRole.Base)
                palette_contrast = metrics.contrast(
                    (color_fg.red(), color_fg.green(), color_fg.blue()),
                    (color_bg.red(), color_bg.green(), color_bg.blue()))
                # QLabel is drawn using WindowText, whereas the card's requested
                # background is from QSS or the QPalette Window role.
                card_background = QColor(config["card_qss"]["background"]) if variant["scoped_qss"] else palette.color(QPalette.ColorRole.Window)
                label_foreground = palette.color(QPalette.ColorRole.WindowText)
                card_contrast = metrics.contrast(
                    (card_background.red(), card_background.green(), card_background.blue()),
                    (label_foreground.red(), label_foreground.green(), label_foreground.blue()))
                exceeds_screen = (host.width() > screen.availableGeometry().width() or
                                  host.height() > screen.availableGeometry().height())
                bounded = {}
                for name in ("button", "approval", "combo", "amount", "error",
                             "disabled_button", "disabled_input"):
                    control = w[name]
                    if not control.isVisible():
                        # A hidden control does not have reliable visible geometry.
                        # The invalid state separately verifies error placement.
                        bounded[name] = None
                        continue
                    top_left = control.mapTo(host, QPoint(0, 0))
                    bounds = QRect(top_left, control.size())
                    bounded[name] = host.rect().contains(bounds)
                all_controls_inside = all(value is not False for value in bounded.values())
                env["variants"][candidate] = {
                    "execution": "EXECUTED", "style_requested": requested,
                    "style_effective": actual_style,
                    "palette_roles": {name: palette.color(getattr(QPalette.ColorRole, name)).name()
                                      for name in ("Window", "Base", "Text", "Button", "ButtonText")},
                    "scoped_card_qss": bool(w["card"].styleSheet()),
                    "native_control_qss_empty": all(not w[name].styleSheet()
                        for name in ("button", "approval", "combo", "amount")),
                    "font_resolved": QFontInfo(host.font()).family(),
                    "calculated_windowtext_card_contrast": card_contrast,
                    "host_exceeds_screen_logical": exceeds_screen,
                    "controls_inside_host": bounded,
                    "all_controls_inside_host": all_controls_inside,
                    "host_actual_logical": [host.width(), host.height()],
                    "note": "role-pair contrast not rendered glyph pixel contrast",
                }
                baseline = {key: widget.grab() for key, widget in (
                    ("button", w["button"]), ("approval", w["approval"]),
                    ("combo", w["combo"]), ("error", w["error"]))}
                snapshots = {}
                for state in STATES:
                    full, target, widget, method, semantic, focus = capture_state(host, w, state)
                    snapshots[state] = full
                    rendered = compare_targets(state, target, baseline, widget)
                    if state == "combo_popup":
                        # A popup is a separate Qt window; host.grab() omits it.
                        popup_path = out / f"contact_sheet_{candidate}_popup.png"
                        if not target.save(str(popup_path)):
                            raise RuntimeError("Cannot capture separate native combo popup")
                    physical = target.toImage().size()
                    rect = widget.geometry()
                    card_img = w["card"].grab().toImage()
                    pixel = metrics.px(card_img, min(8, card_img.width()-1),
                                       min(8, card_img.height()-1))
                    # native control styling is deliberately not overridden.
                    scope_ok = all(not w[name].styleSheet()
                                   for name in ("button", "approval", "combo", "amount"))
                    semantic = semantic and scope_ok
                    assessment = "PASS" if semantic and rendered is not False else (
                        "INCONCLUSIVE" if semantic else "FAIL")
                    records.append(dict(
                        candidate=candidate, style_requested=requested,
                        style_effective=actual_style, variant=variant["id"], state=state,
                        execution="EXECUTED", measurement="MEASURED",
                        assessment=assessment, rendered=rendered, method=method,
                        semantic_ok=semantic,
                        reason=("NOT_RENDERED" if rendered is False else ""),
                        logical_geometry=f"{rect.x()},{rect.y()},{rect.width()},{rect.height()}",
                        physical_pixels=f"{physical.width()}x{physical.height()}",
                        dpr=target.devicePixelRatio(),
                        palette_text_surface_contrast=palette_contrast,
                        palette_text_card_contrast=card_contrast,
                        host_exceeds_screen=exceeds_screen,
                        rendered_card_pixel=metrics.hex_rgb(pixel),
                        card_qss_local=scope_ok,
                        filename=f"contact_sheet_{candidate}.png",
                    ))
                make_sheet(snapshots, candidate, out / f"contact_sheet_{candidate}.png")
            finally:
                host.close()
                QCoreApplication.processEvents()
    env["negative_controls"]["low_contrast"] = negative_control(config, app)
    if not env["negative_controls"]["low_contrast"]["detected"]:
        raise RuntimeError("Negative control FAILED: low-contrast fixture was not detected")
    env["negative_controls"]["matrix"] = len(records) == 8 * len(STATES)
    if not env["negative_controls"]["matrix"]:
        raise RuntimeError("Candidate matrix incomplete")
    with (out / "measurements.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({k: r.get(k, "") for k in FIELDS} for r in records)
    (out / "environment.json").write_text(json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8")
    executed = [r for r in records if r["execution"] == "EXECUTED"]
    not_rendered = [r for r in executed if r.get("rendered") is False]
    failed = [r for r in executed if r["assessment"] == "FAIL"]
    lines = [
        "# Qt Widgets diagnostic — " + scale_tag,
        "", "Source: Bank2Odoo diagnostic probe " + config["source"]["commit"],
        "Lab feature commit: " + str(env["source_sha"]),
        "OS: " + env["platform"], "QPA: " + env["qpa_effective"],
        "Scale: " + env["display_scale_class"] + " / QT_SCALE_FACTOR=" + str(env["qt_scale_factor"]),
        "Capture: Qt widget.grab(), not physical desktop",
        "Candidate states: " + str(len(records)),
        "EXECUTED/MEASURED: " + str(len(executed)),
        "NOT_EXECUTED/NOT_MEASURED: " + str(len(records)-len(executed)),
        "Semantic FAIL: " + str(len(failed)),
        "NOT_RENDERED states: " + str(len(not_rendered)),
        "Low-contrast negative control: " + ("DETECTED" if env["negative_controls"]["low_contrast"]["detected"] else "MISSED"),
        "Candidate low role contrast (<4.5): " + ", ".join(k for k,v in env["variants"].items() if v.get("calculated_windowtext_card_contrast", 99) < 4.5),
        "Window larger than logical screen: " + ", ".join(k for k,v in env["variants"].items() if v.get("host_exceeds_screen_logical")),
        "Widgets outside host bounds: " + ", ".join(k for k,v in env["variants"].items() if v.get("all_controls_inside_host") is False),
        "", "## Missing visual changes", "",
    ] + [f"- {r['candidate']} / {r['state']}" for r in not_rendered] + [
        "", "## Limitations",
        "- Runner-native DPI is not proven equivalent to 100% Windows display scaling.",
        "- QT_SCALE_FACTOR is synthetic, not a real 125%/150% Windows desktop setting.",
        "- PASS only covers probe measurements/semantics; no accountant/device acceptance.",
        "- QTest events are simulated, not human input. Review contact sheets visually.",
    ]
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"RESULT: {len(executed)} executed, {len(failed)} semantic failures, {len(not_rendered)} not rendered")
    print("NEGATIVE_CONTROL:", json.dumps(env["negative_controls"]))
    if failed:
        raise SystemExit("Semantic failures: " + ", ".join(f"{r['candidate']}/{r['state']}" for r in failed))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scale-tag", required=True)
    args = parser.parse_args()
    config, config_hash = load_config()
    args.output.mkdir(parents=True, exist_ok=True)
    run(config, config_hash, args.output, args.scale_tag)


if __name__ == "__main__":
    main()
