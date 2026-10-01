"""Conservative ER PARAM/BND4 and EMEVD editing; untouched records stay intact."""
from pathlib import Path
import struct, zlib, json

def param_patch(raw, changes, added, size):
    """Patch resident rows in place, then extend the existing row directory.

    Existing data, names, null pointers, padding and opaque tail bytes are
    retained. Additions use the append strategy in build_v03.insert_rows,
    also used by the game-tested v0.4+ lineage. No string re-encoding or
    whole-table row packing occurs. Runtime acceptance still needs testing.
    """
    assert len(raw)>=64 and raw[0x2c]==0
    assert raw[0x2d] & 0x84 == 0x84
    count=struct.unpack_from('<H',raw,10)[0]
    assert count+len(added)<65536 and size>0
    end=64+24*count
    assert end<=len(raw)
    records=[struct.unpack_from('<iIQQ',raw,64+24*i) for i in range(count)]
    ids={r[0] for r in records}
    assert len(ids)==count and set(changes)<=ids and not set(added)&ids
    out=bytearray(raw)
    for rid,pad,off,name in records:
        assert end<=off and off+size<=len(raw),(rid,off,size)
        if rid in changes:
            assert len(changes[rid])==size
            out[off:off+size]=changes[rid]
    if not added:
        return bytes(out)
    delta=24*len(added)
    out[end:end]=bytes(delta)
    # StringsOffset is uint32; the type and data-start pointers are uint64.
    # Never read the first eight bytes as one pointer (Unk06 lives at 6).
    for pos,fmt in [(0,'I'),(0x10,'Q'),(0x30,'Q')]:
        old=struct.unpack_from('<'+fmt,raw,pos)[0]
        if old:
            assert old>=end,(pos,old,end)
            struct.pack_into('<'+fmt,out,pos,old+delta)
    moved=[(rid,pad,off+delta,name+delta if name else 0)
           for rid,pad,off,name in records]
    empty=len(out);out.extend(b'\0\0');out.extend(bytes(-len(out)%8))
    for rid,body in sorted(added.items()):
        assert -(2**31)<=rid<2**31 and len(body)==size
        moved.append((rid,0,len(out),empty));out.extend(body)
    struct.pack_into('<H',out,10,len(moved))
    for i,record in enumerate(sorted(moved,key=lambda r:r[0])):
        struct.pack_into('<iIQQ',out,64+24*i,*record)
    return bytes(out)

def bnd_entries(raw):
    assert raw[:4]==b'BND4'
    result={}
    for i in range(struct.unpack_from('<I',raw,12)[0]):
        h=64+36*i
        flag,unk,size,usize,off,rid,noff=struct.unpack_from('<IIQQIII',raw,h)
        end=noff
        while raw[end:end+2]!=b'\0\0':end+=2
        name=raw[noff:end].decode('utf-16le').split('\\')[-1]
        result[name]=(h,raw[off:off+size])
    return result

def bnd_patch(raw,updates):
    out=bytearray(raw)
    parts=bnd_entries(raw)
    assert set(updates)<=set(parts)
    for name,body in updates.items():
        out.extend(bytes(-len(out)%16));pos=len(out);out.extend(body)
        h=parts[name][0];struct.pack_into('<QQI',out,h+8,len(body),len(body),pos)
    check=bnd_entries(out)
    for n,(_,body) in parts.items():assert check[n][1]==updates.get(n,body)
    return bytes(out)

def bnd_repack(raw,updates):
    """Keep original BND4 metadata and pack each live member exactly once.

    Unlike bnd_patch, this does not retain abandoned copies of replaced
    tables. Names/IDs/flags/hash tables are retained in the original prefix;
    only member sizes and data offsets change. PARAM payloads are opaque.
    """
    parts=bnd_entries(raw)
    assert parts and set(updates)<=set(parts)
    first=min(struct.unpack_from('<I',raw,h+24)[0] for h,_ in parts.values())
    assert first>=64+36*len(parts)
    # For the native ER binder, HeadersEnd is the start of aligned payloads.
    assert struct.unpack_from('<Q',raw,0x28)[0]==first
    out=bytearray(raw[:first])
    for name,(h,original) in parts.items():
        body=updates.get(name,original)
        out.extend(bytes(-len(out)%16));offset=len(out)
        assert offset<2**32
        struct.pack_into('<QQI',out,h+8,len(body),len(body),offset)
        out.extend(body)
    checked=bnd_entries(out)
    assert checked.keys()==parts.keys()
    for name,(_,body) in parts.items():
        assert checked[name][1]==updates.get(name,body),name
    return bytes(out)

def dcx_pack(raw):
    h=bytearray.fromhex('44435800000110000000001800000024000000440000004c4443530000000000000000004443500044464c540000002009000000000000000000000000000000000101004443410000000008')
    p=zlib.compress(raw,9);assert len(h)==76
    struct.pack_into('>II',h,28,len(raw),len(p));return bytes(h)+p

def dcx_unpack(blob):
    if blob[:4]!=b'DCX\0':return blob
    assert blob[40:44]==b'DFLT'
    size,cs=struct.unpack_from('>II',blob,28);raw=zlib.decompress(blob[76:76+cs]);assert len(raw)==size;return raw

class Emevd:
    def __init__(self,raw):
        assert raw[:8]==b'EVD\0\0\xff\x01\xff'
        assert struct.unpack_from('<I',raw,12)[0]==len(raw)
        h=struct.unpack_from('<16q',raw,16)
        self.prefix=raw[:12];self.events=[]
        self.linked=raw[h[11]:h[11]+8*h[10]]
        self.strings=raw[h[15]:h[15]+h[14]]
        for e in range(h[0]):
            rid,n,io,pn,po,rest,pad=struct.unpack_from('<5qII',raw,h[1]+48*e)
            assert pad==0
            ins=[]
            for i in range(n):
                bank,idx,alen,ao,lo=struct.unpack_from('<ii3q',raw,h[3]+io+32*i)
                layer=raw[h[7]+lo:h[7]+lo+32] if lo!=-1 else None
                args=raw[h[13]+ao:h[13]+ao+alen] if alen else b''
                assert len(args)==alen
                ins.append((bank,idx,args,layer))
            params=[struct.unpack_from('<3qii',raw,h[9]+po+32*i) for i in range(pn)]
            self.events.append({'id':rid,'rest':rest,'ins':ins,'params':params})
        assert sum(len(e['ins']) for e in self.events)==h[2]
        assert sum(len(e['params']) for e in self.events)==h[8]

    def write(self):
        out=bytearray(self.prefix)+bytes(4+128)
        h=[0]*16;h[0]=len(self.events);h[1]=len(out)
        out.extend(bytes(48*h[0]));h[2]=sum(len(e['ins']) for e in self.events);h[3]=len(out)
        layers=[]
        for e in self.events:
            for i in e['ins']:
                if i[3] is not None and i[3] not in layers:layers.append(i[3])
        ih={}
        for e in self.events:
            for j,i in enumerate(e['ins']):
                ih[e['id'],j]=len(out);out.extend(bytes(32))
        h[5]=len(out);h[6]=len(layers);h[7]=len(out)
        for l in layers:out.extend(l)
        h[13]=len(out)
        instoffset=0
        for k,e in enumerate(self.events):
            struct.pack_into('<5qII',out,h[1]+48*k,e['id'],len(e['ins']),instoffset if e['ins'] else -1,len(e['params']),-1,e['rest'],0)
            instoffset+=32*len(e['ins'])
            for j,(bank,idx,args,layer) in enumerate(e['ins']):
                aoff=len(out)-h[13] if args else -1
                struct.pack_into('<ii3q',out,ih[e['id'],j],bank,idx,len(args),aoff,layers.index(layer)*32 if layer else -1)
                out.extend(args);out.extend(bytes(-len(out)%4))
        out.extend(bytes(-(len(out)-h[13])%16));h[12]=len(out)-h[13]
        h[8]=sum(len(e['params']) for e in self.events);h[9]=len(out)
        for k,e in enumerate(self.events):
            po=len(out)-h[9] if e['params'] else -1
            struct.pack_into('<q',out,h[1]+48*k+32,po)
            for p in e['params']:out.extend(struct.pack('<3qii',*p))
        h[10]=len(self.linked)//8;h[11]=len(out);out.extend(self.linked)
        h[14]=len(self.strings);h[15]=len(out);out.extend(self.strings)
        struct.pack_into('<16q',out,16,*h);struct.pack_into('<I',out,12,len(out))
        assert Emevd(out).events==self.events
        return bytes(out)

def instruction_builder(emedf):
    docs=json.loads(Path(emedf).read_text())
    specs={(b['index'],i['index']):i for b in docs['main_classes'] for i in b['instrs']}
    fmts={0:'B',1:'H',2:'I',3:'b',4:'h',5:'i',6:'f',8:'I'}
    def inst(bank,idx,*args):
        spec=specs[bank,idx]['args'];assert len(spec)==len(args),(bank,idx,args)
        out=bytearray()
        for a,v in zip(spec,args):
            f=fmts[a['type']];size=struct.calcsize(f);out.extend(bytes(-len(out)%size));out.extend(struct.pack('<'+f,v))
        out.extend(bytes(-len(out)%4))
        return bank,idx,bytes(out),None
    return inst
