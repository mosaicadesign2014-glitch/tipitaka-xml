#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
THERAVĀDA I — Pass C2-A
Build only slot 15 (Vinaya Aṭṭhakathā) from two pinned upstream checkouts:

1) Official VRI CST Roman-Pāli XML:
   VipassanaTech/tipitaka-xml
   pinned commit: e064d02da2db3df9a7d116a9191092b12e6dfe01

2) J.R. Bhaddacak cst-kit:
   bhaddacak/cst-kit
   pinned commit: cc0bab5fdf378d01deb3649112c0a9fddc317283
   Kaṅkhāvitaraṇī raw XML licensed CC BY-SA 4.0

Output:
  15_VINAYA_ATTHAKATHA.txt
  PASS_C2A_MANIFEST.txt

The script rebuilds the existing five Samantapāsādikā source blocks
and appends the two Kaṅkhāvitaraṇī books.
It does not create or modify any other TH1 slot.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

EDITION = "Chaṭṭha Saṅgāyana Tipiṭaka (CST)"
SCRIPT = "Roman Pāli"

VRI_UPSTREAM = "https://github.com/VipassanaTech/tipitaka-xml"
VRI_COMMIT = "e064d02da2db3df9a7d116a9191092b12e6dfe01"
VRI_PROVIDER = "Vipassana Research Institute / Tipitaka.org"

CSTKIT_UPSTREAM = "https://github.com/bhaddacak/cst-kit"
CSTKIT_COMMIT = "cc0bab5fdf378d01deb3649112c0a9fddc317283"
CSTKIT_PROVIDER = "J.R. Bhaddacak / cst-kit; original CST data from Tipitaka.org"
CSTKIT_LICENSE = "CC BY-SA 4.0"

OUTPUT_NAME = "15_VINAYA_ATTHAKATHA.txt"

VRI_FILES = [
    "vin01a.att.xml",
    "vin02a1.att.xml",
    "vin02a2.att.xml",
    "vin02a3.att.xml",
    "vin02a4.att.xml",
]

# These are the SHA256 values already present in the audited TH1 slot 15.
# If the pinned VRI checkout does not match them, the build must stop.
EXPECTED_VRI_SHA256 = {
    "vin01a.att.xml": "7ac2797c216e85221ed57ca70e2bcab5dac8e77bdc393b5e3a85b0c10dcf459a",
    "vin02a1.att.xml": "602a057db7f0ca5f8ff55c253510db89fe4f4a5ebc40633c85552ff1eeae3e5b",
    "vin02a2.att.xml": "b50971a3f9216e6da5b6a38d295a405fa67f92461d64f529f7ca2024acda9309",
    "vin02a3.att.xml": "655d7cfa0fd3e26d3a2cf07fb5dfdad4e1f7ee359689afcb05da002528bb602c",
    "vin02a4.att.xml": "9ee4b7f3a5023f873252da0967ba13f88dd0923d5525a92c21735f9d6ba62db2",
}

CSTKIT_FILES = [
    ("cst-ve-kkh1.xml", "Kaṅkhāvitaraṇī — Bhikkhupātimokkhavaṇṇanā"),
    ("cst-ve-kkh2.xml", "Kaṅkhāvitaraṇī — Bhikkhunīpātimokkhavaṇṇanā"),
]

STRUCT_MARKERS = {
    "nikaya": "NIKĀYA",
    "book": "BOOK",
    "chapter": "CHAPTER",
    "title": "TITLE",
    "subhead": "SUBHEAD",
    "subsubhead": "SUBSUBHEAD",
    # cst-kit sometimes uses "strong" for a structural heading.
    "strong": "SUBSUBHEAD",
}

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def normalize_inline(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[\t\r\n ]+", " ", s)
    return s.strip()

def render_element(el: ET.Element) -> str:
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
        raise RuntimeError(f"XML parse failed for {path}: {e}") from e

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

def make_vri_block(vri_root: Path, filename: str):
    path = vri_root / "romn" / filename
    raw, digest, pcount, work, paragraphs = parse_xml(path)

    expected = EXPECTED_VRI_SHA256[filename]
    if digest != expected:
        raise RuntimeError(
            f"VRI SHA256 mismatch for {filename}\n"
            f"expected: {expected}\n"
            f"actual:   {digest}\n"
            "STOP: the reconstructed Samantapāsādikā would not match audited slot 15 sources."
        )

    sep = "=" * 78
    lines = [
        sep,
        "BEGIN_SOURCE",
        f"SOURCE_FILE: romn/{filename}",
        f"WORK: {work}",
        "LAYER_STATUS: AṬṬHAKATHĀ",
        f"EDITION: {EDITION}",
        f"PROVIDER: {VRI_PROVIDER}",
        f"UPSTREAM: {VRI_UPSTREAM}",
        f"UPSTREAM_COMMIT: {VRI_COMMIT}",
        f"SCRIPT: {SCRIPT}",
        f"SOURCE_SHA256: {digest}",
        f"XML_PARAGRAPHS: {pcount}",
        "NOTE: Existing Samantapāsādikā block; SHA256 locked against the audited TH1 slot 15 source metadata.",
        "END_METADATA",
        sep,
        "",
        *paragraphs,
        "",
        "",
    ]
    meta = (f"romn/{filename}", "Samantapāsādikā / Vinaya Aṭṭhakathā", digest, pcount, len(raw))
    return "\n".join(lines), meta

def make_cstkit_block(cstkit_root: Path, filename: str, explicit_work: str):
    path = cstkit_root / "raw" / filename
    raw, digest, pcount, _detected_work, paragraphs = parse_xml(path)

    # Hard safety check: the target XML must actually identify itself as Kaṅkhāvitaraṇī.
    joined_head = "\n".join(paragraphs[:30]).casefold()
    if "kaṅkhāvitaraṇī".casefold() not in joined_head:
        raise RuntimeError(
            f"{filename} does not identify itself as Kaṅkhāvitaraṇī near the beginning. STOP."
        )

    sep = "=" * 78
    lines = [
        sep,
        "BEGIN_SOURCE",
        f"SOURCE_FILE: raw/{filename}",
        f"WORK: {explicit_work}",
        "LAYER_STATUS: AṬṬHAKATHĀ — KAṄKHĀVITARAṆĪ",
        f"EDITION: {EDITION}; cst-kit restructured raw XML",
        f"PROVIDER: {CSTKIT_PROVIDER}",
        f"UPSTREAM: {CSTKIT_UPSTREAM}",
        f"UPSTREAM_COMMIT: {CSTKIT_COMMIT}",
        f"LICENSE: {CSTKIT_LICENSE}",
        "ATTRIBUTION: J.R. Bhaddacak, cst-kit; original CST data from Tipitaka.org.",
        f"SCRIPT: {SCRIPT}",
        f"SOURCE_SHA256: {digest}",
        f"XML_PARAGRAPHS: {pcount}",
        "NOTE: External Pass C2-A source. Kept separate in provenance from the five VRI Samantapāsādikā XML blocks.",
        "END_METADATA",
        sep,
        "",
        *paragraphs,
        "",
        "",
    ]
    meta = (f"raw/{filename}", explicit_work, digest, pcount, len(raw))
    return "\n".join(lines), meta

def main() -> int:
    ap = argparse.ArgumentParser(description="Build TH1 slot 15 v2 with Kaṅkhāvitaraṇī.")
    ap.add_argument("vri_repo", help="Checkout of VipassanaTech/tipitaka-xml at the pinned commit")
    ap.add_argument("cstkit_repo", help="Checkout of bhaddacak/cst-kit at the pinned commit")
    ap.add_argument("--output", required=True, help="Output directory")
    args = ap.parse_args()

    vri_root = Path(args.vri_repo).resolve()
    cstkit_root = Path(args.cstkit_repo).resolve()
    out_dir = Path(args.output).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    missing = []
    for f in VRI_FILES:
        if not (vri_root / "romn" / f).is_file():
            missing.append(str(vri_root / "romn" / f))
    for f, _ in CSTKIT_FILES:
        if not (cstkit_root / "raw" / f).is_file():
            missing.append(str(cstkit_root / "raw" / f))
    if missing:
        print("ERROR: required files missing:", file=sys.stderr)
        for m in missing:
            print("  -", m, file=sys.stderr)
        return 3

    blocks = []
    metas = []

    for f in VRI_FILES:
        block, meta = make_vri_block(vri_root, f)
        blocks.append(block)
        metas.append(meta)

    for f, work in CSTKIT_FILES:
        block, meta = make_cstkit_block(cstkit_root, f, work)
        blocks.append(block)
        metas.append(meta)

    header = [
        "THERAVĀDA RESEARCH CORPUS",
        f"FILE: {OUTPUT_NAME}",
        f"EDITION: {EDITION}",
        "BUILD_STATUS: PASS C2-A / SLOT 15 v2",
        "WORKING SOURCE 1: VRI Roman-Pāli XML (Samantapāsādikā)",
        f"VRI_UPSTREAM: {VRI_UPSTREAM}",
        f"VRI_UPSTREAM_COMMIT: {VRI_COMMIT}",
        "WORKING SOURCE 2: J.R. Bhaddacak cst-kit raw XML (Kaṅkhāvitaraṇī)",
        f"CSTKIT_UPSTREAM: {CSTKIT_UPSTREAM}",
        f"CSTKIT_UPSTREAM_COMMIT: {CSTKIT_COMMIT}",
        f"CSTKIT_LICENSE: {CSTKIT_LICENSE}",
        "CSTKIT_ATTRIBUTION: J.R. Bhaddacak, cst-kit; original CST data from Tipitaka.org.",
        "IMPORTANT: Metadata markers are editorial; source text follows each source block.",
        "IMPORTANT: Samantapāsādikā and Kaṅkhāvitaraṇī are kept as distinct works with distinct provenance.",
        "",
        "",
    ]

    out_path = out_dir / OUTPUT_NAME
    out_path.write_text("\n".join(header + blocks).rstrip() + "\n", encoding="utf-8", newline="\n")
    out_sha = sha256_bytes(out_path.read_bytes())

    text = out_path.read_text(encoding="utf-8")
    checks = {
        "begin_source": text.count("BEGIN_SOURCE"),
        "end_metadata": text.count("END_METADATA"),
        "vri_source_blocks": text.count("SOURCE_FILE: romn/"),
        "cstkit_source_blocks": text.count("SOURCE_FILE: raw/cst-ve-kkh"),
        "kankhavitarani_mentions": text.casefold().count("kaṅkhāvitaraṇī".casefold()),
    }
    if checks["begin_source"] != 7 or checks["end_metadata"] != 7:
        raise RuntimeError(f"Expected 7 complete source blocks, got {checks}")
    if checks["vri_source_blocks"] != 5 or checks["cstkit_source_blocks"] != 2:
        raise RuntimeError(f"Expected 5 VRI + 2 cst-kit blocks, got {checks}")
    if checks["kankhavitarani_mentions"] < 2:
        raise RuntimeError("Kaṅkhāvitaraṇī not sufficiently identifiable in output.")

    manifest = [
        "THERAVĀDA I — PASS C2-A MANIFEST",
        f"BUILD_DATE: {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}",
        f"OUTPUT: {OUTPUT_NAME}",
        f"OUTPUT_SHA256: {out_sha}",
        f"OUTPUT_BYTES: {out_path.stat().st_size}",
        "",
        f"VRI_UPSTREAM: {VRI_UPSTREAM}",
        f"VRI_COMMIT: {VRI_COMMIT}",
        f"CSTKIT_UPSTREAM: {CSTKIT_UPSTREAM}",
        f"CSTKIT_COMMIT: {CSTKIT_COMMIT}",
        f"CSTKIT_LICENSE: {CSTKIT_LICENSE}",
        "",
        "SOURCE_COUNT: 7",
        "SOURCES:",
    ]
    for source_file, work, digest, pcount, nbytes in metas:
        manifest.append(
            f"  - {source_file} | {work} | sha256={digest} | paragraphs={pcount} | bytes={nbytes}"
        )
    manifest += [
        "",
        "INTEGRITY:",
        "  - Five VRI Samantapāsādikā XML SHA256 values match the already-audited TH1 slot 15 metadata.",
        "  - Exactly two Kaṅkhāvitaraṇī raw XML books are appended.",
        "  - No slots other than 15 are built.",
        f"  - Output SHA256: {out_sha}",
    ]

    manifest_path = out_dir / "PASS_C2A_MANIFEST.txt"
    manifest_path.write_text("\n".join(manifest) + "\n", encoding="utf-8", newline="\n")

    print("DONE")
    print(f"Created: {out_path}")
    print("Source blocks: 7 = 5 Samantapāsādikā + 2 Kaṅkhāvitaraṇī")
    print(f"Output SHA256: {out_sha}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
