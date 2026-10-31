# Agent entrypoint — UI-UX-Test-Lab

This repository contains a Python standard-library **foundation verifier** and one **bounded Windows Qt diagnostic adapter**. It is not a general-purpose UI/UX test engine or production testing platform. Start with the [README](README.md) for context; consult the [foundation contract](docs/FOUNDATION.md) for foundation boundaries, and the [Qt adapter guide](adapters/qt_style_probe/README.md) when working on Qt experiments. Read only the references relevant to the task.

## Scope, ownership, and evidence

- Work within the approved capability; do not invent unrelated adapters, runners, external project execution, governance systems, or releases.
- UI/UX interpretation belongs to the specialist ChatGPT Project; accepted personal preferences belong to [PPDM](https://github.com/rezahh107/Personal-Preference-Decision-Model). This repository owns execution and measurement evidence, not product acceptance.
- Preserve existing files (including `.gitattributes`) and protect credentials and private inputs. Never commit secrets, private test data, or generated `artifacts/` output. Do not rewrite historical `adapters/qt_style_probe/source_probe.py` or the `lab-evidence` branch merely to modernize future experiments.
- For an approved adapter, document real setup, invocation, versions/environment, source versus generated artifacts, reproducible checks, and limitations. Distinguish source inspection, synthetic tests, actual runtime/device execution, and production evidence; never pass synthetic CI off as product usability or visual approval.

## Typography for repository-owned Qt experiments

- Normal Qt Lab experiments use the existing **bundled, unmodified Vazirmatn v33.003 Regular and SemiBold**. Follow the [canonical font contract](assets/fonts/vazirmatn/v33.003/README.md); do not introduce an alternate default, version upgrade, or duplicate loader.
- After constructing `QApplication` and **before** creating normal widgets or capturing evidence, call the shared `adapters.qt_style_probe.font_runtime.initialize_font(app)`. Use its canonical widget-family assertion where applicable. Preserve its fail-closed checks for absent/corrupt assets, failed registration, missing required weights/styles, and unexpected effective families; do not silently substitute OS-installed fonts.
- Explicit, approved font-comparison runs may use other fonts but must label their evidence **non-canonical**. This Qt Lab convention does **not** override typography in browser, WordPress, other-platform, or external target applications: preserve the real target font unless a separate approved experiment changes it.
- Registration and `QFontInfo` family checks do **not** universally prove physical font identity for every glyph or rendering parity across platforms. State what the runtime and captures actually establish.

## Proportional validation and approvals

- For repository changes, run `python3 scripts/verify_foundation.py` (Python 3.10+ and Git). It checks foundation links and tracked/ignored-file hygiene, **not** Qt rendering. [Foundation CI](.github/workflows/foundation.yml) repeats the verifier and Python tests on PRs and `main` pushes.
- Run the relevant tests from `python3 -m unittest discover -s tests -p 'test_*.py' -v` when supported. For Qt behavior changes, also gather applicable PySide6/Windows runtime evidence and retain its environment and limitations; see the [Qt diagnostic workflow](.github/workflows/qt-style-probe.yml), which runs only by its configured triggers or dispatch—not automatically for every feature branch.
- For documentation-only edits, check paths, commands, and the diff, then run foundation verification; do **not** install Qt or run GUI experiments merely to edit Markdown. Report executed checks, skips, blockers, and any **NOT_PROVEN** behavior rather than implying green CI proves visual or product acceptance.
- Submit changes through a reviewed PR. Do not merge, tag, publish, release, or deploy without explicit authorization.

These are agent instructions, **not automatic enforcement**; scripts and CI prove only the checks they actually execute.