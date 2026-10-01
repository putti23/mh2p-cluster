# FULL UNINSTALL v1 verification

Built from pinned 2.0-r2 ZIP 272cf59c21f92ec4eb35c9aeaa642fe3ade5f59300787b595e4dcbf66a4c6c84.
The comparison helper is the same static QNX ARM helper used by r2, SHA256
152c8262cc07bc9cff788f98ea80407a40785538e67d35c39043d5241b02aed8.
Its 52 host binary/error cases and QNX static linkage checks were completed in
the r2 build. The uninstaller repeats equal/different/missing-file self-tests
on the device before changing files.

Nine host installer scenarios, with system cmp forbidden:
complete uninstall + repeat, missing original, unknown active launcher, active
diagnostic, unknown/future JAR, missing comparator, failed SD backup, failure
halfway through removal (rollback), failure while staging an original (rollback).
Firmware command, mount, UID and sync are mocked on host fixtures. QNX/vehicle
execution is NOT validated by these tests.

The outer ModKit updater is retained unchanged. This package uses a separate
ClusterFullUninstall update entry, not the generic uninstall.txt marker that
could trigger outer cleanup even after a refused script. It has no Persist/Post
payloads. It only removes the byte-matched ClusterIntegration persist script
inside its verified backup/journal transaction. Never deploy with another mod.

Only known 2.0 payloads are removed. Original .real backups, the 2.0 recovery
baseline, logs, other mods and inert older diagnostic remnants are preserved.
The v19 library and clean launcher are removed only when byte-matched.
No automatic process kills/reboots, no network or system cmp dependency.
Power loss and SD loss remain outside a guarantee of automatic rollback.
