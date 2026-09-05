# TH1 Pass C2-A — Slot 15 v2

This GitHub Actions build changes **only TH1 slot 15**.

It rebuilds the five existing Samantapāsādikā XML source blocks from the exact
VRI commit already used by TH1 slots 14–25 and appends:

- `cst-ve-kkh1.xml` — Kaṅkhāvitaraṇī, Bhikkhupātimokkha section
- `cst-ve-kkh2.xml` — Kaṅkhāvitaraṇī, Bhikkhunīpātimokkha section

Pinned sources:

- VRI: `e064d02da2db3df9a7d116a9191092b12e6dfe01`
- cst-kit: `cc0bab5fdf378d01deb3649112c0a9fddc317283`

The cst-kit raw XML is CC BY-SA 4.0 and attribution is written into the output.

Expected artifact:

`TH1_slot15_v2_Kankhavitarani`

It contains:

- `15_VINAYA_ATTHAKATHA.txt`
- `PASS_C2A_MANIFEST.txt`
- `ARTIFACT_SHA256SUMS.txt`

Do not change any other TH1 slot during this stage.
