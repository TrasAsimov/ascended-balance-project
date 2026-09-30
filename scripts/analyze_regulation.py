from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import struct

BASE = Path(__file__).parent


def u16str(buf, offset):
    if not offset or offset >= len(buf):
        return ''
    end = offset
    while end + 1 < len(buf) and buf[end:end + 2] != b'\0\0':
        end += 2
    return buf[offset:end].decode('utf-16le', 'replace')


def astr(buf, offset):
    if not offset or offset >= len(buf):
        return ''
    return buf[offset:buf.find(b'\0', offset)].decode('ascii', 'replace')


def read_bnd(path):
    b = path.read_bytes()
    assert b[:4] == b'BND4'
    count = struct.unpack_from('<I', b, 12)[0]
    assert struct.unpack_from('<Q', b, 16)[0] == 0x40
    tables = {}
    for i in range(count):
        flag, unknown, size, raw, off, ident, noff = struct.unpack_from('<IIQQIII', b, 0x40 + 0x24 * i)
        name = u16str(b, noff).split('\\')[-1].replace('.param', '')
        assert flag == 0x40 and ident == i and size == raw and off + size <= len(b), (i, name)
        tables[name] = read_param(b[off:off+size], name)
    return b[0x18:0x20].decode(), tables


def read_param(b, name):
    f = b[0x2d]
    count = struct.unpack_from('<H', b, 0xa)[0]
    if f & 0x80:
        ptype = astr(b, struct.unpack_from('<Q', b, 0x10)[0])
    else:
        ptype = astr(b, 0xc)
    off = 0x40 if f & 0x80 else 0x30
    width = 24 if f & 4 else 12
    entries = []
    for i in range(count):
        h = off + i * width
        if width == 24:
            rid, pad, dataoff, nameoff = struct.unpack_from('<iIQQ', b, h)
        else:
            rid, dataoff, nameoff = struct.unpack_from('<iII', b, h)
        entries.append((rid, dataoff, nameoff))
    starts = sorted(set(x[1] for x in entries if x[1]))
    gaps = [c-a for a,c in zip(starts,starts[1:]) if c>a]
    rsize = Counter(gaps).most_common(1)[0][0] if gaps else None
    if rsize is None and starts:
        e = struct.unpack_from('<I', b, 0)[0]
        rsize = e-starts[0]
    rows = {}
    for rid, dataoff, nameoff in entries:
        if not dataoff or not rsize or dataoff+rsize > len(b):
            continue
        rows[rid] = {'data':b[dataoff:dataoff+rsize], 'name':u16str(b,nameoff) if b[0x2e] & 4 else ''}
    return {'ptype':ptype,'flags':f,'row_size':rsize,'rows':rows,'file_size':len(b),'declared_rows':count}


def main():
    mv, m = read_bnd(BASE/'mod.bnd')
    vv, v = read_bnd(BASE/'vanilla.bnd')
    assert set(m)==set(v)
    summary=[]
    detail=[]
    for t in sorted(m):
        x,y=m[t],v[t]
        mx,vy=x['rows'],y['rows']
        added=sorted(mx.keys()-vy.keys()); removed=sorted(vy.keys()-mx.keys())
        common=mx.keys()&vy.keys()
        equal=[];changed=[];sizebad=[]
        for rid in sorted(common):
            a,b=mx[rid]['data'],vy[rid]['data']
            if len(a)!=len(b):
                sizebad.append(rid)
            elif a==b:equal.append(rid)
            else:changed.append(rid)
        summary.append({'table':t,'param_type':x['ptype'],'mod_rows':len(mx),'vanilla_rows':len(vy),'mod_row_size':x['row_size'],'vanilla_row_size':y['row_size'],'mod_only_rows':len(added),'vanilla_only_rows':len(removed),'changed_shared_rows':len(changed),'unchanged_shared_rows':len(equal),'different_size_shared_rows':len(sizebad)})
        for kind,ids in [('mod_only',added),('vanilla_only',removed),('changed_shared',changed),('different_size_shared',sizebad)]:
            for rid in ids:
                r=mx.get(rid) if kind!='vanilla_only' else vy.get(rid)
                a=mx.get(rid,{}).get('data',b'');b=vy.get(rid,{}).get('data',b'')
                diff=sum(p!=q for p,q in zip(a,b)) if kind=='changed_shared' else None
                detail.append({'table':t,'row_id':rid,'row_name':r['name'],'class':kind,'byte_differences':diff})
    (BASE/'comparison_summary.json').write_text(json.dumps({'mod_version':mv,'vanilla_version':vv,'tables':summary},ensure_ascii=False,indent=2))
    (BASE/'comparison_detail.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in detail)+'\n')
    print('versions',mv,vv,'table count',len(m))
    print('totals',{key:sum(r[key] for r in summary) for key in ('mod_rows','vanilla_rows','mod_only_rows','vanilla_only_rows','changed_shared_rows','unchanged_shared_rows','different_size_shared_rows')})
    print('size mismatch',[(r['table'],r['mod_row_size'],r['vanilla_row_size']) for r in summary if r['mod_row_size']!=r['vanilla_row_size']])
    print('most changed',[(r['table'],r['mod_only_rows'],r['changed_shared_rows']) for r in sorted(summary,key=lambda x:x['changed_shared_rows'],reverse=True)[:30]])

if __name__=='__main__':main()
