# Releases of the putti23 fork

## 2.0 — native-map baseline

- Preserve native cluster navigation: disable phone video/mirroring in both
  CarPlay and Android Auto integration, including external config overrides.
- Preserve phone navigation BAP turn-by-turn; remove the 20 km distance cutoff.
- Visible default logo text: `(c) fifthBro v2.0`.
- No stream111 experiments, diagnostic collectors or experimental preloads.
- INSTALL and RESTORE both deploy pinned baseline 2.0. Upgrades must use 2.1,
  2.2, etc.; never replace a published 2.0 artifact/tag with different bytes.
- Preserve upstream attribution and noncommercial CC BY-NC-SA 4.0 license.

Vehicle validation pending. This is a release designation, not a claim that
every PCM/HUD combination has been tested. See packaging/v2/README_PL.md.
