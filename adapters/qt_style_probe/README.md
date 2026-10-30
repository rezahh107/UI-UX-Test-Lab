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


## Synthetic primary-action emphasis comparison (separate experiment)

\`primary_action.py\` reuses the existing \`build_host\`, synthetic labels,
640 × 450 layout, font family/point size, QPalette implementation, pixel
difference and Qt host capture. The primary \`QPushButton#nativePrimary\` is the
**only** styling target. For each QStyle (\`windows11\` if installed, and
\`Fusion\` separately), both the native/light and declared dark-palette
contexts test these three independent emphasis methods:

- \`font_weight\`: only primary-button font weight becomes DemiBold.
- \`palette\`: only primary-button \`QPalette.Button\` and \`ButtonText\`
  roles change; native QStyle might ignore these colors.
- \`button_qss\`: **only** \`QPushButton#nativePrimary\` gets background,
  text, hover, pressed, disabled, and focus-border CSS pseudo selectors.
  No card, other control, or application-wide QSS.

Each of the 2 × 2 × 3 combinations tests normal, focus via keyboard Tab,
hover, pressed, and disabled states (60 rows per scale). Button geometry is
fixed to the pre-emphasis native widget, and the unchanged text, base
font family/point size and keyboard Space activation are checked. The
comparison logs whether normal button pixels actually differ from native;
\`QPalette\` emphasis must **not** be assumed to paint on every style.

Every row has independent EXECUTED/NOT_EXECUTED, MEASURED/NOT_MEASURED,
semantic status, and contrast metadata. Color contrast >= 4.5:1 is
checked using explicit QSS colors or effective Qt \`ButtonText\`/\`Button\`
palette color roles: **this is not rendered-glyph contrast**. A deliberately
unreadable \`#555555\` on \`#565656\` synthetic button QSS and its PNG
negative control must be detected. A hover/focus visual change that cannot
be observed remains INCONCLUSIVE, not an invented PASS.

### Invocation / evidence

Install *PySide6-Essentials==6.11.2* with Python 3.12+ and Git in the Lab
checkout; use an interactive Windows QPA for Windows-specific results:

    python -m pip install "PySide6-Essentials==6.11.2"
    python -m adapters.qt_style_probe.primary_action --output "artifacts/primary-action/native" --scale-tag runner-native

The existing Windows workflow executes this alongside \`lab_runner\` for
runner-native and both synthetic QT_SCALE_FACTOR values; evidence appears
under \`lab-evidence/evidence/qt-style-probe/<run-id>/<scale>/primary-action/\`.
It includes \`measurements.csv\`, \`environment.json\`, \`summary.md\`,
\`negative_button.png\`, and 12 contact sheets when both styles are present.
Artifacts are never committed to main.

Windows hosted runners are not the accountant's Windows 11 machine; Qt
widget captures are not physical screen grabs, synthetic scale is not
Windows Display scaling, and QTest actions do not prove physical input.
Inspect the saved PNGs, then validate visual contrast, focus ring,
hover, keyboard handling, readability and 100/125/150% actual Windows
display scaling on an interactive Windows 11 system before product adoption.
