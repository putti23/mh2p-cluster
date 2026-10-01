import shutil, unittest, zipfile
from test_installer_r2 import InstallerTests, ROOT, HELPER

class UninstallTests(unittest.TestCase):
    def setUp(self):
        InstallerTests.setUp(self)
        with zipfile.ZipFile(ROOT/'releases/full-uninstall-v1/MH2P_Cluster_FULL_UNINSTALL_v1.zip') as z:
            prefix='Mods/ClusterFullUninstall/Update/'
            for n in z.namelist():
                if n.startswith(prefix) and not n.endswith('/'):
                    p=self.mod/n[len(prefix):]; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(z.read(n))
        shutil.copyfile(HELPER,self.mod/'qnx_file_equal')
        source=(ROOT/'packaging/uninstall/install.sh').read_text().replace('/mnt/',self.r.as_posix()+'/mnt/')
        (self.mod/'install.sh').write_text(source,newline='\n')
        for name in ('cluster','gal_cluster.so','dio_cluster.so','VERSION','MANIFEST_V2.json'):
            shutil.copyfile(self.mod/'known'/name,self.cluster/name)
        for name in ('gal','dio_manager'):
            # Executable host fixture, never run. Windows chmod alone cannot
            # model QNX execute bits for a plain text .real file in Git Bash.
            (self.apps/(name+'.real')).write_bytes(b'#!/bin/sh\nexit 0\n')
            (self.apps/(name+'.real')).chmod(0o755)
        (self.jars/'ClusterIntegration_old.jar').unlink()
        shutil.copyfile(self.mod/'known/ClusterIntegration_v2.0.jar',self.jars/'ClusterIntegration_v2.0.jar')
        self.persist=self.r/'mnt/ota/modkit/Mods/ClusterIntegration/Persist/install.sh'
        self.persist.parent.mkdir(parents=True); shutil.copyfile(self.mod/'known/persist.sh',self.persist)
    tearDown=InstallerTests.tearDown
    run_installer=InstallerTests.run_installer
    def assert_installed(self):
        for n in ('gal','dio_manager'): self.assertEqual((self.apps/n).read_bytes(),(self.mod/'known'/n).read_bytes())
        self.assertTrue((self.cluster/'cluster').exists()); self.assertTrue(self.persist.exists())
        self.assertTrue((self.jars/'ClusterIntegration_v2.0.jar').exists())
    def test_complete_and_idempotent_without_cmp(self):
        shutil.copyfile(self.mod/'known/dio_manager',self.apps/'dio_manager.v19.clean')
        shutil.copyfile(self.mod/'known/diag_v19.so',self.cluster/'libp780_carplay_altscreen_v19.so')
        (self.cluster/'unrelated.txt').write_bytes(b'preserve')
        for _ in range(2):
            p=self.run_installer(); self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertIn('PASS_COMMITTED',p.stdout)
            for n in ('gal','dio_manager'):
                self.assertEqual((self.apps/n).read_bytes(),(self.apps/(n+'.real')).read_bytes())
            self.assertFalse(self.persist.exists()); self.assertFalse((self.cluster/'cluster').exists())
            self.assertFalse((self.jars/'ClusterIntegration_v2.0.jar').exists())
            self.assertFalse((self.apps/'dio_manager.v19.clean').exists())
            self.assertFalse((self.cluster/'libp780_carplay_altscreen_v19.so').exists())
            self.assertEqual((self.cluster/'unrelated.txt').read_bytes(),b'preserve')
    def test_missing_original_refused(self):
        (self.apps/'gal.real').unlink()
        p=self.run_installer(); self.assertNotEqual(p.returncode,0)
        self.assertIn('missing_saved_original',p.stderr); self.assert_installed()
    def test_unknown_launcher_refused(self):
        (self.apps/'gal').write_bytes(b'foreign')
        p=self.run_installer(); self.assertNotEqual(p.returncode,0)
        self.assertIn('unknown_active_launcher',p.stderr)
        self.assertEqual((self.apps/'gal').read_bytes(),b'foreign')
        self.assertTrue(self.persist.exists())
    def test_active_diagnostic_refused(self):
        p=self.r/'mnt/ota/modkit/Mods/CP111DiagV19/Persist/install.sh'
        p.parent.mkdir(parents=True); p.write_bytes(b'active')
        result=self.run_installer(); self.assertNotEqual(result.returncode,0)
        self.assertIn('finish_diagnostic_first',result.stderr); self.assert_installed()
    def test_unknown_jar_refused(self):
        (self.jars/'ClusterIntegration_v2.1.jar').write_bytes(b'future')
        p=self.run_installer(); self.assertNotEqual(p.returncode,0)
        self.assertIn('unknown_jar',p.stderr); self.assert_installed()
    def test_missing_comparator_refused(self):
        (self.mod/'qnx_file_equal').unlink()
        p=self.run_installer(); self.assertNotEqual(p.returncode,0)
        self.assertIn('comparator_positive',p.stderr); self.assert_installed()
    def test_backup_failure_no_system_changes(self):
        p=self.run_installer('''cp() { case "${@: -1}" in */files/4) return 9;; esac; command cp "$@"; }''')
        self.assertNotEqual(p.returncode,0); self.assertIn('backup_failed',p.stderr)
        self.assert_installed()
    def test_mid_removal_failure_restores_all(self):
        p=self.run_installer('''rm() { case "${@: -1}" in */cluster_config.json) return 9;; esac; command rm "$@"; }''')
        self.assertNotEqual(p.returncode,0); self.assertIn('FULL_UNINSTALL_RESULT=FAILED',p.stdout)
        self.assertIn('remove:',p.stderr)
        self.assert_installed()
        self.assertEqual((self.cluster/'cluster_config.json').read_bytes(),b'old user config')
    def test_original_staging_failure_rolls_back(self):
        p=self.run_installer('''cp() { case "${@: -1}" in *dio_manager.fulluninstall.new) return 9;; esac; command cp "$@"; }''')
        self.assertNotEqual(p.returncode,0); self.assertIn('restore_original',p.stderr)
        self.assert_installed()

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(UninstallTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
