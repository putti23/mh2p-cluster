# PCM/P780 installer rules

System cmp is unavailable in ModKit update context (confirmed vehicle log).
Never deploy the historical v2.0 installer; use packaging/v2/install-r2.sh and
tools/build_installer_r2.py with the pinned static QNX helper. Do not replace
binary verification with text comparison, file size, or an assumed hash tool.
Test positive/different/missing comparator results before target writes.
Test full installer with system cmp forbidden. Host tests do not prove QNX ABI.
tcpdump failed to load librpc.so.2 in update context; do not depend on it.
Generic ModKit Done installing is not success. Require PASS_COMMITTED and
verification of installed files. Preserve backups, logs, and unknown changes.
Cluster payload 2.0 is immutable; r2 repairs installation only. Future module
changes are 2.1, 2.2 etc. Never mix stable and diagnostic mods on one SD card.
