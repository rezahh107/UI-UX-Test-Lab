# Qt Native Styling Lab — Bank2Odoo experiment

This adapter migrates the read-only Bank2Odoo probe at
https://github.com/rezahh107/Bank2Odoo/tree/diag/qt-style-probe/tools/qt_style_probe
as source_probe.py, preserving original Git blob
7b554e784774f2eac02140de17d08f4f3cf46ab8.
lab_runner.py reuses its difference, contrast and image-pixel measurements.
No product code or financial data is imported.

The separate target.json contains synthetic form values, window geometry,
the canonical font, colors and upstream identity.
See [the v33.003 bundled-font source/license/loader contract](../../assets/fonts/vazirmatn/v33.003/README.md). For each available windows11
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

The existing Windows workflow runs on admitted feature-branch pushes or workflow_dispatch, including the bundled-font PR branch. It uses windows-2025 and pinned PySide6 6.11.2,
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
comparison compares normal-state pixels against native button painting captured
with matching focus/pointer/reset conditions. Disabled-state painting must
differ from both matched native-disabled and emphasized-enabled captures.
Missing or unchanged required visual evidence is INCONCLUSIVE, not PASS;
semantic or calculated contrast violations remain FAIL. The existing CSV
columns are retained; environment.json additionally records both disabled
reference comparisons per candidate. QPalette emphasis is not guaranteed
to change native Qt painting.

Each run writes a new run-ID evidence folder. Historical evidence retains
the original evaluator's meaning and is not reclassified by this repair.

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


## Fusion dark whole-form and Persian approval diagnostic (bounded)

\`whole_form.py\` reuses this Lab's synthetic \`build_host()\`, Qt
\`QWidget.grab()\`, QTest events, palette utilities and the previously tested
**primary-button-only** scoped QSS. It does not import or execute Bank2Odoo.
It reads no product data. The static, public UI string
«اطلاعات مالی بالا را شخصاً بررسی و تأیید کرده‌ام.» was checked in read-only
Bank2Odoo \`bank2odoo/ui/window.py\` at \`d06b35f\`, line 297.

The experiment compares Windows11 (only if exposed by QStyleFactory) and
Fusion in the SAME dark QPalette with the original synthetic form. Each
available installed Tahoma/Vazirmatn font is recorded separately by QFontInfo;
an unavailable font is NOT tested. This does not prove glyph-by-glyph fallback.

Per style/font, native checkbox painting is compared with (a) a local
checkbox-only QPalette override and (b) a minimal
\`QCheckBox#nativeApproval::indicator:unchecked\` QSS border. No global QSS,
custom hit testing or changed keyboard semantics are added. Both static UI
sentences are captured independently in QCheckBox and QLabel under equal
font, RTL direction, text and fixed widget geometry. A deliberate incorrect
ZWNJ within «بررسی» and an intentionally low-contrast unchecked indicator
are saved as independent negative controls. Exact-text invalidity is tested
deterministically; rendering differences are reported, not presumed.

The synthetic matrix exercises unchecked, checkbox keyboard focus, checked
and unchecked via Space and full-row clicks, primary button focus, ComboBox
choice/popup and disabled controls. Color-role contrast is recorded for
checkbox labels, inputs, ComboBox, popup, secondary buttons and disabled
controls. The indicator's actual Qt pixels are evaluated against a sampled
adjacent surface (3:1 indicator threshold and 5% of indicator pixels).
This simple threshold is diagnostic rather than full accessibility proof.
Unchanged/insufficient indicator evidence is INCONCLUSIVE, never automatically
PASS. Semantic/contrast defects are FAIL.

Each run first saves **full native-pixel-resolution lossless PNGs**, including
separate native popup captures, then generates reduced contact-sheet previews.
The existing Windows workflow runs this additional diagnostic in
\`evidence/qt-style-probe/<run-id>/<scale>/whole-form/\` on \`lab-evidence\`.
Its three scale contexts remain runner-native, QT_SCALE_FACTOR=1.25 and 1.5.
The prior evidence runs are immutable, and this experiment requires a distinct
run-ID to identify the exact evaluator and feature commit.

Run independently after installing PySide6-Essentials==6.11.2:

    python -m adapters.qt_style_probe.whole_form --output "artifacts/qt-style-probe/local/whole-form" --scale-tag local-synthetic

**NOT_PROVEN**: actual Windows 11 native OS scale (100/125/150%),
physical keyboard/mouse, real device font fallback, final Persian readability,
assistive tech or glyph-pixel contrast. A specialist must inspect the full
PNG indicator (including unchecked), glyph joining and focus before deciding
whether the local checkbox treatment is acceptable.


## Product-equivalent 22px approval-control qualification (read-only source)

\`approval_equivalence.py\` is a separate bounded Lab diagnostic that uses the
public, fixed approval UI sentence and reconstructs only the following source
contracts from Bank2Odoo commit
\`d06b35f41ac46936716b186fb1dfac33da983eb9\`:
\`_ApprovalIndicatorStyle.pixelMetric\` returns \`max(native,22)\` for indicator
width and height; \`_FullRowCheckBox.hitButton\` accepts any point inside the
row; the checkbox uses minimum height 52, \`StrongFocus\`, and RTL. Its native
vs scoped \`QCheckBox#nativeApproval::indicator:unchecked\` QSS comparison
reuses the existing Lab form and dark QPalette and does NOT import or run the
product (the full product panel, custom QGroupBox surfaces and data logic are
not reproduced). The original files remain unchanged.

The test measures the original proxy \`pixelMetric\`, the **effective** Qt
\`checkbox.style().pixelMetric\` and \`SE_CheckBoxIndicator\` rectangle.
The border candidate is a FAIL if it collapses the 22px indicator geometry,
even if it makes unchecked pixels brighter. Synthetic keyboard Space, Tab focus,
full-row click and checked/unchecked distinction are independently checked.
The measured indicator pixels are compared with a nearby rendered surface;
role-pair contrast is recorded separately, not treated as glyph-pixel contrast.
Unexpected or missing visual evidence is NOT_PROVEN, never a product PASS.

The existing Windows workflow runs this alongside \`lab_runner\`,
\`primary_action\`, and \`whole_form\` and saves *original-resolution* PNGs,
small previews, measurements.csv, environment.json and summary.md in
\`evidence/qt-style-probe/<run-id>/<scale>/approval-equivalence/\` on
\`lab-evidence\`. Vazirmatn is bundled and canonical. Optional --compare-tahoma runs only when Tahoma is available, otherwise NOT_EXECUTED. Missing QStyles remain NOT_EXECUTED. Physical Windows 11 and genuine
OS Display scales 100/125/150 are **always NOT_EXECUTED** in the hosted
Windows-2025 CI and cannot be inferred from \`QT_SCALE_FACTOR\`.

Invoke independently from a PySide6-Essentials==6.11.2 Lab checkout:

    python -m adapters.qt_style_probe.approval_equivalence --output "artifacts/qt-style-probe/manual/approval-equivalence" --scale-tag manual-synthetic

Product adoption is NOT qualified by this proxy-equivalence test alone:
a user-supervised real Windows11 visual and accessibility check under actual
display scaling is still mandatory.
