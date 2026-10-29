# Qt Widgets diagnostic — synthetic-125

Source: Bank2Odoo diagnostic probe 1bfc65b4bfdbac60efabf6957e2a5d558ef9c86b
Lab feature commit: 0fcee70fd6e9b17c67c82e570b5a37c7bcfe392d
OS: Windows-2025Server-10.0.26100-SP0
QPA: windows
Scale: synthetic_QT_SCALE_FACTOR / QT_SCALE_FACTOR=1.25
Capture: Qt widget.grab(), not physical desktop
Candidate states: 80
EXECUTED/MEASURED: 80
NOT_EXECUTED/NOT_MEASURED: 0
Semantic FAIL: 0
NOT_RENDERED states: 5
Low-contrast negative control: DETECTED
Candidate low role contrast (<4.5): windows11_card_qss, fusion_card_qss
Window larger than logical screen: 
Widgets outside host bounds: windows11_baseline, windows11_palette, windows11_card_qss, windows11_palette_card_qss, fusion_baseline, fusion_palette, fusion_card_qss, fusion_palette_card_qss

## Missing visual changes

- windows11_card_qss / hover
- fusion_baseline / hover
- fusion_palette / hover
- fusion_card_qss / hover
- fusion_palette_card_qss / hover

## Limitations
- Runner-native DPI is not proven equivalent to 100% Windows display scaling.
- QT_SCALE_FACTOR is synthetic, not a real 125%/150% Windows desktop setting.
- PASS only covers probe measurements/semantics; no accountant/device acceptance.
- QTest events are simulated, not human input. Review contact sheets visually.
