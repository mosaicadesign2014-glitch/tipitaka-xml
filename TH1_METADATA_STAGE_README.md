# THERAVĀDA I — Metadata / Provenance Stage v1

This stage does NOT modify any of the 25 TH1 Pāli source slots.

It does two things:

1. Verifies that all 61 XML source units represented by slots 01–13 match the exact VRI commit:
   `e064d02da2db3df9a7d116a9191092b12e6dfe01`.

2. Creates/ships the research-index layer:
   - `TH1_SOURCE_REGISTRY_v1.csv`
   - `TH1_SUBWORK_REGISTRY_v1.csv`
   - `TH1_SLOT_FREEZE_C2B5_v1.csv`
   - `VERSION_LOCK.csv`

The SUBWORK registry records only clear logical work boundaries. It does not treat ordinary
chapters or volume divisions as separate works.

Expected artifact:
`TH1_metadata_provenance_audit_v1`

Do not replace any TH1 source file during this stage.
