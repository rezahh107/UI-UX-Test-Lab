# Qt Native Styling Lab — Bank2Odoo experiment

This adapter migrates the read-only Bank2Odoo probe at
https://github.com/rezahh107/Bank2Odoo/tree/diag/qt-style-probe/tools/qt_style_probe
as source_probe.py, preserving original Git blob
7b554e784774f2eac02140de17d08f4f3cf46ab8.
lab_runner.py reuses its difference, contrast and image-pixel measurements.
No product code or financial data is imported.

The separate target.json contains synthetic form values, window geometry,
font candidates, colors and upstream identity. For each available windows11
and Fusion QStyle, four variants keep all non-style variables fixed:
baseline, palette, card_qss, and palette_card_qss. Card QSS is scoped to
QFrame#probeSurface; no QSS is applied directly to native buttons,
checkboxes, combo boxes, or edit fields. Native checkbox semantics remain
including keyboard Space and a full-row hit region.

Each candidate exercises idle, keyboard focus, hover, press, checked,
unchecked, disabled, invalid, combo selection and open popup. The low-contrast
negative control is #555555 text on #565656 and is tested by calculated
palette-role contrast, not rendered glyph pixels. Every state has separate
EXECUTED/NOT_EXECUTED and MEASURED/NOT_MEASURED status and an independent
PASS/FAIL/INCONCLUSIVE assessment.

## Windows CI

The ONE added Windows workflow runs only from the dedicated feature branch
push or workflow_dispatch. It uses windows-2025 and pinned PySide6 6.11.2,
runs the existing unchanged foundation verifier/tests, and commits only
curated synthetic captures, CSV, environment JSON and short summaries to
lab-evidence at evidence/qt-style-probe/<run-id>/. It never pushes to main.
The ephemeral GitHub token has repository-scoped contents:write; the workflow
only issues a push to lab-evidence, so branch protection remains valuable.

Runs: runner-native (actual display scale unverified), synthetic-125 with
QT_SCALE_FACTOR=1.25, synthetic-150 with QT_SCALE_FACTOR=1.5. QWidget.grab()
is a Qt widget painting capture, not a physical Windows desktop screenshot.
Qt simulated QTest events are not physical keyboard/pointer actions.
The actual accountant machine is not tested by CI. Windows11 style is marked
NOT_EXECUTED if QStyleFactory does not expose it. Do not substitute Fusion.

## Local real-device procedure (after PR review and merge)

Prerequisites: Git, Python 3.13, an actual interactive Windows 11 desktop,
and one-time Internet access to install pinned PySide6. From Lab root:

    py -3.13 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install "PySide6==6.11.2"
    $env:QT_QPA_PLATFORM = "windows"
    Remove-Item Env:QT_SCALE_FACTOR -ErrorAction SilentlyContinue
    .\.venv\Scripts\python.exe -m adapters.qt_style_probe.lab_runner --output "C:\Private\qt-probe\real-100" --scale-tag real-display-100

First manually configure and verify Windows Display Settings scale 100%.
Then manually configure 125% and 150%, sign in again if required, and rerun
with paths real-125 and real-150 and matching scale-tag values. Keep
QT_SCALE_FACTOR unset for all real scale runs. This tool does not change
OS scaling. Record the effective Windows scale and display details separately.
Directly inspect Persian glyphs, keyboard focus, native checkbox indicator,
combo selection and popup, clipping and contrast. Return each run's PNG,
measurements.csv, environment.json and summary.md, plus permitted true
desktop screenshots. A specialist must review NOT_RENDERED results and
possible clipped or low-contrast controls.

See [foundation contract](../../docs/FOUNDATION.md) for verification boundaries.
Generated local files must remain outside Git or in ignored artifacts/.
Only the approved evidence workflow curates non-sensitive captures to Git.
