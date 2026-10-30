# Synthetic Qt primary action — runner-native

Commit: 00822084a464328f4853ac11fc8c974df4c30720
PySide6 Essentials target: 6.11.2; runtime: 6.11.2
QPA: windows; QT_SCALE_FACTOR: None
Matrix: 2 styles × 2 palette themes × 3 methods × 5 states = 60
Executed/measured: 60; not executed: 0
Candidate FAIL: 2; INCONCLUSIVE: 8
Negative low-contrast button detected: True
Text contrast: 4.5:1 threshold on declared QSS or effective QPalette role colors, NOT rendered text pixels.

## Failed and inconclusive rows
- windows11/light/font_weight/disabled: FAIL LOW_CONTRAST_ROLE_PAIR
- windows11/light/palette/hover: INCONCLUSIVE NOT_RENDERED
- windows11/light/palette/pressed: INCONCLUSIVE NOT_RENDERED
- windows11/dark/palette/hover: INCONCLUSIVE NOT_RENDERED
- windows11/dark/palette/pressed: INCONCLUSIVE NOT_RENDERED
- Fusion/light/font_weight/hover: INCONCLUSIVE NOT_RENDERED
- Fusion/light/font_weight/disabled: FAIL LOW_CONTRAST_ROLE_PAIR
- Fusion/light/palette/hover: INCONCLUSIVE NOT_RENDERED
- Fusion/dark/font_weight/hover: INCONCLUSIVE NOT_RENDERED
- Fusion/dark/palette/hover: INCONCLUSIVE NOT_RENDERED

## Limits
- This compares simulated Qt control painting, not product UI or a physical desktop.
- Qt native QStyle may ignore palette button roles even with a high calculated ratio.
- Synthetic 125%/150% scale is not real Windows Display scaling.
- Actual rendered glyph contrast, human visual clarity and device keyboard/mouse remain unproven.
