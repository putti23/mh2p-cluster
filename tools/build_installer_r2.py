"""Installer repair only. Preserve every functional v2.0 baseline byte."""
import argparse, hashlib, json, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'releases/v2.0/MH2P_Cluster_v2.0_INSTALL.zip'
OUT=ROOT/'releases/v2.0-r2'
PREFIX='Mods/ClusterIntegration/Update/'
BASE_SHA='d38df19afe3cec7d7347b1a24cfdc410eaa9bdd72edc1669a2c6fead4f6c13bb'
def sha(b): return hashlib.sha256(b).hexdigest()
def build(helper, expected):
    assert sha(BASE.read_bytes())==BASE_SHA
    data=helper.read_bytes(); assert sha(data)==expected
    assert data[:6]==b'\x7fELF\x01\x01' and data[18:20]==b'\x28\0'
    OUT.mkdir(exist_ok=True)
    with zipfile.ZipFile(BASE) as z: entries={n:z.read(n) for n in z.namelist()}
    script=(ROOT/'packaging/v2/install-r2.sh').read_bytes().replace(b'\r\n',b'\n')
    entries[PREFIX+'install.sh']=script; entries[PREFIX+'uninstall.sh']=script
    entries[PREFIX+'qnx_file_equal']=data
    entries[PREFIX+'equal-a.bin']=bytes(range(256))
    entries[PREFIX+'equal-b.bin']=bytes(range(255))+b'\0'
    note=('Cluster 2.0 — instalator r2\n\nNaprawa instalatora: brak zaleznosci od systemowego cmp.\n'
          'Funkcjonalne pliki 2.0 i MANIFEST_V2 pozostaja niezmienione.\n'
          'Po instalacji wymagany restart. Sukces tylko gdy log ClusterIntegration.log\n'
          'zawiera CLUSTER_2_0_R2_RESULT=PASS_COMMITTED. Sam Done installing nie wystarcza.\n'
          'Wersja diagnostyczna NIE jest czescia tej karty.\n').encode()
    entries['README_INSTALLER_R2.txt']=note
    report={'module':'2.0','installer':'r2','original_zip_sha256':BASE_SHA,
            'helper_sha256':expected,'files':{n:sha(b) for n,b in entries.items()}}
    entries['MANIFEST_INSTALLER_R2.json']=json.dumps(report,indent=2).encode()
    for mode in ('INSTALL','RESTORE'):
        path=OUT/f'MH2P_Cluster_v2.0_r2_{mode}.zip'
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            for n,b in sorted(entries.items()):
                info=zipfile.ZipInfo(n); info.compress_type=zipfile.ZIP_DEFLATED
                info.create_system=3; info.external_attr=0o100755<<16; z.writestr(info,b)
        with zipfile.ZipFile(path) as z, zipfile.ZipFile(BASE) as old:
            assert z.testzip() is None
            for n in old.namelist():
                if n not in (PREFIX+'install.sh',PREFIX+'uninstall.sh'):
                    assert z.read(n)==old.read(n),n
    (OUT/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(OUT.glob('*.zip'))),encoding='ascii')
    print((OUT/'SHA256SUMS.txt').read_text())
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('helper',type=Path); p.add_argument('--sha256',required=True)
    a=p.parse_args(); build(a.helper,a.sha256)
