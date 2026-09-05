#!/usr/bin/env python3
from pathlib import Path
import csv, collections

M = Path("metadata")

def rows(name):
    with (M/name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def main():
    source = rows("TH1_SOURCE_REGISTRY_v1_1.csv")
    prov = rows("TH1_PROVENANCE_01_13_VERIFIED.csv")
    freeze = rows("TH1_SLOT_FREEZE_C2B5_v1.csv")
    sub = rows("TH1_SUBWORK_REGISTRY_v1.csv")
    lock = rows("VERSION_LOCK_v1_2.csv")

    assert len(source) == 156
    assert len({r["source_file"] for r in source}) == 156
    assert len({r["source_sha256"] for r in source}) == 156

    statuses = collections.Counter(r["provenance_status"] for r in source)
    assert statuses["VERIFIED_PINNED_01_13"] == 61
    assert statuses["PINNED_IN_SLOT"] == 92
    assert statuses["VERIFIED_C2A_CSTKIT"] == 2
    assert statuses["VERIFIED_C2B5_DIPLOMATIC_EXTERNAL"] == 1

    vri = statuses["VERIFIED_PINNED_01_13"] + statuses["PINNED_IN_SLOT"]
    assert vri == 153
    assert vri + statuses["VERIFIED_C2A_CSTKIT"] + statuses["VERIFIED_C2B5_DIPLOMATIC_EXTERNAL"] == 156

    assert len(prov) == 61
    assert all(r["match"] == "PASS" for r in prov)
    assert all(r["expected_source_sha256"] == r["actual_source_sha256"] for r in prov)

    assert len(freeze) == 25
    assert sum(int(r["source_blocks"]) for r in freeze) == 156
    assert len(sub) == 36

    datasets = {r["dataset"]:r for r in lock}
    vri_lock = datasets["VRI_CST_ROMN_TH1"]
    assert vri_lock["commit"] == "e064d02da2db3df9a7d116a9191092b12e6dfe01"
    assert vri_lock["status"] == "LOCKED_153_VRI_SOURCE_UNITS"

    cst = datasets["CSTKIT_KANKHAVITARANI"]
    assert cst["commit"] == "cc0bab5fdf378d01deb3649112c0a9fddc317283"

    print("PASS: TH1 C2-C metadata freeze v1.2 is internally consistent.")
    print("Population: 153 VRI + 2 cst-kit + 1 PTS diplomatic = 156 total.")

if __name__ == "__main__":
    main()
