"""Reproducible v2.0 release from pinned upstream QNX/JAR artifacts.

No proprietary SDK is redistributed. Length/stack-neutral bytecode edits and
one same-length ELF string edit; source equivalents are committed alongside.
"""
import hashlib
import copy
import io
import json
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'builds/ClusterIntegration_v0034_beta2_candidate_90d0b76.zip'
# Actual pinned archive (deliberately separate from filenames/version labels).
BASE_SHA = '9211f5bdca37e246cc8dceb02a91121c54fa78623f94aa4c395afad1035bdb23'
PREFIX = 'Mods/ClusterIntegration/Update/'
OUT = ROOT / 'releases/v2.0'
TARGETS = ('de/audi/app/terminalmode/smartphone/carplay/CarPlayClusterIntegration.class',
           'de/audi/app/terminalmode/smartphone/androidauto2/nav/AndroidAutoClusterIntegration.class')
def sha(b): return hashlib.sha256(b).hexdigest()
def u2(b, p): return struct.unpack_from('>H', b, p)[0]
def u4(b, p): return struct.unpack_from('>I', b, p)[0]

def pool(b):
    assert b[:4] == b'\xca\xfe\xba\xbe'
    n = u2(b, 8); cp = [None] * n; i = 1; p = 10
    while i < n:
        tag = b[p]; p += 1
        if tag == 1:
            size = u2(b, p); p += 2
            cp[i] = (tag, b[p:p+size].decode('utf-8', 'replace')); p += size
        elif tag in (7,8,16,19,20): cp[i] = (tag, u2(b,p)); p += 2
        elif tag in (9,10,11,12,17,18): cp[i] = (tag,u2(b,p),u2(b,p+2)); p += 4
        elif tag in (3,4): cp[i] = (tag, b[p:p+4]); p += 4
        elif tag in (5,6): cp[i] = (tag,b[p:p+8]); p += 8; i += 1
        elif tag == 15: cp[i] = (tag,b[p],u2(b,p+1)); p += 3
        else: raise ValueError(('constant-pool tag',tag))
        i += 1
    return cp, p

def methods(b):
    cp,p = pool(b); p += 6
    p += 2 + 2*u2(b,p)
    fields = u2(b,p); p += 2
    for _ in range(fields):
        ac = u2(b,p+6); p += 8
        for _ in range(ac): p += 6 + u4(b,p+2)
    mc = u2(b,p); p += 2
    for _ in range(mc):
        name = cp[u2(b,p+2)][1]; ac = u2(b,p+6); p += 8
        for _ in range(ac):
            attr = cp[u2(b,p)][1]; length = u4(b,p+2); data = p+6
            if attr == 'Code':
                size = u4(b,data+4)
                yield name, data+8, bytes(b[data+8:data+8+size])
            p = data+length

def instructions(code):
    one = {0x10,0x12,0xa9,0xbc,*range(0x15,0x1a),*range(0x36,0x3b)}
    two = {0x11,0x13,0x14,0x84, *range(0x99,0xa9), *range(0xb2,0xb9),0xbb,0xbd,0xc0,0xc1,0xc6,0xc7}
    p = 0
    while p < len(code):
        op = code[p]
        if op in one: size=2
        elif op in two: size=3
        elif op in (0xb9,0xba,0xc8,0xc9): size=5
        elif op == 0xc5: size=4
        elif op == 0xc4: size=6 if code[p+1] == 0x84 else 4
        elif op in (0xaa,0xab):
            q = (p+4) & ~3
            if op == 0xaa:
                low,high = struct.unpack_from('>ii',code,q+4)
                assert high >= low
                size = q-p+12+4*(high-low+1)
            else: size = q-p+8+8*u4(code,q+4)
        else:
            assert op <= 0xc9 and op not in (0xca,), ('unknown opcode',op)
            size=1
        assert p+size <= len(code), ('truncated instruction',p,op)
        yield p,op
        p += size
    assert p == len(code)

def patch_class(original):
    cp,end = pool(original); count = len(cp)
    b = bytearray(original[:8] + struct.pack('>H',count+1) + original[10:end]
                  + b'\x03\x7f\xff\xff\xff' + original[end:])
    fields = {i for i,r in enumerate(cp) if r and r[0] == 9
              and cp[cp[r[2]][1]][1] == 'enableMapRender'
              and cp[cp[r[2]][2]][1] == 'Z'}
    assert len(fields) == 1, fields
    edits=[]; distances=0; gates=0
    for method,offset,code in methods(b):
        for p,op in instructions(code):
            if op == 0x11 and code[p+1:p+3] == b'\x4e\x20':
                b[offset+p:offset+p+3] = b'\x13'+struct.pack('>H',count)
                distances += 1; edits.append([method,p,'20km-limit -> Integer.MAX_VALUE'])
            if op == 0xb4 and u2(code,p+1) in fields:
                # objectref -> boolean becomes objectref -> pop -> false.
                # Same net stack effect and byte length, no branch/frame moves.
                b[offset+p:offset+p+3] = b'\x57\x03\x00'
                gates += 1; edits.append([method,p,'map-render read -> false'])
    assert distances == 1 and gates >= 3, (distances,gates)
    for _,_,code in methods(b):
        for p,op in instructions(code):
            assert not (op == 0xb4 and u2(code,p+1) in fields)
            assert not (op == 0x11 and code[p+1:p+3] == b'\x4e\x20')
    return bytes(b), edits

def patch_jar(data):
    out=io.BytesIO(); report={}
    with zipfile.ZipFile(io.BytesIO(data)) as old, zipfile.ZipFile(out,'w') as new:
        for entry in old.infolist():
            b=old.read(entry.filename)
            if entry.filename in TARGETS:
                before=sha(b); b,edits=patch_class(b)
                report[entry.filename]={'before':before,'after':sha(b),'edits':edits}
            if entry.filename.endswith('cluster_config.json'):
                cfg=json.loads(b); cfg['config']['enableMapRender']=False
                b=(json.dumps(cfg,indent=2)+'\n').encode()
            new.writestr(entry,b)
        marker=zipfile.ZipInfo('META-INF/CLUSTER_VERSION.txt')
        marker.compress_type=zipfile.ZIP_DEFLATED
        new.writestr(marker,'2.0\nNative map, phone turn-by-turn; no experimental stream111.\n')
    assert set(report) == set(TARGETS)
    return out.getvalue(),report

def main():
    assert sha(BASE.read_bytes()) == BASE_SHA
    OUT.mkdir(parents=True,exist_ok=True)
    replacements={}; manifest={'version':'2.0','rollback_baseline':'2.0','base_sha256':BASE_SHA}
    with zipfile.ZipFile(BASE) as old:
        jarname=next(n for n in old.namelist() if n.endswith('.jar'))
        jar,report=patch_jar(old.read(jarname)); manifest['classes']=report
        native=old.read(PREFIX+'cluster')
        assert sha(native) == '6057d531cae222b5bb016d2cbda6f19d2c1410420b8b00b615aba6372617923a'
        before=b'(c) 2026 fifthBro\0'; after=b'(c) fifthBro v2.0\0'
        assert len(before)==len(after) and native.count(before)==1
        replacements[PREFIX+'cluster']=native.replace(before,after)
        cfg=json.loads(old.read(PREFIX+'cluster_config.json')); cfg['config']['enableMapRender']=False
        replacements[PREFIX+'cluster_config.json']=(json.dumps(cfg,indent=2)+'\n').encode()
        replacements[PREFIX+'install.sh']=(ROOT/'packaging/v2/install.sh').read_bytes().replace(b'\r\n',b'\n')
        # Restore means reinstall baseline 2.0, NOT upstream's factory uninstall.
        replacements[PREFIX+'uninstall.sh']=replacements[PREFIX+'install.sh']
        replacements[PREFIX+'ClusterIntegration_v2.0.jar']=jar
        replacements['README_V2_PL.md']=(ROOT/'packaging/v2/README_PL.md').read_bytes().replace(b'\r\n',b'\n')
        replacements['Mods/ClusterIntegration/README.md']=replacements['README_V2_PL.md']
        replacements[PREFIX+'README.md']=replacements['README_V2_PL.md']
        replacements[PREFIX+'VERSION']=b'2.0\n'
        manifest['payload_sha256']={n:sha(b) for n,b in replacements.items()}
        replacements[PREFIX+'MANIFEST_V2.json']=(json.dumps(manifest,indent=2)+'\n').encode()
        for mode in ('INSTALL','RESTORE'):
            path=OUT/f'MH2P_Cluster_v2.0_{mode}.zip'
            with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as new:
                for entry in old.infolist():
                    name=entry.filename.replace('\\','/')
                    if entry.filename == jarname or name in replacements: continue
                    assert not name.endswith('uninstall.txt')
                    cloned=copy.copy(entry); cloned.filename=name
                    new.writestr(cloned,old.read(entry))
                for name,b in replacements.items():
                    entry=zipfile.ZipInfo(name); entry.compress_type=zipfile.ZIP_DEFLATED
                    entry.external_attr=0o100755<<16; new.writestr(entry,b)
            with zipfile.ZipFile(path) as check:
                assert check.testzip() is None
                assert len([n for n in check.namelist() if n.endswith('.jar')]) == 1
                assert not any('cp111' in n.lower() or 'altscreen' in n.lower() for n in check.namelist())
    (OUT/'MANIFEST_V2.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    sums=[f'{sha(p.read_bytes())}  {p.name}' for p in sorted(OUT.glob('*.zip'))]
    (OUT/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='ascii')
    print('\n'.join(sums)); print(json.dumps(report,indent=2))

if __name__ == '__main__': main()
