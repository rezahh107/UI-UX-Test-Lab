# Synthetic Qt primary action — synthetic-125

Commit: 9941a3e460ec09a8a50e051bee178622071690b9
PySide6 Essentials target: 6.11.2; runtime: 6.11.2
QPA: windows; QT_SCALE_FACTOR: 1.25
Matrix: 2 styles × 2 palette themes × 3 methods × 5 states = 60
Executed/measured: 60; not executed: 0
Candidate FAIL: 60; INCONCLUSIVE: 0
Negative low-contrast button detected: True
Text contrast: 4.5:1 threshold on declared QSS or effective QPalette role colors, NOT rendered text pixels.

## Failed and inconclusive rows
- windows11/light/font_weight/normal: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/font_weight/focus: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/font_weight/hover: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/font_weight/pressed: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/font_weight/disabled: FAIL LOW_CONTRAST_ROLE_PAIR
- windows11/light/palette/normal: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/palette/focus: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/palette/hover: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/palette/pressed: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/palette/disabled: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/button_qss/normal: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/button_qss/focus: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/button_qss/hover: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/button_qss/pressed: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/light/button_qss/disabled: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/font_weight/normal: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/font_weight/focus: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/font_weight/hover: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/font_weight/pressed: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/font_weight/disabled: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/palette/normal: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/palette/focus: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/palette/hover: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/palette/pressed: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/palette/disabled: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/button_qss/normal: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/button_qss/focus: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/button_qss/hover: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/button_qss/pressed: FAIL SEMANTIC_OR_INVARIANT_FAIL
- windows11/dark/button_qss/disabled: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/font_weight/normal: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/font_weight/focus: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/font_weight/hover: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/font_weight/pressed: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/font_weight/disabled: FAIL LOW_CONTRAST_ROLE_PAIR
- Fusion/light/palette/normal: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/palette/focus: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/palette/hover: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/palette/pressed: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/palette/disabled: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/button_qss/normal: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/button_qss/focus: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/button_qss/hover: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/button_qss/pressed: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/light/button_qss/disabled: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/font_weight/normal: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/font_weight/focus: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/font_weight/hover: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/font_weight/pressed: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/font_weight/disabled: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/palette/normal: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/palette/focus: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/palette/hover: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/palette/pressed: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/palette/disabled: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/button_qss/normal: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/button_qss/focus: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/button_qss/hover: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/button_qss/pressed: FAIL SEMANTIC_OR_INVARIANT_FAIL
- Fusion/dark/button_qss/disabled: FAIL SEMANTIC_OR_INVARIANT_FAIL

## Limits
- This compares simulated Qt control painting, not product UI or a physical desktop.
- Qt native QStyle may ignore palette button roles even with a high calculated ratio.
- Synthetic 125%/150% scale is not real Windows Display scaling.
- Actual rendered glyph contrast, human visual clarity and device keyboard/mouse remain unproven.
