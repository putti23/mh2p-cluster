#!/bin/ksh
# Cluster FULL UNINSTALL v1. Never removes ModKit or other modifications.
set -u
unset LD_PRELOAD
MOD_PATH="${modPath:-${MOD_PATH:-}}"
MEDIA_PATH="${mediaPath:-${MEDIA_PATH:-}}"
[[ -n "$MOD_PATH" && -n "$MEDIA_PATH" ]] || exit 1
APPS=/mnt/app/eso/bin/apps
CLUSTER="$APPS/cluster"
JARS=/mnt/app/eso/hmi/lsd/jars
PERSIST=/mnt/ota/modkit/Mods/ClusterIntegration/Persist/install.sh
RW=0; COMMITTED=0; JOURNAL=""
equal() { [[ -f "$1" && -f "$2" && ! -L "$1" && ! -L "$2" ]] && "$MOD_PATH/qnx_file_equal" "$1" "$2" >/dev/null 2>&1; }
fail() { print -u2 "FULL_UNINSTALL_REFUSED: $*"; exit 1; }
finish() {
    rc=$?
    if [[ "$COMMITTED" = 0 && -n "$JOURNAL" && -f "$JOURNAL" ]]; then
        while IFS='|' read -r kind dest saved; do
            [[ "$kind" != F ]] || continue
            cp -p "$saved" "$dest.fulluninstall.rollback" &&
                equal "$saved" "$dest.fulluninstall.rollback" &&
                mv "$dest.fulluninstall.rollback" "$dest" || {
                    print -u2 "ROLLBACK_FAILED dest=$dest backup=$saved"; rc=1;
                }
        done < "$JOURNAL"
    fi
    sync
    if [[ "$RW" = 1 ]]; then mount -ur /mnt/app/ || rc=1; fi
    if [[ "$COMMITTED" = 1 && "$rc" = 0 ]]; then
        print 'CLUSTER_FULL_UNINSTALL_RESULT=PASS_COMMITTED restart_required=yes'
    else
        print 'CLUSTER_FULL_UNINSTALL_RESULT=FAILED keep_backup=yes'
        [[ "$rc" != 0 ]] || rc=1
    fi
    exit "$rc"
}
trap finish EXIT
trap 'exit 130' HUP INT TERM
[[ `id -u` = 0 ]] || fail root_required
for tool in cp mv rm mkdir chmod sync mount grep awk cut sed date touch; do
    command -v "$tool" >/dev/null 2>&1 || fail "tool_missing:$tool"
done
equal "$MOD_PATH/equal-a.bin" "$MOD_PATH/equal-a.bin" || fail comparator_positive
"$MOD_PATH/qnx_file_equal" "$MOD_PATH/equal-a.bin" "$MOD_PATH/equal-b.bin" >/dev/null 2>&1
[[ $? = 1 ]] || fail comparator_negative
[[ ! -e "$MOD_PATH/selftest-must-not-exist" ]] || fail comparator_fixture
"$MOD_PATH/qnx_file_equal" "$MOD_PATH/equal-a.bin" "$MOD_PATH/selftest-must-not-exist" >/dev/null 2>&1
[[ $? = 2 ]] || fail comparator_error
FW=`/mnt/app/armle/usr/bin/pc b:46924065:401 | cut -c 61- | sed ':a;N;$!ba;s/\n//g' | sed -e 's/\.//g' -e 's/ //g'`
case "$FW" in MH2p_*_PO*_P26??|MH2p_*_PO*_P28??) ;; *) fail "unsupported_firmware:$FW";; esac
for dir in /mnt/ota/modkit/Mods/CP111Diag* /mnt/ota/modkit/Mods/CarPlaySecondScreenProbe; do
    [[ ! -f "$dir/Persist/install.sh" && ! -f "$dir/Post/install.sh" ]] || fail "finish_diagnostic_first:$dir"
done
[[ ! -f /mnt/ota/modkit/Mods/ClusterIntegration/Post/install.sh ]] || fail unknown_cluster_post_hook
for name in gal dio_manager; do
    [[ -f "$APPS/$name.real" && -x "$APPS/$name.real" && ! -L "$APPS/$name.real" ]] || fail "missing_saved_original:$name"
    if equal "$APPS/$name" "$MOD_PATH/known/$name"; then :
    elif equal "$APPS/$name" "$APPS/$name.real"; then :
    else fail "unknown_active_launcher:$name"; fi
done
[[ ! -L "$CLUSTER" && ! -L "$JARS" && ! -L "${PERSIST%/install.sh}" ]] || fail symlink_directory
if [[ -e "$PERSIST" ]]; then equal "$PERSIST" "$MOD_PATH/known/persist.sh" || fail unknown_persist; fi
# Refuse unknown/newer functional versions rather than delete by wildcard.
for name in cluster gal_cluster.so dio_cluster.so VERSION MANIFEST_V2.json; do
    if [[ -e "$CLUSTER/$name" ]]; then equal "$CLUSTER/$name" "$MOD_PATH/known/$name" || fail "unknown_cluster_payload:$name"; fi
done
for jar in "$JARS"/ClusterIntegration_* "$JARS"/AndroidAutoCluster_*; do
    [[ -e "$jar" ]] || continue
    equal "$jar" "$MOD_PATH/known/ClusterIntegration_v2.0.jar" || fail "unknown_jar:$jar"
done
# Only known inert v19 artifacts are eligible; other diagnostic evidence stays.
if [[ -e "$APPS/dio_manager.v19.clean" ]]; then
    equal "$APPS/dio_manager.v19.clean" "$MOD_PATH/known/dio_manager" || fail unknown_v19_clean
fi
if [[ -e "$CLUSTER/libp780_carplay_altscreen_v19.so" ]]; then
    equal "$CLUSTER/libp780_carplay_altscreen_v19.so" "$MOD_PATH/known/diag_v19.so" || fail unknown_v19_library
fi
stamp=`date +%Y%m%d_%H%M%S`; n=0
while [[ -e "$MEDIA_PATH/Backup/Cluster_FULL_UNINSTALL_${stamp}_$n" ]]; do n=$((n+1)); done
BACKUP="$MEDIA_PATH/Backup/Cluster_FULL_UNINSTALL_${stamp}_$n"
mkdir -p "$BACKUP/files" || fail backup_directory
PLAN="$BACKUP/plan.txt"
touch "$PLAN" || fail plan_create
INDEX=0
save() {
    kind="$1"; dest="$2"
    [[ -e "$dest" || -L "$dest" ]] || return 0
    [[ -f "$dest" && ! -L "$dest" ]] || fail "nonregular:$dest"
    [[ ! -e "$dest.fulluninstall.new" && ! -e "$dest.fulluninstall.rollback" ]] || fail "stale_stage:$dest"
    INDEX=$((INDEX+1)); saved="$BACKUP/files/$INDEX"
    cp -p "$dest" "$saved" && equal "$dest" "$saved" || fail "backup_failed:$dest"
    print "$kind|$dest|$saved" >> "$PLAN" || fail plan_write
}
for name in gal dio_manager; do save F "$APPS/$name.real"; save R "$APPS/$name"; done
for name in cluster gal_cluster.so dio_cluster.so cluster_config.json VERSION MANIFEST_V2.json libp780_carplay_altscreen_v19.so; do save D "$CLUSTER/$name"; done
for jar in "$JARS"/ClusterIntegration_* "$JARS"/AndroidAutoCluster_*; do [[ ! -e "$jar" ]] || save D "$jar"; done
save D "$APPS/dio_manager.v19.clean"
save D "$PERSIST"
# No writes to system files until every backup has been verified.
mount -uw /mnt/app/ || fail remount; RW=1
JOURNAL="$BACKUP/applied.txt"
touch "$JOURNAL" || fail journal_create
while IFS='|' read -r kind dest saved; do
    [[ "$kind" != F ]] || continue
    equal "$dest" "$saved" || fail "file_changed_after_backup:$dest"
    print "$kind|$dest|$saved" >> "$JOURNAL" || fail journal_write
    case "$kind" in
        R) factory_saved=`awk -F '|' -v target="$dest.real" '$1=="F" && $2==target {print $3}' "$PLAN"`
           equal "$dest.real" "$factory_saved" || fail "original_changed_after_backup:$dest"
           cp -p "$factory_saved" "$dest.fulluninstall.new" &&
           equal "$factory_saved" "$dest.fulluninstall.new" &&
           chmod 755 "$dest.fulluninstall.new" &&
           mv "$dest.fulluninstall.new" "$dest" || fail "restore_original:$dest";;
        D) rm -f "$dest" || fail "remove:$dest";;
        *) fail invalid_plan;;
    esac
done < "$PLAN"
for name in gal dio_manager; do equal "$APPS/$name" "$APPS/$name.real" || fail "verify_original:$name"; done
while IFS='|' read -r kind dest saved; do
    [[ "$kind" != D || ! -e "$dest" ]] || fail "still_present:$dest"
done < "$PLAN"
COMMITTED=1
print "Backup=$BACKUP"
print 'Scope=cluster_2.0 active_diagnostics=REFUSED ModKit=KEPT saved_originals=KEPT logs_and_baselines=KEPT'
print 'Restart PCM after completion. Current processes are not killed by this script.'
