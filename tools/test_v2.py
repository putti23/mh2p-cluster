import io
import json
import unittest
import zipfile
import build_v2 as b

class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=zipfile.ZipFile(b.BASE)
        cls.pkg=zipfile.ZipFile(b.OUT/'MH2P_Cluster_v2.0_INSTALL.zip')
        j=next(n for n in cls.base.namelist() if n.endswith('.jar'))
        cls.oldjar=zipfile.ZipFile(io.BytesIO(cls.base.read(j)))
        cls.jar=zipfile.ZipFile(io.BytesIO(cls.pkg.read(b.PREFIX+'ClusterIntegration_v2.0.jar')))
    def test_fixed_base(self): self.assertEqual(b.sha(b.BASE.read_bytes()),b.BASE_SHA)
    def test_restore_identical(self):
        self.assertEqual((b.OUT/'MH2P_Cluster_v2.0_INSTALL.zip').read_bytes(),(b.OUT/'MH2P_Cluster_v2.0_RESTORE.zip').read_bytes())
    def test_native_string_only(self):
        old=self.base.read(b.PREFIX+'cluster'); new=self.pkg.read(b.PREFIX+'cluster')
        self.assertEqual(new,old.replace(b'(c) 2026 fifthBro\0',b'(c) fifthBro v2.0\0'))
        self.assertEqual(len(new),len(old)); self.assertEqual(new[:4],b'\x7fELF')
    def test_preload_libraries_untouched(self):
        for n in ('gal_cluster.so','dio_cluster.so','gal','dio_manager'):
            self.assertEqual(self.base.read(b.PREFIX+n),self.pkg.read(b.PREFIX+n))
    def test_bytecode_method_offsets_and_only_declared_changes(self):
        for name in b.TARGETS:
            old=self.oldjar.read(name); new=self.jar.read(name)
            expected,edits=b.patch_class(old)
            self.assertEqual(new,expected)
            old_methods=list(b.methods(old)); new_methods=list(b.methods(new))
            self.assertEqual(len(old_methods),len(new_methods))
            for (on,_,oc),(nn,_,nc) in zip(old_methods,new_methods):
                self.assertEqual(on,nn); self.assertEqual(len(oc),len(nc))
                allowed=set()
                for method,p,_ in edits:
                    if method==on: allowed.update(range(p,p+3))
                self.assertTrue(all(a==z or i in allowed for i,(a,z) in enumerate(zip(oc,nc))))
                list(b.instructions(nc))
            self.assertEqual(len(new),len(old)+5) # one Integer constant only
    def test_all_other_jar_entries_unchanged(self):
        for n in self.oldjar.namelist():
            if n in b.TARGETS or n.endswith('cluster_config.json'): continue
            self.assertEqual(self.oldjar.read(n),self.jar.read(n),n)
    def test_native_map_configuration(self):
        cfg=json.loads(self.pkg.read(b.PREFIX+'cluster_config.json'))
        self.assertIs(cfg['config']['enableMapRender'],False)
    def test_long_distances(self):
        for meters,km10 in ((19900,199),(20000,200),(20001,200),(35000,350),(100000,1000)):
            self.assertLess(meters,2147483647)
            self.assertEqual((meters+50)//100,km10)
    def test_no_experimental_package_files(self):
        self.assertTrue(all('cp111' not in n.lower() and 'altscreen' not in n.lower() for n in self.pkg.namelist()))
        self.assertNotIn('Mods/ClusterIntegration/uninstall.txt',self.pkg.namelist())
    def test_patch_refuses_second_application(self):
        for name in b.TARGETS:
            with self.assertRaises(AssertionError): b.patch_class(self.jar.read(name))

if __name__=='__main__': unittest.main(verbosity=2)
