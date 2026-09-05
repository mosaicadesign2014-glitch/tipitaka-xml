#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
THERAVĀDA I — PASS C2-B5
Build ONLY slot 25 v3 by:
1) rebuilding the existing TH1 slots 14–25 from the exact pinned VRI commit
   through the already-audited base builder;
2) taking only the rebuilt slot 25;
3) appending a separately-provenanced diplomatic PTS 1915 transcription
   of Rūpārūpavibhāga plus its critical apparatus.

No other TH1 slot is emitted.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile

VRI_COMMIT = "e064d02da2db3df9a7d116a9191092b12e6dfe01"
BASE_BUILDER = Path("scripts/build_th1_slots_14_25.py")
EXPECTED_BASE_BUILDER_SHA256 = "2146648ef2f9fb9409dc6401389260b9a8c59f901bd4ce4b7cdbbcda48e6a115"

DIPLOMATIC = Path("external/ruparupavibhaga/RUPARUPAVIBHAGA_PTS1915_DIPLOMATIC_v1.txt")
APPARATUS = Path("external/ruparupavibhaga/RUPARUPAVIBHAGA_FINAL_APPARATUS_v1.txt")

EXPECTED_DIPLOMATIC_SHA256 = "a4b40ead381ec831a0df96c560de527fbf80cb08f40dad37977a1ea1d75a892f"
EXPECTED_APPARATUS_SHA256 = "d236c26e45bce95aa8e34d2ede0a335534d9895fff72887c4a8c2fbd5b988103"

PTS_PDF_SHA256 = "038337d23ebad13bf6d70b4405f33ccaeaff596896d7e3899e7e15931b59e699"
UPT589_SHA256 = "b2a8b56cc380952a611b4ff3c03be6d802edaf6192a99ac71b41fc5e9d127d8d"

OUTPUT_NAME = "25_ABHIDHAMMA_TIKA_MANUALS.txt"

BASE_SOURCE_FILES = [
    "abh01t.tik.xml", "abh02t.tik.xml", "abh03t.tik.xml",
    "abh04t.nrf.xml", "abh05t.nrf.xml", "abh06t.nrf.xml",
    "abh07t.nrf.xml", "abh08t.nrf.xml",
]

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require_hash(path: Path, expected: str, label: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(
            f"{label} SHA256 mismatch\nexpected: {expected}\nactual:   {actual}"
        )

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vri_repo", help="Pinned checkout of VipassanaTech/tipitaka-xml")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    vri = Path(args.vri_repo).resolve()
    out_dir = Path(args.output).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    require_hash(BASE_BUILDER, EXPECTED_BASE_BUILDER_SHA256, "Base TH1 builder")
    require_hash(DIPLOMATIC, EXPECTED_DIPLOMATIC_SHA256, "Diplomatic PTS text")
    require_hash(APPARATUS, EXPECTED_APPARATUS_SHA256, "Critical apparatus")

    dip = DIPLOMATIC.read_text(encoding="utf-8")
    app = APPARATUS.read_text(encoding="utf-8")

    # Non-negotiable diplomatic gates.
    exact_e = "Upacaya-santatiyo (catūhi ?) jāyantīti vuccanti."
    exact_h = "(Na arūpakasattānaṃ paṭisandhikāle na\nsaddo viyāti (?)."
    if exact_e not in dip:
        raise RuntimeError("E locus is not preserved exactly as required.")
    if exact_h not in dip:
        raise RuntimeError("H locus is not preserved without emendation.")
    if "RŪPĀRŪPAVIBHĀGO NIṬṬHITO." not in dip:
        raise RuntimeError("Rūpārūpavibhāga explicit missing.")

    with tempfile.TemporaryDirectory(prefix="th1-c2b5-") as td:
        base_out = Path(td) / "base"
        subprocess.run(
            [
                sys.executable,
                str(BASE_BUILDER),
                str(vri),
                "--output", str(base_out),
                "--upstream-commit", VRI_COMMIT,
            ],
            check=True,
        )

        base_slot = base_out / OUTPUT_NAME
        if not base_slot.is_file():
            raise RuntimeError("Base slot 25 was not produced.")

        base_text = base_slot.read_text(encoding="utf-8")

    # Protect the old slot-25 composition.
    if base_text.count("BEGIN_SOURCE") != 8:
        raise RuntimeError("Base slot 25 must contain exactly 8 VRI source blocks.")
    for filename in BASE_SOURCE_FILES:
        if f"SOURCE_FILE: romn/{filename}" not in base_text:
            raise RuntimeError(f"Missing old slot-25 source: {filename}")

    sep = "=" * 78
    ext_block = f"""
{sep}
BEGIN_SOURCE
SOURCE_FILE: external/ruparupavibhaga/RUPARUPAVIBHAGA_PTS1915_DIPLOMATIC_v1.txt
WORK: Rūpārūpavibhāga
LAYER_STATUS: POST-CANONICAL ABHIDHAMMA MANUAL — DIPLOMATIC PTS-BASED TEXT
TEXTUAL_STATUS: PTS 1915 DIPLOMATIC BASE WITH EXPLICIT UNRESOLVED APPARATUS
BASE_EDITION: A. P. Buddhadatta (ed.), Buddhadatta's Manuals, Part I, PTS 1915, pp. 149–159
BASE_EDITION_FIRST_PUBLISHED: 1915
BASE_PDF_SHA256: {PTS_PDF_SHA256}
SCRIPT: Roman Pāli
SOURCE_SHA256: {EXPECTED_DIPLOMATIC_SHA256}
APPARATUS_FILE: external/ruparupavibhaga/RUPARUPAVIBHAGA_FINAL_APPARATUS_v1.txt
APPARATUS_SHA256: {EXPECTED_APPARATUS_SHA256}
MANUSCRIPT_CONTROL: UPT589_4F, Myanmar script, fols. 249b–254a
MANUSCRIPT_CONTROL_SHA256: {UPT589_SHA256}
ATTRIBUTION_STATUS: DISPUTED
ATTRIBUTION_NOTE: Conventional/PTS attribution Buddhadatta; some catalogue/traditional evidence attributes the work to Vācissara.
CRITICAL_LOCUS_E: Upacaya-santatiyo (catūhi ?) jāyantīti vuccanti. — UNRESOLVED; PRESERVED AS PTS.
CRITICAL_LOCUS_H: PTS parenthetical clause at end of Rūpavibhāga — UNRESOLVED; NO CONJECTURAL EMENDATION.
NOTE: UPT589_4F is manuscript control only; no word-level Myanmar reading is claimed here.
NOTE: Modern copyrighted control works are not reproduced in this repository.
END_METADATA
{sep}

{dip.rstrip()}

{sep}
BEGIN_CRITICAL_APPARATUS
APPARATUS_FOR: Rūpārūpavibhāga
{sep}

{app.rstrip()}

{sep}
END_CRITICAL_APPARATUS
{sep}
"""

    final_text = base_text.rstrip() + "\n\n" + ext_block.lstrip()
    final_path = out_dir / OUTPUT_NAME
    final_path.write_text(final_text.rstrip() + "\n", encoding="utf-8", newline="\n")

    final = final_path.read_text(encoding="utf-8")
    if final.count("BEGIN_SOURCE") != 9:
        raise RuntimeError("Final slot 25 must contain exactly 9 source blocks.")
    if final.count("SOURCE_FILE: external/ruparupavibhaga/") != 1:
        raise RuntimeError("Expected exactly one external Rūpārūpavibhāga source.")
    if exact_e not in final or exact_h not in final:
        raise RuntimeError("Diplomatic E/H gate failed in final slot.")

    final_sha = sha256(final_path)
    manifest = f"""THERAVĀDA I — PASS C2-B5 MANIFEST
BUILD_DATE: {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}
OUTPUT: {OUTPUT_NAME}
OUTPUT_SHA256: {final_sha}
OUTPUT_BYTES: {final_path.stat().st_size}

VRI_COMMIT: {VRI_COMMIT}
BASE_BUILDER_SHA256: {EXPECTED_BASE_BUILDER_SHA256}

BASE_SLOT25_SOURCE_COUNT: 8
FINAL_SLOT25_SOURCE_COUNT: 9
ADDED_WORK: Rūpārūpavibhāga

DIPLOMATIC_TEXT_SHA256: {EXPECTED_DIPLOMATIC_SHA256}
APPARATUS_SHA256: {EXPECTED_APPARATUS_SHA256}
PTS_PDF_SHA256: {PTS_PDF_SHA256}
UPT589_4F_SHA256: {UPT589_SHA256}

INTEGRITY:
- Old slot 25 is regenerated through the exact audited base builder and pinned VRI commit.
- Exactly one new external source block is appended.
- E is preserved as PTS: Upacaya-santatiyo (catūhi ?) jāyantīti vuccanti.
- H is preserved without conjectural emendation.
- No other TH1 slot is emitted.
"""
    (out_dir / "PASS_C2B5_MANIFEST.txt").write_text(manifest, encoding="utf-8", newline="\n")

    print("PASS C2-B5 BUILD COMPLETE")
    print(final_path)
    print("SHA256:", final_sha)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
