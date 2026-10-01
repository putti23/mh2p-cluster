import hashlib, json, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'releases/v2.0-r2/MH2P_Cluster_v2.0_r2_INSTALL.zip'
DIAG=ROOT.parent/'P780CarPlayAltScreenSD/v019/P780_DIAG_v0.19_r2_BASELINE_2.0.zip'
OUT=ROOT/'releases/full-uninstall-v1'
P='Mods/ClusterFullUninstall/Update/'
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    assert sha(BASE.read_bytes())=='272cf59c21f92ec4eb35c9aeaa642fe3ade5f59300787b595e4dcbf66a4c6c84'
    entries={}
    with zipfile.ZipFile(BASE) as z:
        for n in z.namelist():
            if n.startswith(('Data/','Meta/')) or n in ('LICENSE.md','Logs/README.md'):
                entries[n]=z.read(n)
        old='Mods/ClusterIntegration/Update/'
        for f in ('cluster','gal_cluster.so','dio_cluster.so','VERSION','MANIFEST_V2.json','ClusterIntegration_v2.0.jar','gal','dio_manager'):
            entries[P+'known/'+f]=z.read(old+f)
        entries[P+'known/persist.sh']=z.read('Mods/ClusterIntegration/Persist/install.sh')
        for f in ('qnx_file_equal','equal-a.bin','equal-b.bin'): entries[P+f]=z.read(old+f)
    assert sha(entries[P+'qnx_file_equal'])=='152c8262cc07bc9cff788f98ea80407a40785538e67d35c39043d5241b02aed8'
    with zipfile.ZipFile(DIAG) as z:
        lib=z.read('Mods/CarPlaySecondScreenProbe/Update/libp780_carplay_altscreen.so')
        assert sha(lib)=='d0fe6b242872557fc57b8ae9f63aa944f0d84e0aa48e75a1ca6f07316206e5c5'
        entries[P+'known/diag_v19.so']=lib
    entries[P+'install.sh']=(ROOT/'packaging/uninstall/install.sh').read_bytes().replace(b'\r\n',b'\n')
    entries['README_FULL_UNINSTALL_PL.md']=(ROOT/'packaging/uninstall/README_PL.md').read_bytes().replace(b'\r\n',b'\n')
    entries['README.md']=entries['README_FULL_UNINSTALL_PL.md']
    entries['MANIFEST_FULL_UNINSTALL.json']=json.dumps({'type':'FULL_UNINSTALL','version':1,'supported_module':'2.0','files':{n:sha(b) for n,b in entries.items()}},indent=2).encode()
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/'MH2P_Cluster_FULL_UNINSTALL_v1.zip'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(entries.items()):
            i=zipfile.ZipInfo(n); i.compress_type=zipfile.ZIP_DEFLATED; i.create_system=3; i.external_attr=0o100755<<16; z.writestr(i,b)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert not any('/Persist/' in n or n.endswith('uninstall.txt') for n in z.namelist())
        assert len([n for n in z.namelist() if n.endswith('/Update/install.sh')])==1
    (OUT/'SHA256SUMS.txt').write_text(sha(path.read_bytes())+'  '+path.name+'\n',encoding='ascii')
    print((OUT/'SHA256SUMS.txt').read_text())
if __name__=='__main__': main()
