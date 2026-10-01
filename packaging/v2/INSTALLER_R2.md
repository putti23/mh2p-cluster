# Cluster 2.0 — installer r2

The original installer did NOT work on this PCM: system cmp was unavailable.
Use `releases/v2.0-r2/MH2P_Cluster_v2.0_r2_INSTALL.zip` or its identical RESTORE.
Do not deploy the old release ZIP or rebuild it as a replacement for r2.

No functional module changes: every original ZIP entry remains byte-identical
except install.sh/uninstall.sh. JAR, native libraries, native executable, config,
VERSION and MANIFEST_V2 are exactly the original baseline. Added: static QNX ARM
comparator, two binary self-test fixtures, installer-specific manifest and note.

The comparator is built in lab Actions 36907546435 from file_equal.c with the
pinned QNX toolchain, `-static`. SHA256:
`152c8262cc07bc9cff788f98ea80407a40785538e67d35c39043d5241b02aed8`.
No ELF interpreter or dynamic library dependencies. This is not a claim of
hardware validation; target self-tests must pass before modifying the app.

52 comparator cases and 5 full installer tests pass with system cmp forbidden,
including reinstall, absent comparator, failed difference test, failed copy
rollback and foreign launcher refusal. Existing 10 cluster payload tests pass.

Success is only `CLUSTER_2_0_R2_RESULT=PASS_COMMITTED`, after all installed files
were checked against baseline. Generic ModKit Done installing is not success.
Reboot required. Do not combine this package with diagnostic mods on the card.
