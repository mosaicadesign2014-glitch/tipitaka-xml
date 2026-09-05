#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, sys

META = Path("metadata")

def rows(name):
    with (META/name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def main():
    source = rows("TH1_SOURCE_REGISTRY_v1_1.csv")
    prov = rows("TH1_PROVENANCE_01_13_VERIFIED.csv")
    freeze = rows("TH1_SLOT_FREEZE_C2B5_v1.csv")
    sub = rows("TH1_SUBWORK_REGISTRY_v1.csv")
    lock = rows("VERSION_LOCK_v1_1.csv")

    assert len(source) == 156, len(source)
    assert len({r["source_file"] for r in source}) == 156
    assert len({r["source_sha256"] for r in source}) == 156

    assert len(prov) == 61
    assert all(r["match"] == "PASS" for r in prov)
    assert all(r["expected_source_sha256"] == r["actual_source_sha256"] for r in prov)

    verified = {r["source_file"] for r in source if r["provenance_status"]=="VERIFIED_PINNED_01_13"}
    assert verified == {r["source_file"] for r in prov}
    assert len(verified) == 61
    assert not any(r["provenance_status"]=="PENDING_PIN_VERIFY" for r in source)

    assert len(freeze) == 25
    assert [int(r["slot"]) for r in freeze] == list(range(1,26))
    assert sum(int(r["source_blocks"]) for r in freeze) == 156

    assert len(sub) == 36
    assert {r["slot"] for r in sub}.issubset({"22","24","25"})

    datasets = {r["dataset"]:r for r in lock}
    assert datasets["VRI_CST_ROMN_TH1"]["commit"] == "e064d02da2db3df9a7d116a9191092b12e6dfe01"
    assert datasets["CSTKIT_KANKHAVITARANI"]["commit"] == "cc0bab5fdf378d01deb3649112c0a9fddc317283"

    print("PASS: TH1 C2-C metadata freeze v1.1 is internally consistent.")

if __name__ == "__main__":
    main()
