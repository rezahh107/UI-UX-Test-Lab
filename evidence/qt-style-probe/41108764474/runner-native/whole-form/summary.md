# Synthetic dark-palette whole-form + approval-checkbox qualification
Source head: 2ad93426b010d9dd177e28124ded9bf42a931348; scale: runner-native
Styles: ('windows11', 'Fusion'); installed fonts: ['Tahoma']; unavailable: ['Vazirmatn']
Expected rows: 60
Executed: 60; not executed: 0; assessments: {'PASS': 20, 'FAIL': 0, 'INCONCLUSIVE': 40}
Malformed ZWNJ control distinguished: True
Low-indicator-contrast declared control detected: True
Low-indicator Qt pixel contrast: True; declared/rendered agreement: True
## Per-candidate indicator evidence
- windows11_tahoma_native: unchecked=False (max 1.1:1, fraction 0.0), checked=True, distinct=True, font=Tahoma
- windows11_tahoma_checkbox_palette: unchecked=False (max 1.173:1, fraction 0.0), checked=True, distinct=True, font=Tahoma
- windows11_tahoma_unchecked_border: unchecked=True (max 13.925:1, fraction 0.4375), checked=True, distinct=True, font=Tahoma
- fusion_tahoma_native: unchecked=False (max 1.173:1, fraction 0.0), checked=True, distinct=True, font=Tahoma
- fusion_tahoma_checkbox_palette: unchecked=False (max 1.173:1, fraction 0.0), checked=True, distinct=True, font=Tahoma
- fusion_tahoma_unchecked_border: unchecked=True (max 13.925:1, fraction 0.4898), checked=True, distinct=True, font=Tahoma
## Limits
- Full PNGs are Qt widget grabs; contact sheets are resized previews.
- QPalette role contrast is not font/glyph pixel contrast.
- Only installed fonts are tested, per-glyph fallback not established.
- Native Windows 11 hardware and physical 100/125/150% scale are NOT_PROVEN.
- This is synthetic Lab evidence, not Bank2Odoo product acceptance.
