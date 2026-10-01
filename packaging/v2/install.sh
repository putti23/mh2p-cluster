#!/bin/ksh
# Cluster v2.0 install / restore baseline. No CP111 payloads, no process killing.
set -u
MOD_PATH="${modPath:-${MOD_PATH:-}}"
MEDIA_PATH="${mediaPath:-${MEDIA_PATH:-}}"
[[ -n "$MOD_PATH" && -n "$MEDIA_PATH" ]] || exit 1
APPS=/mnt/app/eso/bin/apps
CLUSTER="$APPS/cluster"
JARS=/mnt/app/eso/hmi/lsd/jars
BASELINE=/mnt/ota/modkit/cluster_baselines/2.0
COMMITTED=0
RW=0
JOURNAL=""

equal() { cmp "$1" "$2" >/dev/null 2>&1; }
fail() { print -u2 "Cluster v2.0 REFUSED: $*"; exit 1; }
finish() {
    if [[ "$COMMITTED" = 0 && -n "$JOURNAL" && -f "$JOURNAL" ]]; then
        while IFS='|' read -r dest backup existed; do
            if [[ "$existed" = 1 ]]; then
                cp -p "$backup" "$dest.v2.rollback" && equal "$backup" "$dest.v2.rollback" && mv "$dest.v2.rollback" "$dest" || print -u2 "ROLLBACK FAILED: $dest; backup=$backup"
            else
                rm -f "$dest"
            fi
        done < "$JOURNAL"
    fi
    sync
    [[ "$RW" = 0 ]] || mount -ur /mnt/app/ >/dev/null 2>&1
}
trap finish EXIT
trap 'exit 130' HUP INT TERM
command -v cmp >/dev/null 2>&1 || fail 'byte comparison tool missing'
[[ `id -u` = 0 ]] || fail 'installer must run through ModKit as root'
[[ -d "$JARS" && -d "$CLUSTER" ]] || fail 'existing cluster installation required'
for name in gal dio_manager; do
    [[ -f "$APPS/$name.real" ]] || fail "missing original $name.real"
    equal "$APPS/$name" "$MOD_PATH/$name" || fail "active $name is not the clean upstream wrapper; finish/remove diagnostics first"
done
for dir in /mnt/ota/modkit/Mods/CP111Diag*; do
    [[ ! -f "$dir/Persist/install.sh" ]] || fail 'active diagnostic hook remains; collect/remove first'
done
RELEASE_VERSION=`/mnt/app/armle/usr/bin/pc b:46924065:401 | cut -c 61- | sed ':a;N;$!ba;s/\n//g' | sed -e 's/\.//g' -e 's/ //g'`
case "$RELEASE_VERSION" in MH2p_*_PO*_P26??|MH2p_*_PO*_P28??) ;; *) fail "unsupported firmware $RELEASE_VERSION";; esac
FILES='cluster gal_cluster.so dio_cluster.so gal dio_manager cluster_config.json ClusterIntegration_v2.0.jar VERSION MANIFEST_V2.json'
for file in $FILES; do [[ -f "$MOD_PATH/$file" && ! -L "$MOD_PATH/$file" ]] || fail "missing payload $file"; done
[[ `cat "$MOD_PATH/VERSION"` = 2.0 ]] || fail 'wrong release marker'

# Immutable, explicit rollback baseline, never overwritten by a newer version.
if [[ -e "$BASELINE" ]]; then
    [[ -d "$BASELINE" && ! -L "$BASELINE" ]] || fail 'invalid baseline path'
    for file in $FILES; do equal "$BASELINE/$file" "$MOD_PATH/$file" || fail "baseline 2.0 differs: $file"; done
else
    [[ ! -e "$BASELINE.new" ]] || fail 'unfinished baseline staging; preserve for inspection'
    mkdir -p "$BASELINE.new" || fail 'cannot create baseline'
    for file in $FILES; do cp -p "$MOD_PATH/$file" "$BASELINE.new/$file" && equal "$MOD_PATH/$file" "$BASELINE.new/$file" || fail 'baseline copy failed'; done
    mv "$BASELINE.new" "$BASELINE" || fail 'baseline activation failed'
fi
stamp=`date +%Y%m%d_%H%M%S`
n=0
while [[ -e "$MEDIA_PATH/Backup/Cluster_v2.0_${stamp}_$n" ]]; do n=$((n+1)); done
BACKUP="$MEDIA_PATH/Backup/Cluster_v2.0_${stamp}_$n"
mkdir -p "$BACKUP" || fail 'cannot create SD backup'
JOURNAL="$BACKUP/rollback.txt"
touch "$JOURNAL" || fail 'cannot create rollback journal'
mount -uw /mnt/app/ || fail 'cannot remount app'; RW=1

remember() {
    dest="$1"; backup="$BACKUP/${dest##*/}"
    [[ ! -L "$dest" ]] || fail "symlink target $dest"
    if [[ -f "$dest" ]]; then
        cp -p "$dest" "$backup" && equal "$dest" "$backup" || fail "backup failed $dest"
        print "$dest|$backup|1" >> "$JOURNAL" || fail 'journal write failed'
    else
        [[ ! -e "$dest" ]] || fail "non-file target $dest"
        print "$dest|$backup|0" >> "$JOURNAL" || fail 'journal write failed'
    fi
}
install_file() {
    src="$1"; dest="$2"
    equal "$src" "$dest" && return 0
    remember "$dest"
    cp -p "$src" "$dest.v2.new" && equal "$src" "$dest.v2.new" || fail "stage failed $dest"
    mv "$dest.v2.new" "$dest" || fail "replace failed $dest"
}
for file in cluster gal_cluster.so dio_cluster.so; do
    install_file "$BASELINE/$file" "$CLUSTER/$file"
    chmod 755 "$CLUSTER/$file" || fail 'mode update failed'
done
install_file "$BASELINE/cluster_config.json" "$CLUSTER/cluster_config.json"
install_file "$BASELINE/ClusterIntegration_v2.0.jar" "$JARS/ClusterIntegration_v2.0.jar"
for jar in "$JARS"/ClusterIntegration_*.jar "$JARS"/AndroidAutoCluster_*.jar; do
    [[ -f "$jar" && "$jar" != "$JARS/ClusterIntegration_v2.0.jar" ]] || continue
    remember "$jar"
    rm -f "$jar" || fail "cannot retire old jar $jar"
done
install_file "$BASELINE/VERSION" "$CLUSTER/VERSION"
install_file "$BASELINE/MANIFEST_V2.json" "$CLUSTER/MANIFEST_V2.json"
COMMITTED=1
print 'Cluster v2.0 installed; RESTORE baseline=2.0; native map + CarPlay turn-by-turn'
print "Backup=$BACKUP; reboot required; no running process killed"
