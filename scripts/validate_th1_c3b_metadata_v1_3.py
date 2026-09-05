#!/usr/bin/env python3
from pathlib import Path
import csv, collections

M=Path("metadata")

def rows(name):
    with (M/name).open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def main():
    source=rows("TH1_SOURCE_REGISTRY_v1_3.csv")
    freeze=rows("TH1_SLOT_FREEZE_C3B_v1_3.csv")
    prov=rows("TH1_PROVENANCE_01_13_VERIFIED.csv")
    sub=rows("TH1_SUBWORK_REGISTRY_v1.csv")
    lock=rows("VERSION_LOCK_v1_3.csv")

    assert len(source)==157
    assert len({r["source_file"] for r in source})==157
    assert len({r["source_sha256"] for r in source})==157

    c=collections.Counter(r["provenance_status"] for r in source)
    assert c["VERIFIED_PINNED_01_13"]==61
    assert c["PINNED_IN_SLOT"]==92
    assert c["VERIFIED_C3B_VRI_DERIVED"]==1
    assert c["VERIFIED_C2A_CSTKIT"]==2
    assert c["VERIFIED_C2B5_DIPLOMATIC_EXTERNAL"]==1
    assert sum(c.values())==157
    assert 61+92+1==154

    moh=[r for r in source if r["provenance_status"]=="VERIFIED_C3B_VRI_DERIVED"]
    assert len(moh)==1
    m=moh[0]
    assert m["source_file"]=="derived/vri/abh09t.nrf.xml#Mohavicchedanī"
    assert m["upstream_source_file"]=="romn/abh09t.nrf.xml"
    assert m["upstream_source_sha256"]=="af89c67f8144da1e11b0494a4c587a5f84d8e65633ccebf2dfdc532c9b7cb1f5"
    assert m["source_sha256"]=="f6ff1aa52e4964589aa863667354c5f199df83e75f14cc5b2285258d5091b8b2"

    assert len(freeze)==25
    assert sum(int(r["source_blocks"]) for r in freeze)==157
    s25=[r for r in freeze if r["slot"]=="25"][0]
    assert s25["source_blocks"]=="10"
    assert s25["sha256"]=="0a02c068929495f5998ef74f1d0f1780219ee11c33764477f8baa9d4d419ac3a"

    assert len(prov)==61 and all(r["match"]=="PASS" for r in prov)
    assert len(sub)==36

    d={r["dataset"]:r for r in lock}
    assert d["VRI_CST_ROMN_TH1"]["status"]=="LOCKED_154_VRI_DERIVED_SOURCE_BLOCKS"
    assert d["VRI_CST_ROMN_TH1"]["commit"]=="e064d02da2db3df9a7d116a9191092b12e6dfe01"

    print("PASS: TH1 C3-B metadata freeze v1.3")
    print("157 total = 154 VRI-derived/pinned + 2 cst-kit + 1 PTS diplomatic")

if __name__=="__main__":
    main()
