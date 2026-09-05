# TH1 GitHub Builder

This fork contains a small build layer for Theravāda I slots 14–25.

The GitHub Action:
1. downloads a clean copy of the official `VipassanaTech/tipitaka-xml`;
2. records the exact official upstream commit SHA;
3. creates only slots 14–25;
4. performs integrity checks;
5. creates an Actions artifact named `TH1_slots_14_25`.

The existing VRI XML in this fork is not used as the build input and is not modified.

For the first build, leave `upstream_ref` = `main`.
For exact later reproduction, enter the upstream SHA recorded in `BUILD_MANIFEST.txt`.
