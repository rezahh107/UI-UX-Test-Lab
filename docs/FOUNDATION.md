# Foundation contract

## Current implementation

The repository currently contains documentation, agent guidance, file-hygiene configuration, and a Python-standard-library foundation verifier. There is **no UI/UX testing engine**. No user interface, web browser, WordPress site, Qt desktop, or external project is launched by foundation verification.

## Verification

Run `python3 scripts/verify_foundation.py` at any location within a Git checkout with Python 3.10+ and Git installed. The script resolves its repository root from its own file path, so the shell working directory is not significant.

The command fails (non-zero exit) when any of these contracts fail:

1. Tracked Markdown files contain simple relative Markdown links pointing to missing files/directories or outside the repository. External URLs and fragment-only links are not checked; heading anchors and non-Markdown references are not checked.
2. Tracked paths are forbidden by the effective **tracked** `.gitignore` policy, using Git semantics for nested paths, directories, globs, and negation exceptions. User-global excludes, local `.git/info/exclude`, and untracked `.gitignore` files do not define repository policy. This is a path-hygiene check, **not** secret-content detection.
3. Representative local credential, cache and generated-output paths are not ignored by Git, or `.env.example` is accidentally ignored.

The command and focused standard-library regression tests (`python3 -m unittest discover -s tests -p "test_*.py" -v`) run in [foundation CI](../.github/workflows/foundation.yml) on pull requests and pushes to `main`. The workflow explicitly checks out the pull-request **head commit** (not GitHub’s synthetic merge ref) and prints the checked-out SHA. CI has read-only contents permission and does not provision test subjects, install project dependencies, or execute external targets. A successful check establishes only these foundation invariants at the tested commit; it does not establish platform/device/production usability.

## Future implementation boundaries (not implemented)

When an approved need first appears, introduce the smallest working adapter and its tests rather than pre-creating empty systems:

- **Desktop GUI:** explicitly record the OS, desktop/session type, Qt/PySide6 versions and whether a real display or simulation was exercised.
- **Browser:** identify browser/runtime versions, viewport, interaction paths and measurement provenance.
- **WordPress/Elementor:** distinguish owned integration code from host behavior; identify installed versions and site/environment scope.
- **Measurements:** define units, collection method and limitations; distinguish deterministic geometry/color/contrast readings from subjective UI/UX assessment.
- **Evidence:** retain reproducible target identity, environment, procedure, results, artifacts, and limitations in a reviewed per-capability format. Generated local output belongs under ignored `artifacts/` by default; curated non-sensitive fixtures can be committed deliberately outside it after review.

Never execute arbitrary third-party projects solely because a pull request or incoming file asks for it. External test execution, privileged credentials, self-hosted runners and expanded workflow permissions require a separate safety and applicability review. Do not commit real secrets, user content, or production screenshots without authorization.

The specialist ChatGPT UI/UX Project remains the decision authority for interpretation; this repository records measurements and their provenance. PPDM remains the authority for accepted preferences. None of these boundaries turn automatic measurements into human acceptance.
