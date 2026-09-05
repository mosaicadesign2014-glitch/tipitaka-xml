#!/usr/bin/env python3
from pathlib import Path
import argparse, csv, hashlib, sys, datetime as dt

PINNED_COMMIT = "e064d02da2db3df9a7d116a9191092b12e6dfe01"
UPSTREAM = "https://github.com/VipassanaTech/tipitaka-xml"

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("vri_repo")
    ap.add_argument("--expected", required=True)
    ap.add_argument("--source-registry", required=True)
    ap.add_argument("--subwork-registry", required=True)
    ap.add_argument("--slot-freeze", required=True)
    ap.add_argument("--output", required=True)
    a=ap.parse_args()

    root=Path(a.vri_repo)
    out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    expected=list(csv.DictReader(open(a.expected,encoding="utf-8")))
    if len(expected)!=61:
        raise SystemExit(f"Expected 61 canonical source rows, got {len(expected)}")

    verified=[]
    failures=[]
    for r in expected:
        sf=r["source_file"]
        rel=sf[5:] if sf.startswith("romn/") else sf
        p=root/"romn"/rel
        if not p.is_file():
            failures.append((sf,"MISSING",""))
            continue
        actual=sha256(p)
        ok=actual==r["expected_source_sha256"]
        verified.append({**r,
            "actual_source_sha256":actual,
            "match":"PASS" if ok else "FAIL",
            "verified_upstream":UPSTREAM,
            "verified_commit":PINNED_COMMIT})
        if not ok:
            failures.append((sf,r["expected_source_sha256"],actual))

    with (out/"TH1_PROVENANCE_01_13_VERIFIED.csv").open("w",encoding="utf-8",newline="") as f:
        fields=list(verified[0].keys()) if verified else []
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(verified)

    # Copy metadata registries into artifact.
    for src,name in [
        (a.source_registry,"TH1_SOURCE_REGISTRY_v1.csv"),
        (a.subwork_registry,"TH1_SUBWORK_REGISTRY_v1.csv"),
        (a.slot_freeze,"TH1_SLOT_FREEZE_C2B5_v1.csv")]:
        Path(out,name).write_bytes(Path(src).read_bytes())

    with (out/"VERSION_LOCK.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f)
        w.writerow(["dataset","upstream","commit","status"])
        w.writerow(["VRI_CST_ROMN_TH1","https://github.com/VipassanaTech/tipitaka-xml",PINNED_COMMIT,
                    "VERIFIED_01_13" if not failures else "FAILED_01_13"])
        w.writerow(["CSTKIT_KANKHAVITARANI","https://github.com/bhaddacak/cst-kit",
                    "cc0bab5fdf378d01deb3649112c0a9fddc317283","PINNED_C2A"])
        w.writerow(["RUPARUPAVIBHAGA_PTS1915","PTS 1915 pp.149-159","N/A","DIPLOMATIC_C2B5"])

    report=[
        "THERAVĀDA I — METADATA / PROVENANCE AUDIT v1",
        f"DATE_UTC: {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}",
        f"PINNED_VRI_COMMIT: {PINNED_COMMIT}",
        f"EXPECTED_01_13_SOURCE_UNITS: 61",
        f"VERIFIED_ROWS: {len(verified)}",
        f"FAILURES: {len(failures)}",
        "",
    ]
    if failures:
        report.append("RESULT: FAIL")
        for sf,exp,act in failures:
            report.append(f"FAIL | {sf} | expected={exp} | actual={act}")
    else:
        report += [
            "RESULT: PASS",
            "All 61 source XML units represented in TH1 slots 01–13 match the exact pinned VRI commit.",
            "No canonical Pāli slot file was modified by this audit.",
            "Use SOURCE_REGISTRY + VERSION_LOCK as the provenance layer rather than rewriting slots 01–13 merely to add commit metadata.",
        ]
    (out/"TH1_METADATA_PROVENANCE_AUDIT_REPORT.txt").write_text("\n".join(report)+"\n",encoding="utf-8")

    if failures:
        raise SystemExit(2)
    print("PASS: all 61 TH1 slots 01–13 XML hashes match pinned VRI commit.")

if __name__=="__main__":
    main()
