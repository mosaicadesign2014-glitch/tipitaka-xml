#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
THERAVĀDA I — PASS C3-B / BUILDER v4.2
Build ONLY slot 25 v4 by preserving the already-audited slot 25 v3 and
appending one extracted VRI/CST source segment: Mohavicchedanī.

Important:
romn/abh09t.nrf.xml is an aggregate VRI XML containing a derived
Abhidhammamātikāpāḷi prefix followed by Mohavicchedanī.
The derived mātikā prefix is NOT ingested as an independent TH1 work.
Only the Mohavicchedanī segment is extracted.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET

VRI_COMMIT = "e064d02da2db3df9a7d116a9191092b12e6dfe01"
VRI_UPSTREAM = "https://github.com/VipassanaTech/tipitaka-xml"
VRI_SOURCE = "romn/abh09t.nrf.xml"

V3_BUILDER = Path("scripts/build_th1_slot25_v3.py")
EXPECTED_V3_BUILDER_SHA256 = "c0d9d9cdf2a1e40203114b37442b2ca666dae39ed27956256922af3526c10764"
EXPECTED_V3_SLOT25_SHA256 = "b901d644e9bef996b59efc24d6bd0822aea793f638ad01e20242185bf8cbdb1f"

OUTPUT_NAME = "25_ABHIDHAMMA_TIKA_MANUALS.txt"
EDITION = "Chaṭṭha Saṅgāyana Tipiṭaka (CST)"
PROVIDER = "Vipassana Research Institute / Tipitaka.org"

STRUCT_MARKERS = {
    "nikaya": "NIKĀYA",
    "book": "BOOK",
    "chapter": "CHAPTER",
    "title": "TITLE",
    "subhead": "SUBHEAD",
    "subsubhead": "SUBSUBHEAD",
}

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())

def require_hash(path: Path, expected: str, label: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise RuntimeError(
            f"{label} SHA256 mismatch\nexpected: {expected}\nactual:   {actual}"
        )

def normalize_inline(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[\t\r\n ]+", " ", s)
    return s.strip()

def key(s: str) -> str:
    s = unicodedata.normalize("NFC", s).casefold()
    s = s.replace("’", "'").replace("‘", "'")
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .–—-:;")

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

def parse_paragraphs(xml_path: Path):
    raw = xml_path.read_bytes()
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        raise RuntimeError(f"XML parse failed for {xml_path}: {e}") from e

    paras = []
    for p in root.iter():
        if p.tag.split("}")[-1] != "p":
            continue
        rend = p.attrib.get("rend", "bodytext")
        text = normalize_inline(render_element(p))
        if not text:
            continue
        marker = STRUCT_MARKERS.get(rend)
        rendered = f"⟦{marker}⟧ {text}" if marker else text
        paras.append({
            "rend": rend,
            "text": text,
            "key": key(text),
            "rendered": rendered,
        })
    return raw, paras

def find_unique(indices, label: str) -> int:
    if len(indices) != 1:
        raise RuntimeError(f"Expected exactly one {label}; found {len(indices)}: {indices[:20]}")
    return indices[0]

def extract_mohavicchedani(xml_path: Path):
    raw, paras = parse_paragraphs(xml_path)
    if len(paras) < 100:
        raise RuntimeError(f"Unexpectedly short aggregate XML: {len(paras)} paragraphs")

    # Boundary 1: explicit end of the derived Abhidhammamātikāpāḷi.
    prefix_hits = [
        i for i,p in enumerate(paras)
        if "abhidhammamātikāpāḷi niṭṭhitā" in p["key"]
        or "abhidhammamātikāpāli niṭṭhitā" in p["key"]
    ]
    prefix_end = find_unique(prefix_hits, "Abhidhammamātikāpāḷi explicit")

    # Boundary 2: structural Mohavicchedanī heading after that explicit.
    heading_hits = [
        i for i,p in enumerate(paras)
        if i > prefix_end
        and "mohavicchedanī" in p["key"]
        and p["rend"] in {"book","chapter","title","subhead","subsubhead","centre","center"}
    ]
    if not heading_hits:
        # Conservative fallback: exact textual heading after the prefix.
        heading_hits = [
            i for i,p in enumerate(paras)
            if i > prefix_end and p["key"] == "mohavicchedanī"
        ]
    if not heading_hits:
        raise RuntimeError("No Mohavicchedanī heading found after Abhidhammamātikāpāḷi explicit.")

    # VRI aggregate XML can repeat the work title later (for example in a
    # colophon/structural closing context).  The work-start is therefore the
    # EARLIEST Mohavicchedanī heading after the derived mātikā explicit.
    # Later same-title structural occurrences are audit information, not
    # alternative start boundaries.
    heading = min(heading_hits)
    later_moh_headings = [i for i in heading_hits if i != heading]

    # Include the nearest Namo tassa between the mātikā explicit and the heading.
    namo_hits = [
        i for i,p in enumerate(paras)
        if prefix_end < i <= heading
        and p["key"].startswith("namo tassa bhagavato arahato sammāsambuddhassa")
    ]
    if len(namo_hits) != 1:
        raise RuntimeError(
            f"Expected exactly one Namo tassa between prefix explicit and Moh heading; found {namo_hits}"
        )
    start = namo_hits[0]

    if start <= prefix_end:
        raise RuntimeError("Extraction boundary would include derived mātikā prefix.")

    segment = paras[start:]
    joined = "\n".join(p["rendered"] for p in segment)
    joined_key = key(joined)

    # Incipit / identity gates.
    incipit_ok = (
        "kāruññabhāvitaṃ" in joined_key
        or "karuṇābhāvitaṃ" in joined_key
        or "karuṇābhāvitaṃ" in joined_key
    )
    if not incipit_ok:
        raise RuntimeError("Mohavicchedanī incipit stanza was not found.")

    if "mohavicchedaniṃ nāma" not in joined_key and "mohavicchedani nāma" not in joined_key:
        raise RuntimeError("Programmatic title stanza 'Mohavicchedaniṃ nāma' not found.")

    # Seven Abhidhamma-mātikā coverage gates.
    required_stems = {
        "1_Dhammasangani": ["dhammasaṅgaṇīmātik"],
        "2_Vibhanga": ["dhammahadayavibhaṅgamātik", "vibhaṅgamātik"],
        "3_Dhatukatha": ["dhātukathāmātik"],
        "4_Puggalapannatti": ["puggalapaññattimātik"],
        "5_Kathavatthu": ["kathāvatthumātik"],
        "6_Yamaka": ["yamakamātik"],
        "7_Patthana": ["paṭṭhānamātik"],
    }
    coverage = {}
    for label, stems in required_stems.items():
        found = [stem for stem in stems if stem in joined_key]
        coverage[label] = found
        if not found:
            raise RuntimeError(f"Required Mohavicchedanī section missing: {label}")

    # End gate: a final niṭṭhitā must occur near EOF, with Moh context in the tail.
    nitthita = [i for i,p in enumerate(segment) if "niṭṭhitā" in p["key"]]
    if not nitthita:
        raise RuntimeError("No niṭṭhitā explicit found in extracted Mohavicchedanī.")
    last_explicit = nitthita[-1]

    tail = segment[max(0, len(segment)-80):]
    tail_key = key("\n".join(p["rendered"] for p in tail))
    if "mohavicchedan" not in tail_key:
        raise RuntimeError("Final tail lacks Mohavicchedanī colophon/context.")
    if "niṭṭhitā" not in tail_key:
        raise RuntimeError("Final tail lacks a niṭṭhitā explicit.")

    # No later independent work may begin after the last explicit.
    after_explicit = segment[last_explicit+1:]
    later_structural = [
        (p["rend"], p["text"]) for p in after_explicit
        if p["rend"] in {"book","chapter","title"}
    ]
    if later_structural:
        raise RuntimeError(
            "Unexpected independent structural heading after final Moh explicit: "
            + repr(later_structural[:10])
        )

    # Render exact extracted research text.
    extracted_text = "\n".join(p["rendered"] for p in segment).rstrip() + "\n"
    extracted_bytes = extracted_text.encode("utf-8")
    extracted_sha = sha256_bytes(extracted_bytes)
    upstream_sha = sha256_bytes(raw)

    def context(a: int, b: int):
        a=max(0,a); b=min(len(paras),b)
        return [f"{i:05d} | {paras[i]['rend']:<12} | {paras[i]['rendered']}" for i in range(a,b)]

    audit = {
        "upstream_sha": upstream_sha,
        "upstream_bytes": len(raw),
        "aggregate_paragraphs": len(paras),
        "prefix_end_index": prefix_end,
        "heading_index": heading,
        "all_mohavicchedani_heading_indices": heading_hits,
        "later_mohavicchedani_heading_indices": later_moh_headings,
        "start_index": start,
        "extracted_paragraphs": len(segment),
        "extracted_bytes": len(extracted_bytes),
        "extracted_sha": extracted_sha,
        "last_explicit_segment_index": last_explicit,
        "coverage": coverage,
        "boundary_context": context(prefix_end-4, heading+8),
        "tail_context": [
            f"{start+i:05d} | {p['rend']:<12} | {p['rendered']}"
            for i,p in list(enumerate(segment))[-25:]
        ],
    }
    return extracted_text, audit

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vri_repo", help="Pinned checkout of VipassanaTech/tipitaka-xml")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    vri = Path(args.vri_repo).resolve()
    out_dir = Path(args.output).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    require_hash(V3_BUILDER, EXPECTED_V3_BUILDER_SHA256, "Audited slot-25 v3 builder")

    xml_path = vri / VRI_SOURCE
    if not xml_path.is_file():
        raise RuntimeError(f"Required VRI source not found: {xml_path}")

    # First reconstruct the already audited v3 slot 25.
    with tempfile.TemporaryDirectory(prefix="th1-c3b-v3-") as td:
        v3_out = Path(td) / "v3"
        subprocess.run(
            [
                sys.executable,
                str(V3_BUILDER),
                str(vri),
                "--output", str(v3_out),
            ],
            check=True,
        )
        v3_slot = v3_out / OUTPUT_NAME
        if not v3_slot.is_file():
            raise RuntimeError("Slot 25 v3 was not produced.")
        require_hash(v3_slot, EXPECTED_V3_SLOT25_SHA256, "Audited slot 25 v3")
        base_text = v3_slot.read_text(encoding="utf-8")

    if base_text.count("BEGIN_SOURCE") != 9:
        raise RuntimeError("Audited v3 base must contain exactly 9 source blocks.")
    if "WORK: Rūpārūpavibhāga" not in base_text:
        raise RuntimeError("Audited v3 base is missing Rūpārūpavibhāga.")

    extracted, audit = extract_mohavicchedani(xml_path)

    # Protect against accidental inclusion of the derived mātikā prefix.
    if "Abhidhammamātikāpāḷi niṭṭhitā" in extracted:
        raise RuntimeError("Derived Abhidhammamātikāpāḷi prefix leaked into Moh extraction.")

    sep = "=" * 78
    source_block = f"""
{sep}
BEGIN_SOURCE
SOURCE_FILE: derived/vri/abh09t.nrf.xml#Mohavicchedanī
UPSTREAM_SOURCE_FILE: {VRI_SOURCE}
WORK: Mohavicchedanī
LAYER_STATUS: AṬṬHAKATHĀ / CLASSICAL ABHIDHAMMA EXEGESIS — MOHAVICCHEDANĪ
TEXTUAL_STATUS: EXTRACTED LOGICAL WORK FROM PINNED VRI/CST AGGREGATE XML
EDITION: {EDITION}
PROVIDER: {PROVIDER}
UPSTREAM: {VRI_UPSTREAM}
UPSTREAM_COMMIT: {VRI_COMMIT}
UPSTREAM_SOURCE_SHA256: {audit['upstream_sha']}
SCRIPT: Roman Pāli
SOURCE_SHA256: {audit['extracted_sha']}
SOURCE_SHA256_SCOPE: UTF-8 LF-normalized rendered Mohavicchedanī segment only
XML_PARAGRAPHS_EXTRACTED: {audit['extracted_paragraphs']}
ATTRIBUTION: Mahākassapatthera / Kassapa (traditional/textual attribution)
RESEARCH_CLASSIFICATION: Commentary on the mātikās of the seven Abhidhamma texts
EXCLUDED_PREFIX: Abhidhammamātikāpāḷi derived compilation — NOT INGESTED AS AN INDEPENDENT TH1 WORK
RIGHTS_NOTE: VRI repository states its XML files are freely available for non-commercial use and requests attribution.
NOTE: Extraction boundaries and integrity gates are recorded in MOHAVICCHEDANI_C3B_EXTRACTION_AUDIT.txt.
END_METADATA
{sep}

{extracted.rstrip()}
{sep}
END_DERIVED_SOURCE
{sep}
"""

    final = base_text.rstrip() + "\n\n" + source_block.lstrip()
    final_path = out_dir / OUTPUT_NAME
    final_path.write_text(final.rstrip() + "\n", encoding="utf-8", newline="\n")

    check = final_path.read_text(encoding="utf-8")
    if check.count("BEGIN_SOURCE") != 10:
        raise RuntimeError("Slot 25 v4 must contain exactly 10 source blocks.")
    if check.count("SOURCE_FILE: derived/vri/abh09t.nrf.xml#Mohavicchedanī") != 1:
        raise RuntimeError("Expected exactly one Mohavicchedanī derived source block.")
    if check.count("WORK: Mohavicchedanī") != 1:
        raise RuntimeError("Expected exactly one Mohavicchedanī WORK metadata line.")
    if check.count("WORK: Rūpārūpavibhāga") != 1:
        raise RuntimeError("Rūpārūpavibhāga must remain exactly once.")
    if "Upacaya-santatiyo (catūhi ?) jāyantīti vuccanti." not in check:
        raise RuntimeError("C2-B5 locus E was lost.")
    if "(Na arūpakasattānaṃ paṭisandhikāle na\nsaddo viyāti (?)." not in check:
        raise RuntimeError("C2-B5 locus H was altered.")

    final_sha = sha256_file(final_path)

    # Detailed boundary/extraction audit.
    audit_lines = [
        "THERAVĀDA I — PASS C3-B",
        "MOHAVICCHEDANĪ EXTRACTION AUDIT",
        "",
        f"VRI_UPSTREAM: {VRI_UPSTREAM}",
        f"VRI_COMMIT: {VRI_COMMIT}",
        f"UPSTREAM_SOURCE_FILE: {VRI_SOURCE}",
        f"UPSTREAM_SOURCE_SHA256: {audit['upstream_sha']}",
        f"UPSTREAM_SOURCE_BYTES: {audit['upstream_bytes']}",
        f"AGGREGATE_XML_PARAGRAPHS: {audit['aggregate_paragraphs']}",
        "",
        f"DERIVED_PREFIX_EXPLICIT_INDEX: {audit['prefix_end_index']}",
        f"MOHAVICCHEDANI_START_HEADING_INDEX: {audit['heading_index']}",
        f"ALL_MOHAVICCHEDANI_STRUCTURAL_INDICES: {audit['all_mohavicchedani_heading_indices']}",
        f"LATER_SAME_TITLE_STRUCTURAL_INDICES: {audit['later_mohavicchedani_heading_indices']}",
        f"EXTRACTION_START_INDEX: {audit['start_index']}",
        f"EXTRACTED_PARAGRAPHS: {audit['extracted_paragraphs']}",
        f"EXTRACTED_BYTES_UTF8: {audit['extracted_bytes']}",
        f"EXTRACTED_TEXT_SHA256: {audit['extracted_sha']}",
        f"LAST_EXPLICIT_SEGMENT_INDEX: {audit['last_explicit_segment_index']}",
        "",
        "SEVEN-MATIKA COVERAGE:",
    ]
    for label, found in audit["coverage"].items():
        audit_lines.append(f"PASS | {label} | {', '.join(found)}")
    audit_lines += [
        "",
        "BOUNDARY CONTEXT:",
        *audit["boundary_context"],
        "",
        "FINAL TAIL CONTEXT:",
        *audit["tail_context"],
        "",
        "DECISION:",
        "PASS if this report was produced by the builder.",
        "The derived Abhidhammamātikāpāḷi prefix was excluded.",
        "Only Mohavicchedanī was appended to TH1 slot 25.",
    ]
    (out_dir/"MOHAVICCHEDANI_C3B_EXTRACTION_AUDIT.txt").write_text(
        "\n".join(audit_lines) + "\n", encoding="utf-8", newline="\n"
    )

    manifest = f"""THERAVĀDA I — PASS C3-B MANIFEST
BUILD_DATE_UTC: {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}
OUTPUT: {OUTPUT_NAME}
OUTPUT_SHA256: {final_sha}
OUTPUT_BYTES: {final_path.stat().st_size}

BASE_SLOT25_VERSION: v3 / C2-B5
BASE_SLOT25_SHA256: {EXPECTED_V3_SLOT25_SHA256}
BASE_SLOT25_SOURCE_COUNT: 9

ADDED_WORK: Mohavicchedanī
ADDED_SOURCE_TYPE: extracted logical work from pinned VRI aggregate XML
UPSTREAM_SOURCE_FILE: {VRI_SOURCE}
UPSTREAM_SOURCE_SHA256: {audit['upstream_sha']}
EXTRACTED_TEXT_SHA256: {audit['extracted_sha']}
FINAL_SLOT25_SOURCE_COUNT: 10

VRI_COMMIT: {VRI_COMMIT}

INTEGRITY:
- Slot 25 v3 is rebuilt and SHA256-locked before modification.
- Exactly one new Mohavicchedanī source block is appended.
- The preceding derived Abhidhammamātikāpāḷi compilation is excluded.
- Seven Abhidhamma-mātikā coverage gates pass.
- Mohavicchedanī incipit/title/explicit gates pass.
- C2-B5 Rūpārūpavibhāga loci E and H remain unchanged.
- No other TH1 slot is emitted.
"""
    (out_dir/"PASS_C3B_MANIFEST.txt").write_text(manifest, encoding="utf-8", newline="\n")

    print("PASS C3-B BUILD COMPLETE")
    print(final_path)
    print("OUTPUT_SHA256:", final_sha)
    print("MOHAVICCHEDANI_SOURCE_SHA256:", audit["extracted_sha"])
    print("UPSTREAM_XML_SHA256:", audit["upstream_sha"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
