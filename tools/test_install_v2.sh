#!/bin/bash
# Transaction helpers from production script, isolated paths and mount mocked.
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
t=$(mktemp -d /tmp/cluster-v2-test.XXXXXXXX)
case "$t" in /tmp/cluster-v2-test.*) ;; *) exit 1;; esac
trap 'rm -r -- "$t"' EXIT
sed -n '/^equal()/,/^trap finish EXIT/p' "$root/packaging/v2/install.sh" | sed '$d' > "$t/functions"
sed -n '/^remember()/,/^for file in cluster /p' "$root/packaging/v2/install.sh" | sed '$d' >> "$t/functions"
print() { if [[ "$1" = -u2 ]]; then shift; printf '%s\n' "$*" >&2; else printf '%s\n' "$*"; fi; }
sync() { :; }; mount() { :; }
mkdir "$t/backup" "$t/dest"
echo old > "$t/dest/a"; echo new > "$t/source"
(
    source "$t/functions"
    COMMITTED=0; RW=0; BACKUP="$t/backup"; JOURNAL="$BACKUP/journal"; touch "$JOURNAL"
    trap finish EXIT
    install_file "$t/source" "$t/dest/a"
    install_file "$t/source" "$t/dest/b"
    # Simulate failure later in transaction: restore a, remove newly-created b.
)
grep -q old "$t/dest/a"; [[ ! -e "$t/dest/b" ]]
(
    source "$t/functions"
    COMMITTED=0; RW=0; BACKUP="$t/backup"; JOURNAL="$BACKUP/journal2"; touch "$JOURNAL"
    trap finish EXIT
    install_file "$t/source" "$t/dest/a"
    COMMITTED=1
)
grep -q new "$t/dest/a"
if (
    source "$t/functions"
    COMMITTED=0; RW=0; BACKUP="$t/backup"; JOURNAL="$BACKUP/journal3"; touch "$JOURNAL"
    trap finish EXIT
    cp() { case "${@: -1}" in *.v2.new) return 9;; *) command cp "$@";; esac; }
    install_file "$t/source" "$t/dest/c"
); then echo 'FAIL staging error ignored'; exit 1; fi
[[ ! -e "$t/dest/c" ]]
echo 'PASS: failed transaction restores old/removes new, successful commit persists, staging failure refuses'
