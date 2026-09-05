# THERAVĀDA I — PASS C3-B — Mohavicchedanī

## Discovery

The pinned official VRI/CST repository contains:

`romn/abh09t.nrf.xml`

at commit:

`e064d02da2db3df9a7d116a9191092b12e6dfe01`

This aggregate contains a derived `Abhidhammamātikāpāḷi` compilation followed by
the independent classical work **Mohavicchedanī**.

## Editorial decision

Do **not** ingest the aggregate XML wholesale.

The builder:

1. rebuilds the already-audited slot 25 v3;
2. requires its exact SHA256:
   `b901d644e9bef996b59efc24d6bd0822aea793f638ad01e20242185bf8cbdb1f`;
3. locates `Abhidhammamātikāpāḷi niṭṭhitā`;
4. finds the following `Namo tassa ...` and `Mohavicchedanī` heading;
5. extracts only the Mohavicchedanī segment;
6. verifies the incipit/title formula;
7. verifies coverage of all seven Abhidhamma mātikā sections;
8. verifies a final Mohavicchedanī/niṭṭhitā context;
9. appends exactly one new source block.

The derived mātikā prefix is recorded but is **not** ingested as an independent TH1 work.

## Expected source-count change

Slot 25:
- v3 = 9 source blocks
- v4 = 10 source blocks

TH1 total after successful audit:
- current = 156
- candidate v4 = 157

Do not update the TH1 metadata freeze until the GitHub-generated v4 artifact has been audited.

## Required existing fork files

This package assumes the repository still contains the previously installed C2-B5 files:
- `scripts/build_th1_slot25_v3.py`
- `scripts/build_th1_slots_14_25.py`
- `external/ruparupavibhaga/RUPARUPAVIBHAGA_PTS1915_DIPLOMATIC_v1.txt`
- `external/ruparupavibhaga/RUPARUPAVIBHAGA_FINAL_APPARATUS_v1.txt`

The v4 builder SHA-locks the v3 builder at:

`c0d9d9cdf2a1e40203114b37442b2ca666dae39ed27956256922af3526c10764`

## Package files

- `.github/workflows/build-th1-slot25-v4-mohavicchedani.yml`
- `scripts/build_th1_slot25_v4_mohavicchedani.py`
- `TH1_PASS_C3B_README.md`

## Expected artifact

`TH1_slot25_v4_Mohavicchedani`

Expected contents:
- `25_ABHIDHAMMA_TIKA_MANUALS.txt`
- `MOHAVICCHEDANI_C3B_EXTRACTION_AUDIT.txt`
- `PASS_C3B_MANIFEST.txt`
- `ARTIFACT_SHA256SUMS.txt`

Do not replace the installed slot 25 v3 until this artifact is audited.
