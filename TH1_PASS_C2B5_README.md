# TH1 PASS C2-B5 — Slot 25 v3

This package updates **only `25_ABHIDHAMMA_TIKA_MANUALS.txt`**.

## Method

The new builder does not reconstruct the old slot 25 independently.

It first runs the already-audited base builder:

`scripts/build_th1_slots_14_25.py`

and verifies that file's SHA256:

`2146648ef2f9fb9409dc6401389260b9a8c59f901bd4ce4b7cdbbcda48e6a115`

against the pinned VRI commit:

`e064d02da2db3df9a7d116a9191092b12e6dfe01`

It then takes only the regenerated slot 25 and appends one new external source:

**Rūpārūpavibhāga**, PTS 1915, pp.149–159.

## Textual policy

This is a **diplomatic PTS-based research transcription**, not a newly invented critical edition.

E is preserved:

`Upacaya-santatiyo (catūhi ?) jāyantīti vuccanti.`

H is preserved without conjectural correction.

UPT589_4F is recorded as manuscript control only. No word-level Myanmar reading is invented.

The modern `A Comprehensive Manual of Abhidhamma` is used only as doctrinal control.
Its copyrighted PDF/text is **not included** in this public-GitHub package.

## Package files

- `.github/workflows/build-th1-slot25-v3.yml`
- `scripts/build_th1_slot25_v3.py`
- `external/ruparupavibhaga/RUPARUPAVIBHAGA_PTS1915_DIPLOMATIC_v1.txt`
- `external/ruparupavibhaga/RUPARUPAVIBHAGA_FINAL_APPARATUS_v1.txt`
- `TH1_PASS_C2B5_README.md`

Expected GitHub artifact:

`TH1_slot25_v3_Ruparupavibhaga`

Expected artifact contents:

- `25_ABHIDHAMMA_TIKA_MANUALS.txt`
- `PASS_C2B5_MANIFEST.txt`
- `ARTIFACT_SHA256SUMS.txt`

Do not replace the existing TH1 slot 25 until the downloaded artifact has been audited.
