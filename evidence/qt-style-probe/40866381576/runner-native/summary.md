# Qt Widgets diagnostic — runner-native

Source: Bank2Odoo diagnostic probe 1bfc65b4bfdbac60efabf6957e2a5d558ef9c86b
Lab feature commit: 873b2d47e69e22442c30cae91f2d76abe6e0dbbd
OS: Windows-2025Server-10.0.26100-SP0
QPA: windows
Scale: runner_native_unverified / QT_SCALE_FACTOR=None
Capture: Qt widget.grab(), not physical desktop
Candidate states: 80
EXECUTED/MEASURED: 80
NOT_EXECUTED/NOT_MEASURED: 0
Semantic FAIL: 0
NOT_RENDERED states: 16
Low-contrast negative control: DETECTED

## Missing visual changes

- windows11_baseline / focus
- windows11_palette / focus
- windows11_card_qss / focus
- windows11_palette_card_qss / focus
- fusion_baseline / focus
- fusion_baseline / hover
- fusion_baseline / checked
- fusion_palette / focus
- fusion_palette / hover
- fusion_palette / checked
- fusion_card_qss / focus
- fusion_card_qss / hover
- fusion_card_qss / checked
- fusion_palette_card_qss / focus
- fusion_palette_card_qss / hover
- fusion_palette_card_qss / checked

## Limitations
- Runner-native DPI is not proven equivalent to 100% Windows display scaling.
- QT_SCALE_FACTOR is synthetic, not a real 125%/150% Windows desktop setting.
- PASS only covers probe measurements/semantics; no accountant/device acceptance.
- QTest events are simulated, not human input. Review contact sheets visually.
