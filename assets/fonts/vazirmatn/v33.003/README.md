# Canonical Qt font: original Vazirmatn v33.003

Normal Lab Qt runs use the two **unmodified standard static TTFs** from the
[official v33.003 release](https://github.com/rastikerdar/vazirmatn/releases/tag/v33.003),
upstream annotated tag `f68f7bc5dd1d046bd6a5a2bda355bd6d430e807a`
(commit `83629f877e8f084cc07b47030b5d3a0ff06c76ec`), `fonts/ttf/`.
Not Rounded, Variable, Non-Latin, or Persian-Digits-only variants.

| Bundled asset | Verified binary SHA-256 |
| --- | --- |
| `Vazirmatn-Regular.ttf` | `b69fd4c680b8f3f225feabcc655a2c585d97627b8f5f5c0f9985e894069f3a56` |
| `Vazirmatn-SemiBold.ttf` | `3f239d8364c14ee32c46b6839fa197c28958358b82a9673d2c6acc8506d78bc5` |

Original `OFL.txt` contains copyright and SIL **Open Font License 1.1**.
The copyright notice and license accompany redistribution; the unmodified
font files are not sold separately. SemiBold supports the existing primary
button's Qt DemiBold weight treatment; no unrelated weight is bundled.

## Initialization and fail-closed semantics

Create `QApplication` and **before** creating any widgets or screenshots call:

```python
from adapters.qt_style_probe import font_runtime
font_metadata = font_runtime.initialize_font(app, point_size=11)
```

This shared helper uses an absolute asset directory derived from `__file__`
(not process CWD), checks actual file bytes against the SHA-256 values, calls
`QFontDatabase.addApplicationFont` and verifies `applicationFontFamilies`,
the exposed Regular/SemiBold styles and weights, and the effective application
family using `QFontInfo`. It sets app.font() to canonical Vazirmatn.
Normal host widgets must pass `font_runtime.assert_widget_font(widget)`;
wrong requested/effective family, missing/invalid file, bad weight, or failed
Qt registration raises `FontLoadError` rather than falling back to installed
Tahoma, Arial, Segoe UI or an unspecified application font.

`environment.json` for each experiment includes `canonical_font`:
upstream URL, version, binary checksums, Qt styles, weights, pre-registration
family presence and effective family. All four normal entrypoints share this:

```sh
python -m adapters.qt_style_probe.lab_runner --output artifacts/probe --scale-tag local
python -m adapters.qt_style_probe.primary_action --output artifacts/primary --scale-tag local
python -m adapters.qt_style_probe.whole_form --output artifacts/whole --scale-tag local
python -m adapters.qt_style_probe.approval_equivalence --output artifacts/equivalent --scale-tag local
```

`whole_form` and `approval_equivalence` also accept
`--compare-tahoma`, explicitly **non-default system-font comparisons**.
Tahoma availability is not guaranteed and these comparisons cannot qualify as
canonical execution. The integrity-protected `source_probe.py` is a read-only
upstream historical reference, not a supported Lab normal entrypoint; it is
not edited or used directly as canonical evidence. Future Qt adapters should
reuse this single initializer, not implement another font-priority chain.

The existing Windows CI runs a preflight
`python -m adapters.qt_style_probe.font_runtime --require-system-absent`
before the suite. If the runner already has Vazirmatn in its Qt font database,
that preflight **fails** rather than falsely claiming absence of OS dependency.
Otherwise successful registration proves that this checkout works on a
Windows runner without Vazirmatn preinstalled. Tests cover bad/missing fonts,
failed registration, wrong family, and substitution.

Historical `lab-evidence` remains untouched and new runs are captured
under new run IDs. `QFontInfo`, family registration and screenshot pixel
measurements do **not** establish per-glyph font fidelity, perceptual Persian
readability, physical Windows display scaling, or end-user/product acceptance.
Unavailable Windows11 style is NOT_EXECUTED rather than silently replaced.
