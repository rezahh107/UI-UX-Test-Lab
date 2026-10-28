# UI-UX-Test-Lab

**Status: foundation only.** No GUI, browser, WordPress, rendering, screenshot, or visual-measurement runner is implemented.

This repository will hold **reusable execution and measurement tools** for a separate specialist ChatGPT UI/UX Project. It is intended to produce reproducible evidence, not UI/UX design judgments.

## Ownership boundaries

- **Specialist ChatGPT Project:** UI/UX reasoning, assessment, and recommendations.
- **This repository:** future test adapters, executable checks, measurements, and evidence production.
- **[PPDM](https://github.com/rezahh107/Personal-Preference-Decision-Model):** accepted personal preferences and transferable lessons, not runtime lab configuration.

A measured result does not by itself prove usability, visual quality, or production behavior. Simulated results must identify their environment and limitations.

## Start here

Prerequisites for the **existing foundation only**: Git and Python 3.10+ (standard library; no package installation). From a checkout, run:

```sh
python3 scripts/verify_foundation.py
```

On Windows, `py -3 scripts/verify_foundation.py` is an equivalent invocation if the Python launcher is installed. A successful run checks local documentation links, tracked-file hygiene, and representative ignore rules. It does **not** test a UI/UX application. See [foundation verification and limits](docs/FOUNDATION.md).

## Repository map

- [Foundation contract and extension boundaries](docs/FOUNDATION.md): current verification and future integration principles.
- [Agent instructions](AGENTS.md): concise instructions for AI-assisted changes.
- [Foundation verifier](scripts/verify_foundation.py): the single local/CI verification implementation.
- [Foundation CI](.github/workflows/foundation.yml): repeats the verifier on changes; does not run third-party projects.
- `.gitattributes`, `.editorconfig`, `.gitignore`: version-control, editor, and local-artifact hygiene.

No application dependencies, build stages, test fixtures, release procedure, or platform-specific test environments exist yet. Add them only alongside an approved, working capability and its actual verification path.
