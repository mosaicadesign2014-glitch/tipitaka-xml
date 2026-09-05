#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build THERAVĀDA I slots 14–25 from a local checkout/unzipped copy of
VipassanaTech/tipitaka-xml (romn/ Roman-Pāli XML files).

Usage:
    python build_th1_slots_14_25.py /path/to/tipitaka-xml-main

Output:
    TH1_slots_14_25/
        14_VISUDDHIMAGGA_CLASSICAL.txt
        ...
        25_ABHIDHAMMA_TIKA_MANUALS.txt
        BUILD_MANIFEST.txt

The script does NOT modify slots 01–13 and does NOT change the source XML files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

EDITION = "Chaṭṭha Saṅgāyana Tipiṭaka (CST)"
PROVIDER = "Vipassana Research Institute / Tipitaka.org"
UPSTREAM = "https://github.com/VipassanaTech/tipitaka-xml"
SCRIPT = "Roman Pāli"

SLOTS = {
    "14_VISUDDHIMAGGA_CLASSICAL.txt": [
        "e0101n.mul.xml", "e0102n.mul.xml", "e0103n.att.xml", "e0104n.att.xml",
    ],
    "15_VINAYA_ATTHAKATHA.txt": [
        "vin01a.att.xml", "vin02a1.att.xml", "vin02a2.att.xml", "vin02a3.att.xml", "vin02a4.att.xml",
    ],
    "16_DN_ATTHAKATHA.txt": [
        "s0101a.att.xml", "s0102a.att.xml", "s0103a.att.xml",
    ],
    "17_MN_ATTHAKATHA.txt": [
        "s0201a.att.xml", "s0202a.att.xml", "s0203a.att.xml",
    ],
    "18_SN_ATTHAKATHA.txt": [
        "s0301a.att.xml", "s0302a.att.xml", "s0303a.att.xml", "s0304a.att.xml", "s0305a.att.xml",
    ],
    "19_AN_ATTHAKATHA.txt": [
        "s0401a.att.xml", "s0402a.att.xml", "s0403a.att.xml", "s0404a.att.xml",
    ],
    "20_KN_ATTHAKATHA_I.txt": [
        "s0501a.att.xml", "s0502a.att.xml", "s0503a.att.xml", "s0504a.att.xml", "s0505a.att.xml",
        "s0506a.att.xml", "s0507a.att.xml", "s0508a1.att.xml", "s0508a2.att.xml", "s0509a.att.xml",
    ],
    "21_KN_ATTHAKATHA_II.txt": [
        "s0510a.att.xml", "s0511a.att.xml", "s0512a.att.xml",
        "s0513a1.att.xml", "s0513a2.att.xml", "s0513a3.att.xml", "s0513a4.att.xml",
        "s0514a1.att.xml", "s0514a2.att.xml", "s0514a3.att.xml",
        "s0515a.att.xml", "s0516a.att.xml", "s0517a.att.xml", "s0519a.att.xml",
    ],
    "22_ABHIDHAMMA_ATTHAKATHA.txt": [
        "abh01a.att.xml", "abh02a.att.xml", "abh03a.att.xml",
    ],
    "23_SUTTA_NETTI_TIKA.txt": [
        "s0101t.tik.xml", "s0102t.tik.xml", "s0103t.tik.xml",
        "s0201t.tik.xml", "s0202t.tik.xml", "s0203t.tik.xml",
        "s0301t.tik.xml", "s0302t.tik.xml", "s0303t.tik.xml", "s0304t.tik.xml", "s0305t.tik.xml",
        "s0401t.tik.xml", "s0402t.tik.xml", "s0403t.tik.xml", "s0404t.tik.xml",
        "s0519t.tik.xml", "s0501t.nrf.xml", "e1210n.nrf.xml", "s0104t.nrf.xml", "s0105t.nrf.xml",
    ],
    "24_VINAYA_TIKA_MANUALS.txt": [
        "vin01t1.tik.xml", "vin01t2.tik.xml", "vin02t.tik.xml",
        "vin05t.nrf.xml", "vin06t.nrf.xml", "vin07t.nrf.xml", "vin08t.nrf.xml", "vin09t.nrf.xml",
        "vin10t.nrf.xml", "vin11t.nrf.xml", "vin12t.nrf.xml", "vin13t.nrf.xml", "e1102n.nrf.xml",
    ],
    "25_ABHIDHAMMA_TIKA_MANUALS.txt": [
        "abh01t.tik.xml", "abh02t.tik.xml", "abh03t.tik.xml",
        "abh04t.nrf.xml", "abh05t.nrf.xml", "abh06t.nrf.xml", "abh07t.nrf.xml", "abh08t.nrf.xml",
    ],
}

# Historical/research layer labels. These deliberately do not merely copy VRI filename suffixes.
EXPLICIT_LAYER = {
    "e0101n.mul.xml": "POST-CANONICAL / SYSTEMATIC — VISUDDHIMAGGA",
    "e0102n.mul.xml": "POST-CANONICAL / SYSTEMATIC — VISUDDHIMAGGA",
    "e0103n.att.xml": "ṬĪKĀ — VISUDDHIMAGGA-MAHĀṬĪKĀ / PARAMATTHAMAÑJŪSĀ",
    "e0104n.att.xml": "ṬĪKĀ — VISUDDHIMAGGA-MAHĀṬĪKĀ / PARAMATTHAMAÑJŪSĀ",
    "s0501t.nrf.xml": "LATE ṬĪKĀ / NETTI EXEGESIS — NETTIVIBHĀVINĪ",
    "e1210n.nrf.xml": "ṬĪKĀ / MILINDA EXEGESIS — MILINDAṬĪKĀ",
    "s0104t.nrf.xml": "ABHINAVAṬĪKĀ / LATE",
    "s0105t.nrf.xml": "ABHINAVAṬĪKĀ / LATE",
    "vin05t.nrf.xml": "POST-CANONICAL VINAYA COMPENDIUM / EXEGESIS",
    "vin06t.nrf.xml": "ṬĪKĀ — VINAYA EXEGESIS",
    "vin07t.nrf.xml": "ṬĪKĀ — VINAYA EXEGESIS",
    "vin08t.nrf.xml": "ṬĪKĀ — VINAYA EXEGESIS",
    "vin09t.nrf.xml": "ṬĪKĀ — VINAYA EXEGESIS",
    "vin10t.nrf.xml": "POST-CANONICAL VINAYA MANUAL",
    "vin11t.nrf.xml": "ṬĪKĀ — VINAYA EXEGESIS",
    "vin12t.nrf.xml": "YOJANĀ / VINAYA EXEGESIS",
    "vin13t.nrf.xml": "POST-CANONICAL VINAYA MANUALS",
    "e1102n.nrf.xml": "POST-CANONICAL VINAYA TREATISE — SĪMĀ",
    "abh04t.nrf.xml": "ANUṬĪKĀ — ABHIDHAMMA",
    "abh05t.nrf.xml": "ANUṬĪKĀ — ABHIDHAMMA",
    "abh06t.nrf.xml": "POST-CANONICAL ABHIDHAMMA MANUAL — COMMENTARIAL ERA",
    "abh07t.nrf.xml": "POST-CANONICAL ABHIDHAMMA MANUAL — MEDIEVAL",
    "abh08t.nrf.xml": "ṬĪKĀ — ABHIDHAMMA MANUAL",
}

STRUCT_MARKERS = {
    "nikaya": "NIKĀYA",
    "book": "BOOK",
    "chapter": "CHAPTER",
    "title": "TITLE",
    "subhead": "SUBHEAD",
    "subsubhead": "SUBSUBHEAD",
}


def layer_for(filename: str) -> str:
    if filename in EXPLICIT_LAYER:
        return EXPLICIT_LAYER[filename]
    if filename.endswith(".att.xml"):
        return "AṬṬHAKATHĀ"
    if filename.endswith(".tik.xml"):
        return "ṬĪKĀ"
    if filename.endswith(".nrf.xml"):
        return "POST-CANONICAL / ANCILLARY PĀLI"
    if filename.endswith(".mul.xml"):
        return "MŪLA / TECHNICAL VRI CATEGORY — SEE WORK-LEVEL STATUS"
    return "UNCLASSIFIED"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_inline(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[\t\r\n ]+", " ", s)
    return s.strip()


def render_element(el: ET.Element) -> str:
    """Render inline XML while preserving VRI page refs and notes as searchable markers."""
    tag = el.tag.split("}")[-1]
    out = el.text or ""
    for child in list(el):
        ctag = child.tag.split("}")[-1]
        if ctag == "pb":
            ed = child.attrib.get("ed", "?")
            n = child.attrib.get("n", "?")
            piece = f" ⟦PB:{ed}:{n}⟧ "
        elif ctag == "note":
            note_text = normalize_inline("".join(child.itertext()))
            piece = f" ⟦NOTE:{note_text}⟧ " if note_text else ""
        elif ctag in {"lb", "br"}:
            piece = "\n"
        else:
            piece = render_element(child)
        out += piece
        if child.tail:
            out += child.tail
    return out


def parse_xml(path: Path):
    raw = path.read_bytes()
    digest = sha256_bytes(raw)
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        raise RuntimeError(f"XML parse failed for {path.name}: {e}") from e

    paragraphs = []
    work_candidates = []
    for p in root.iter():
        if p.tag.split("}")[-1] != "p":
            continue
        rend = p.attrib.get("rend", "bodytext")
        text = normalize_inline(render_element(p))
        if not text:
            continue
        marker = STRUCT_MARKERS.get(rend)
        if marker:
            line = f"⟦{marker}⟧ {text}"
            if rend in {"book", "title", "chapter", "nikaya"}:
                work_candidates.append(text)
        else:
            line = text
        paragraphs.append(line)

    work = work_candidates[0] if work_candidates else path.stem
    return raw, digest, len(paragraphs), work, paragraphs


def source_block(repo_root: Path, filename: str) -> tuple[str, dict]:
    path = repo_root / "romn" / filename
    raw, digest, pcount, work, paragraphs = parse_xml(path)
    layer = layer_for(filename)

    meta = {
        "source_file": f"romn/{filename}",
        "work": work,
        "layer": layer,
        "sha256": digest,
        "paragraphs": pcount,
        "bytes": len(raw),
    }

    sep = "=" * 78
    lines = [
        sep,
        "BEGIN_SOURCE",
        f"SOURCE_FILE: romn/{filename}",
        f"WORK: {work}",
        f"LAYER_STATUS: {layer}",
        f"EDITION: {EDITION}",
        f"PROVIDER: {PROVIDER}",
        f"SCRIPT: {SCRIPT}",
        f"SOURCE_SHA256: {digest}",
        f"XML_PARAGRAPHS: {pcount}",
        "NOTE: VRI filename suffix is a technical repository category; LAYER_STATUS is work-level research classification.",
        "END_METADATA",
        sep,
        "",
    ]
    lines.extend(paragraphs)
    lines.extend(["", ""])
    return "\n".join(lines), meta


def validate(repo_root: Path) -> list[str]:
    all_files = [f for files in SLOTS.values() for f in files]
    duplicates = sorted({f for f in all_files if all_files.count(f) > 1})
    if duplicates:
        raise RuntimeError("Duplicate source files across slots: " + ", ".join(duplicates))

    missing = [f for f in all_files if not (repo_root / "romn" / f).is_file()]
    return missing


def human_mb(n: int) -> str:
    return f"{n / 1024 / 1024:.2f} MB"


def main() -> int:
    ap = argparse.ArgumentParser(description="Build THERAVĀDA I slots 14–25 from VRI Roman-Pāli XML.")
    ap.add_argument("repo", help="Path to unzipped/cloned VipassanaTech/tipitaka-xml repository")
    ap.add_argument("--output", default=None, help="Output folder (default: <repo>/TH1_slots_14_25)")
    ap.add_argument("--upstream-commit", default="UNKNOWN", help="Optional Git commit SHA for provenance")
    args = ap.parse_args()

    repo_root = Path(args.repo).expanduser().resolve()
    if not (repo_root / "romn").is_dir():
        print(f"ERROR: romn/ folder not found under: {repo_root}", file=sys.stderr)
        return 2

    missing = validate(repo_root)
    if missing:
        print("ERROR: required XML files are missing:", file=sys.stderr)
        for f in missing:
            print("  -", f, file=sys.stderr)
        print("\nMake sure you downloaded the complete current repository and did not rename files.", file=sys.stderr)
        return 3

    out_dir = Path(args.output).expanduser().resolve() if args.output else repo_root / "TH1_slots_14_25"
    out_dir.mkdir(parents=True, exist_ok=True)

    build_date = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    manifest_lines = [
        "THERAVĀDA I — BUILD MANIFEST FOR SLOTS 14–25",
        f"BUILD_DATE: {build_date}",
        f"UPSTREAM: {UPSTREAM}",
        f"UPSTREAM_COMMIT: {args.upstream_commit}",
        f"EDITION: {EDITION}",
        f"PROVIDER: {PROVIDER}",
        "RULE: source XML is read-only; slots 01–13 are not touched.",
        "RULE: VRI filename suffixes are not treated as historical layer labels.",
        "",
    ]

    total_sources = 0
    for slot_name, source_files in SLOTS.items():
        print(f"Building {slot_name} ({len(source_files)} source files)...")
        header = [
            "THERAVĀDA RESEARCH CORPUS",
            f"FILE: {slot_name}",
            f"EDITION: {EDITION}",
            "WORKING SOURCE: VRI Roman-Pāli XML (romn/)",
            f"UPSTREAM: {UPSTREAM}",
            f"UPSTREAM_COMMIT: {args.upstream_commit}",
            "IMPORTANT: Metadata markers are editorial; source text follows each source block.",
            "IMPORTANT: Historical LAYER_STATUS is assigned at work level, not inferred mechanically from .mul/.att/.tik/.nrf.",
            "",
            "",
        ]
        blocks = []
        slot_meta = []
        for f in source_files:
            block, meta = source_block(repo_root, f)
            blocks.append(block)
            slot_meta.append(meta)
            total_sources += 1

        content = "\n".join(header + blocks).rstrip() + "\n"
        out_path = out_dir / slot_name
        out_path.write_text(content, encoding="utf-8", newline="\n")
        out_sha = sha256_bytes(out_path.read_bytes())
        manifest_lines.append(f"SLOT: {slot_name}")
        manifest_lines.append(f"OUTPUT_SHA256: {out_sha}")
        manifest_lines.append(f"OUTPUT_SIZE: {human_mb(out_path.stat().st_size)}")
        manifest_lines.append(f"SOURCE_COUNT: {len(slot_meta)}")
        for m in slot_meta:
            manifest_lines.append(
                f"  - {m['source_file']} | {m['layer']} | sha256={m['sha256']} | paragraphs={m['paragraphs']}"
            )
        manifest_lines.append("")

    manifest_path = out_dir / "BUILD_MANIFEST.txt"
    manifest_path.write_text("\n".join(manifest_lines).rstrip() + "\n", encoding="utf-8", newline="\n")

    print("\nDONE")
    print(f"Output folder: {out_dir}")
    print(f"Created 12 slot files from {total_sources} source XML files.")
    print("Also created BUILD_MANIFEST.txt for provenance/checksums (do not upload it as a TH1 source slot unless you explicitly want metadata searchable).")
    print("\nUpload ONLY the 12 files numbered 14–25 to Theravāda I. Keep existing slots 01–13 unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
