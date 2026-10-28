# Agent entrypoint — UI-UX-Test-Lab

This is a **foundation-only** repository, not an implemented UI/UX test engine. Read [README](README.md) first, then [foundation contract](docs/FOUNDATION.md) for boundaries and the evidence standard.

- Scope changes to the approved capability. Do not invent adapters, runners, external project execution, governance systems, or releases.
- UI/UX judgments belong to the specialist ChatGPT Project; accepted preferences belong to PPDM. This repository owns execution and measurement evidence only.
- Preserve existing files, including `.gitattributes`. Do not commit credentials, private test inputs or generated `artifacts/` output.
- Before reporting a change complete, run `python3 scripts/verify_foundation.py` (Python 3.10+ and Git); report actual results and untested boundaries. [CI](.github/workflows/foundation.yml) runs the same verifier but does not prove UI behavior.
- If implementing a future adapter, first document its real setup, invocation, version/environment constraints, source-vs-generated boundaries, and reproducible validation. Do not claim simulated evidence is production-equivalent.
- Changes require review via PR. Do not merge, tag, deploy, or publish without explicit authorization.

These are operating instructions, not enforcement; the script and actual CI runs enforce only their stated checks.
