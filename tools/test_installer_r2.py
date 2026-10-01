import os, shutil, subprocess, tempfile, unittest, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent
BASH=shutil.which('bash') or r'C:\Program Files\Git\bin\bash.exe'
HELPER=WORK/'.tools/file_equal.exe'
PREFIX='Mods/ClusterIntegration/Update/'
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='r2-test-',dir=WORK/'.tools')
        self.r=Path(self.tmp.name); self.mod=self.r/'package'; self.mod.mkdir()
        with zipfile.ZipFile(ROOT/'releases/v2.0/MH2P_Cluster_v2.0_INSTALL.zip') as z:
            for n in z.namelist():
                if n.startswith(PREFIX) and not n.endswith('/'):
                    (self.mod/n[len(PREFIX):]).write_bytes(z.read(n))
        self.apps=self.r/'mnt/app/eso/bin/apps'; self.cluster=self.apps/'cluster'
        self.jars=self.r/'mnt/app/eso/hmi/lsd/jars'
        self.cluster.mkdir(parents=True); self.jars.mkdir(parents=True)
        for f in ('gal','dio_manager'):
            shutil.copyfile(self.mod/f,self.apps/f); (self.apps/(f+'.real')).write_bytes(b'original')
        (self.cluster/'cluster').write_bytes(b'old executable')
        (self.cluster/'cluster_config.json').write_bytes(b'old user config')
        (self.jars/'ClusterIntegration_old.jar').write_bytes(b'old jar')
        (self.r/'mnt/ota/modkit/cluster_baselines').mkdir(parents=True)
        (self.r/'mnt/ota/modkit/Mods').mkdir()
        self.media=self.r/'media'; self.media.mkdir()
        pc=self.r/'mnt/app/armle/usr/bin/pc'; pc.parent.mkdir(parents=True)
        pc.write_text('#!/bin/sh\nprintf "%060d%s\\n" 0 MH2p_ER_PO416_P2800\n',newline='\n'); pc.chmod(0o755)
        shutil.copyfile(HELPER,self.mod/'qnx_file_equal')
        (self.mod/'equal-a.bin').write_bytes(bytes(range(256)))
        (self.mod/'equal-b.bin').write_bytes(bytes(range(255))+b'\0')
        s=(ROOT/'packaging/v2/install-r2.sh').read_text().replace('/mnt/',self.r.as_posix()+'/mnt/')
        (self.mod/'install.sh').write_text(s,newline='\n')
    def tearDown(self): self.tmp.cleanup()
    def run_installer(self,extra=''):
        script=f'''export PATH=/usr/bin:/bin:$PATH
print() {{ if [[ "$1" = -u2 ]]; then shift; printf '%s\\n' "$*" >&2; else printf '%s\\n' "$*"; fi; }}
cmp() {{ echo FORBIDDEN_SYSTEM_CMP >&2; return 127; }}
id() {{ echo 0; }}
mount() {{ return 0; }}
sync() {{ return 0; }}
{extra}
MOD_PATH='{self.mod.as_posix()}' MEDIA_PATH='{self.media.as_posix()}'
. "$MOD_PATH/install.sh"
'''
        p=subprocess.run([BASH,'-c',script],capture_output=True,text=True,encoding='utf-8',errors='replace')
        self.assertNotIn('FORBIDDEN_SYSTEM_CMP',p.stderr)
        return p
    def test_full_install_without_system_cmp_and_reinstall(self):
        for _ in range(2):
            p=self.run_installer(); self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertIn('PASS_COMMITTED',p.stdout)
            for f in ('cluster','gal_cluster.so','dio_cluster.so','cluster_config.json','VERSION','MANIFEST_V2.json'):
                self.assertEqual((self.cluster/f).read_bytes(),(self.mod/f).read_bytes())
            self.assertEqual((self.jars/'ClusterIntegration_v2.0.jar').read_bytes(),(self.mod/'ClusterIntegration_v2.0.jar').read_bytes())
            self.assertFalse((self.jars/'ClusterIntegration_old.jar').exists())
    def test_missing_helper_no_mutation(self):
        (self.mod/'qnx_file_equal').unlink()
        p=self.run_installer(); self.assertNotEqual(p.returncode,0)
        self.assertIn('positive self-test failed',p.stderr)
        self.assertEqual((self.cluster/'cluster').read_bytes(),b'old executable')
        self.assertFalse((self.r/'mnt/ota/modkit/cluster_baselines/2.0').exists())
    def test_helper_always_equal_refused(self):
        (self.mod/'equal-b.bin').write_bytes((self.mod/'equal-a.bin').read_bytes())
        p=self.run_installer(); self.assertNotEqual(p.returncode,0)
        self.assertIn('difference self-test failed',p.stderr)
        self.assertEqual((self.cluster/'cluster').read_bytes(),b'old executable')
    def test_failed_stage_rolls_back(self):
        p=self.run_installer('''cp() {
case "${@: -1}" in *gal_cluster.so.v2.new) return 9;; esac
command cp "$@"
}''')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('stage failed',p.stderr)
        self.assertIn('RESULT=FAILED',p.stdout)
        self.assertEqual((self.cluster/'cluster').read_bytes(),b'old executable')
        self.assertFalse((self.cluster/'gal_cluster.so').exists())
        self.assertTrue((self.jars/'ClusterIntegration_old.jar').exists())
    def test_foreign_launcher_refused(self):
        (self.apps/'dio_manager').write_bytes(b'foreign')
        p=self.run_installer(); self.assertNotEqual(p.returncode,0)
        self.assertEqual((self.apps/'dio_manager').read_bytes(),b'foreign')
if __name__=='__main__': unittest.main(verbosity=2)
