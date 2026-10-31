#!/usr/bin/env python3
"""Standalone, repository-read-only Qt v33.003 vs v32.102 qualification harness.

Requires genuine PySide6-Essentials==6.11.2 and an actual Qt GUI runtime.
This file is NOT a repository change, production adapter, or a simulated Qt test.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys

CANONICAL = {
    "Regular": "b69fd4c680b8f3f225feabcc655a2c585d97627b8f5f5c0f9985e894069f3a56",
    "SemiBold": "3f239d8364c14ee32c46b6839fa197c28958358b82a9673d2c6acc8506d78bc5",
}
COMPETITOR_BLOBS = {
    "Regular": "623537f0ca1bb910120405a2cf216ab6a24fa344",
    "SemiBold": "431dd3ae9be357219a7322de86028593783f4668",
}
FIXTURES = {
    "persian_discriminator": "سی‌سی سیب سی یاس س ی",
    "persian_joining": "سلام فارسی خانه می‌روم نمی‌توانم",
    "arabic": "السلام عليكم س ي يـيِ",
    "latin": "Sample Latin Qt 6 UIUX ABC xyz",
    "digits": "0123456789 ۰۱۲۳۴۵۶۷۸۹ ٠١٢٣٤٥٦٧٨٩",
    "zwnj": "می‌روم نیم‌فاصله می‌توانم",
}
WEIGHTS = ("Regular", "SemiBold")
EXPECTED_HEAD = "30b68a88d9cb6e7d97ef61cc06fa653cd1fc8d4d"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def tables_of(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if len(data) < 12:
        raise ValueError(f"Invalid sfnt: {path}")
    count = struct.unpack_from(">H", data, 4)[0]
    tables = {}
    for i in range(count):
        offset = 12 + i * 16
        tag, _, start, length = struct.unpack_from(">4sIII", data, offset)
        if start + length > len(data):
            raise ValueError(f"Invalid table range in {path}: {tag}")
        tables[tag.decode("ascii")] = data[start:start + length]
    return tables


def verified_paths(repo: Path, competitor: Path) -> tuple[dict, dict, dict]:
    bundled = repo / "assets" / "fonts" / "vazirmatn" / "v33.003"
    paths = {"canonical": {}, "competitor": {}}
    hashes = {}
    for weight in WEIGHTS:
        filename = f"Vazirmatn-{weight}.ttf"
        cur = bundled / filename
        old = competitor / filename
        cur_bytes = cur.read_bytes()
        old_bytes = old.read_bytes()
        if sha(cur_bytes) != CANONICAL[weight]:
            raise RuntimeError(f"Bundled asset SHA-256 mismatch: {cur}")
        if blob_sha(old_bytes) != COMPETITOR_BLOBS[weight]:
            raise RuntimeError(f"Competitor is not official v32.102: {old}")
        paths["canonical"][weight] = cur
        paths["competitor"][weight] = old
        src = tables_of(cur)
        alt = tables_of(old)
        hashes[weight] = {
            "canonical_file_sha256": sha(cur_bytes),
            "competitor_file_sha256": sha(old_bytes),
            "canonical_name_table": sha(src["name"]),
            "competitor_name_table": sha(alt["name"]),
            "canonical_hmtx_table": sha(src["hmtx"]),
            "competitor_hmtx_table": sha(alt["hmtx"]),
            "name_table_discriminating": src["name"] != alt["name"],
            "glyph_table_discriminating": src["glyf"] != alt["glyf"],
            "metrics_table_discriminating": src["hmtx"] != alt["hmtx"],
        }
        if not all((hashes[weight]["name_table_discriminating"],
                    hashes[weight]["glyph_table_discriminating"],
                    hashes[weight]["metrics_table_discriminating"])):
            raise RuntimeError(f"Non-discriminating competitor for {weight}")
    return paths["canonical"], paths["competitor"], hashes


def classify(raw, hashes: dict, weight: str) -> dict:
    name = bytes(raw.fontTable("name"))
    hmtx = bytes(raw.fontTable("hmtx"))
    if not name:
        identity = "UNKNOWN_NO_NAME_TABLE"
    elif sha(name) == hashes[weight]["canonical_name_table"]:
        identity = "BUNDLED_V33_003"
    elif sha(name) == hashes[weight]["competitor_name_table"]:
        identity = "COMPETITOR_V32_102"
    else:
        # A fallback could be a DIFFERENT weight of either font; never claim
        # that it is the expected Regular/SemiBold merely from the family.
        identity = "UNKNOWN_OR_WRONG_WEIGHT"
    return {
        "family": raw.familyName(),
        "style": raw.styleName(),
        "physical_identity_for_expected_weight": identity,
        "name_table_sha256": sha(name) if name else None,
        "hmtx_table_sha256": sha(hmtx) if hmtx else None,
    }


def load_original_loader(repo: Path):
    module_path = repo / "adapters" / "qt_style_probe" / "font_runtime.py"
    spec = importlib.util.spec_from_file_location("qa_original_font_runtime", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the original production loader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_child(args) -> int:
    from PySide6 import __version__ as pyside_version
    from PySide6.QtCore import Qt, qVersion
    from PySide6.QtGui import QFont, QFontDatabase, QFontInfo, QFontMetricsF, QTextLayout, QImage, QRawFont
    from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

    if qVersion() != "6.11.2" or pyside_version != "6.11.2":
        raise RuntimeError(f"Requires Qt/PySide6 6.11.2, actual {qVersion()}/{pyside_version}")
    canonical, competitor, hashes = verified_paths(args.repo, args.competitor)
    app = QApplication([])
    app.setStyle("Fusion")
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    before = "Vazirmatn" in QFontDatabase.families()
    report = {
        "scenario": args.scenario,
        "platform": platform.platform(),
        "python": sys.version,
        "qt": qVersion(),
        "pyside6": pyside_version,
        "qpa": app.platformName(),
        "font_present_before_any_registration": before,
        "font_assets": hashes,
        "competitor_registrations": [],
        "tests": {},
    }
    if args.scenario in ("A", "B") and before:
        raise RuntimeError(f"Invalid {args.scenario} precondition: a system Vazirmatn is already present")
    if args.scenario == "B":
        for weight in WEIGHTS:
            font_id = QFontDatabase.addApplicationFont(str(competitor[weight]))
            families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
            report["competitor_registrations"].append({"weight": weight, "id": font_id, "families": families})
            if font_id < 0 or "Vazirmatn" not in families:
                raise RuntimeError(f"Failed to register competitor {weight}: {families!r}")
    if args.scenario == "C" and not before:
        raise RuntimeError("Scenario C unavailable: no system-installed Vazirmatn precondition")

    # Probe the physical selection before the production loader, not only its
    # family name. For C, a different system version invalidates this fixture.
    report["pre_loader_physical_selection"] = {}
    if args.scenario in ("B", "C"):
        for weight in WEIGHTS:
            test_font = QFont("Vazirmatn", 16)
            test_font.setWeight(QFont.Weight.Normal if weight == "Regular" else QFont.Weight.DemiBold)
            raw = QRawFont.fromFont(test_font)
            report["pre_loader_physical_selection"][weight] = classify(raw, hashes, weight)
        if args.scenario == "C" and any(
            report["pre_loader_physical_selection"][weight]["physical_identity_for_expected_weight"] != "COMPETITOR_V32_102"
            for weight in WEIGHTS
        ):
            raise RuntimeError("Scenario C system-font fixture not independently identified as v32.102 for both weights")

    loader = load_original_loader(args.repo)
    report["production_loader_succeeded"] = False
    try:
        report["production_loader"] = loader.initialize_font(app)
        loader.assert_widget_font(app)
    except loader.FontLoadError as exc:
        report["production_loader_error"] = str(exc)
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / f"{args.scenario}.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return 0  # A successful fail-closed rejection is a measured outcome.
    report["production_loader_succeeded"] = True
    report["qt_styles"] = QFontDatabase.styles("Vazirmatn")
    report["font_present_at_loader_start"] = report["production_loader"]["family_present_before_registration"]

    for weight in WEIGHTS:
        font = QFont("Vazirmatn", 16)
        font.setWeight(QFont.Weight.Normal if weight == "Regular" else QFont.Weight.DemiBold)
        info = QFontInfo(font)
        record = {
            "requested_family": font.family(),
            "requested_weight": int(font.weight()),
            "qfontinfo_family": info.family(),
            "qfontinfo_weight": int(info.weight()),
            "metrics": {},
            "glyph_runs": {},
        }
        host = QWidget()
        host.setObjectName(f"font_collision_{weight}")
        host.setStyleSheet("QWidget { background: white; color: black; } QLabel { background: white; color: black; }")
        host.setFixedWidth(1100)
        vertical = QVBoxLayout(host)
        for key, content in FIXTURES.items():
            metrics = QFontMetricsF(font)
            record["metrics"][key] = {
                "horizontal_advance": round(metrics.horizontalAdvance(content), 5),
                "bounding_width": round(metrics.boundingRect(content).width(), 5),
                "height": round(metrics.height(), 5),
            }
            layout = QTextLayout(content, font)
            layout.beginLayout()
            line = layout.createLine()
            line.setLineWidth(10000)
            layout.endLayout()
            runs = []
            for gr in layout.glyphRuns():
                raw = gr.rawFont()
                if not raw.isValid():
                    raise RuntimeError(f"Invalid raw font {weight}/{key}")
                classified = classify(raw, hashes, weight)
                classified["glyph_indexes"] = list(gr.glyphIndexes())
                classified["positions"] = [[round(p.x(), 4), round(p.y(), 4)] for p in gr.positions()]
                classified["rtl"] = gr.isRightToLeft()
                runs.append(classified)
            record["glyph_runs"][key] = runs
            label = QLabel(content)
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            label.setFont(font)
            loader.assert_widget_font(label)
            label.setFixedSize(1050, 64)
            vertical.addWidget(label)
        host.adjustSize()
        host.show()
        app.processEvents()
        snapshot = host.grab().toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        filename = f"{args.scenario}_{weight}.png"
        if not snapshot.save(str(args.out / filename), "PNG"):
            raise RuntimeError("Could not save PNG " + filename)
        record["widget_grab_png"] = filename
        record["widget_pixels_sha256"] = sha(bytes(snapshot.bits()))
        record["widget_size"] = [snapshot.width(), snapshot.height()]
        record["widget_dpr"] = snapshot.devicePixelRatio()
        record["widget_vs_textlayout_physical_identity_not_directly_proven"] = True
        report["tests"][weight] = record
        host.close()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{args.scenario}.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return 0


def run_parent(args) -> int:
    actual = subprocess.run(["git", "-C", str(args.repo), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    if actual != EXPECTED_HEAD:
        raise RuntimeError(f"Wrong repository checkout: {actual}; expected {EXPECTED_HEAD}")
    dirty = subprocess.run(["git", "-C", str(args.repo), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, check=True).stdout.strip()
    if dirty:
        raise RuntimeError("Repository has modified tracked files; refuse non-canonical loader run")
    args.out.mkdir(parents=True, exist_ok=True)
    _, _, hashes = verified_paths(args.repo, args.competitor)
    results = {"exact_head": actual, "note": "Qt scenarios are separate subprocesses; never equate family equality with file identity", "font_controls": hashes, "scenarios": {}}
    for scenario in args.scenarios:
        command = [sys.executable, str(Path(__file__).resolve()), "--child", "--scenario", scenario,
                   "--repo", str(args.repo), "--competitor", str(args.competitor), "--out", str(args.out)]
        proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90, check=False)
        results["scenarios"][scenario] = {"exit_code": proc.returncode,
            "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-8000:]}
        result_path = args.out / f"{scenario}.json"
        if proc.returncode == 0 and result_path.exists():
            results["scenarios"][scenario]["observations"] = json.loads(result_path.read_text(encoding="utf-8"))
    baseline = results["scenarios"].get("A", {}).get("observations")
    baseline_file = args.out / "A.json"
    if baseline is None and baseline_file.is_file():
        baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
        results["baseline_from_previous_clean_process"] = str(baseline_file)
    for name in ("B", "C"):
        collision = results["scenarios"].get(name, {}).get("observations")
        if (baseline and collision and baseline.get("tests") and collision.get("tests")
                and baseline.get("qt") == collision.get("qt")
                and baseline.get("platform") == collision.get("platform")
                and baseline.get("qpa") == collision.get("qpa")):
            changes = {}
            for weight in WEIGHTS:
                x = baseline["tests"][weight]
                y = collision["tests"][weight]
                changes[weight] = {
                    "widget_pixels_differ": x["widget_pixels_sha256"] != y["widget_pixels_sha256"],
                    "metrics_differ": x["metrics"] != y["metrics"],
                    "glyph_runs_differ": x["glyph_runs"] != y["glyph_runs"],
                    "selected_competitor_in_run": any(
                        g["physical_identity_for_expected_weight"] == "COMPETITOR_V32_102"
                        for runs in y["glyph_runs"].values() for g in runs
                    ),
                }
            results["scenarios"][name]["comparison_to_A"] = changes
    (args.out / "comparison.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if all(item["exit_code"] == 0 for item in results["scenarios"].values()) else 2


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True, help="Unchanged checkout of exact PR #5 HEAD")
    p.add_argument("--competitor", type=Path, required=True, help="Official v32.102 fonts/ttf directory")
    p.add_argument("--out", type=Path, required=True, help="External temporary output directory")
    p.add_argument("--scenarios", nargs="+", choices=("A", "B", "C"), default=("A", "B"))
    p.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--scenario", choices=("A", "B", "C"), help=argparse.SUPPRESS)
    args = p.parse_args()
    args.repo = args.repo.resolve()
    args.competitor = args.competitor.resolve()
    args.out = args.out.resolve()
    if args.child:
        if not args.scenario:
            p.error("--child requires --scenario")
        return run_child(args)
    return run_parent(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"QUALIFICATION BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(3)