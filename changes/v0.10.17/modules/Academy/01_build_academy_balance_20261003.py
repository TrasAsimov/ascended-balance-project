"""Apply authorized balance fields to current regulation and academy map; no ZIP creation."""
from pathlib import Path
import argparse,struct,json,hashlib,os,zlib
import zstandard
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
from cryptography.hazmat.primitives.padding import PKCS7
from pathlib import Path
import struct,zlib,json,re,xml.etree.ElementTree as ET
from collections import Counter
def param_rebuild(raw, changes, added, size):
    assert raw[0x2d] & 0x84 == 0x84
    count=struct.unpack_from('<H',raw,10)[0]
    records=[]
    for i in range(count):
        rid,pad,off,name=struct.unpack_from('<iIQQ',raw,64+24*i)
        body=changes.get(rid,raw[off:off+size]); assert len(body)==size
        namebytes=b''
        if name:
            end=name
            while raw[end:end+2]!=b'\0\0':end+=2
            namebytes=raw[name:end]
        records.append((rid,pad,body,namebytes))
    assert not set(added)&{r[0] for r in records}
    records += [(rid,0,body,b'') for rid,body in added.items()]
    records.sort(key=lambda r:r[0])
    # Canonical ordering: headers, contiguous fixed-size rows, then strings.
    # Keeping strings before appended rows breaks size inference in editors.
    out=bytearray(raw[:64])+bytearray(24*len(records))
    struct.pack_into('<H',out,4,0)
    struct.pack_into('<Q',out,0x30,len(out))
    struct.pack_into('<H',out,10,len(records))
    for i,(rid,pad,body,name) in enumerate(records):
        pos=len(out);out.extend(body)
        struct.pack_into('<iIQQ',out,64+24*i,rid,pad,pos,0)
    stringstart=len(out)
    typepos=struct.unpack_from('<Q',raw,0x10)[0]
    typ=raw[typepos:raw.index(b'\0',typepos)+1]
    out.extend(typ);out.extend(bytes(-len(out)%2))
    struct.pack_into('<I',out,0,stringstart)
    struct.pack_into('<Q',out,0x10,stringstart)
    cache={}
    for i,(_,_,_,name) in enumerate(records):
        if name not in cache:
            cache[name]=len(out);out.extend(name+b'\0\0')
        struct.pack_into('<Q',out,64+24*i+16,cache[name])
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

def dcx_pack(raw):
    h=bytearray.fromhex('44435800000110000000001800000024000000440000004c4443530000000000000000004443500044464c540000002009000000000000000000000000000000000101004443410000000008')
    p=zlib.compress(raw,9);assert len(h)==76
    struct.pack_into('>II',h,28,len(raw),len(p));return bytes(h)+p

def dcx_unpack(blob):
    if blob[:4]!=b'DCX\0':return blob
    assert blob[40:44]==b'DFLT'
    size,cs=struct.unpack_from('>II',blob,28);raw=zlib.decompress(blob[76:76+cs]);assert len(raw)==size;return raw

from pathlib import Path
import struct,zlib,json,re,xml.etree.ElementTree as ET
from collections import Counter
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

TYPES={'u8':('B',1),'s8':('b',1),'u16':('H',2),'s16':('h',2),'u32':('I',4),'s32':('i',4),'f32':('f',4)}
def decode(data,field):
    name,typ,pos,size,bits,shift,n=field
    if pos+size>len(data): return '<out of range>'
    b=data[pos:pos+size]
    if bits is not None:return (int.from_bytes(b,'little')>>shift)&((1<<bits)-1)
    if typ=='dummy8':return b.hex()
    if typ=='fixstr':return b.split(b'\0')[0].decode('shift_jis','replace')
    if typ=='fixstrW':return b.decode('utf-16le','replace').split('\0')[0]
    fmt,count=TYPES[typ]
    if n>1:return str(struct.unpack('<'+fmt*n,b))
    val=struct.unpack('<'+fmt,b)[0]
    return round(val,7) if typ=='f32' else val

NF={'hp': ('hp', 'u32', 36, 4, None, None, 1), 'darkDamageCutRate': ('darkDamageCutRate', 'f32', 448, 4, None, None, 1), 'neutralDamageCutRate': ('neutralDamageCutRate', 'f32', 420, 4, None, None, 1), 'slashDamageCutRate': ('slashDamageCutRate', 'f32', 424, 4, None, None, 1), 'blowDamageCutRate': ('blowDamageCutRate', 'f32', 428, 4, None, None, 1), 'thrustDamageCutRate': ('thrustDamageCutRate', 'f32', 432, 4, None, None, 1), 'spEffectID0': ('spEffectID0', 's32', 76, 4, None, None, 1), 'spEffectID1': ('spEffectID1', 's32', 80, 4, None, None, 1), 'spEffectID2': ('spEffectID2', 's32', 84, 4, None, None, 1), 'spEffectID3': ('spEffectID3', 's32', 88, 4, None, None, 1), 'spEffectID4': ('spEffectID4', 's32', 92, 4, None, None, 1), 'spEffectID5': ('spEffectID5', 's32', 96, 4, None, None, 1), 'spEffectID6': ('spEffectID6', 's32', 100, 4, None, None, 1), 'spEffectID7': ('spEffectID7', 's32', 104, 4, None, None, 1), 'spEffectID8': ('spEffectID8', 's32', 376, 4, None, None, 1), 'spEffectID9': ('spEffectID9', 's32', 380, 4, None, None, 1), 'spEffectID10': ('spEffectID10', 's32', 384, 4, None, None, 1), 'spEffectID11': ('spEffectID11', 's32', 388, 4, None, None, 1), 'spEffectID12': ('spEffectID12', 's32', 392, 4, None, None, 1), 'spEffectID13': ('spEffectID13', 's32', 396, 4, None, None, 1), 'spEffectID14': ('spEffectID14', 's32', 400, 4, None, None, 1), 'spEffectID15': ('spEffectID15', 's32', 404, 4, None, None, 1), 'spEffectID16': ('spEffectID16', 's32', 488, 4, None, None, 1), 'spEffectID17': ('spEffectID17', 's32', 492, 4, None, None, 1), 'spEffectID18': ('spEffectID18', 's32', 496, 4, None, None, 1), 'spEffectID19': ('spEffectID19', 's32', 500, 4, None, None, 1), 'spEffectID20': ('spEffectID20', 's32', 504, 4, None, None, 1), 'spEffectID21': ('spEffectID21', 's32', 508, 4, None, None, 1), 'spEffectID22': ('spEffectID22', 's32', 512, 4, None, None, 1), 'spEffectID23': ('spEffectID23', 's32', 516, 4, None, None, 1), 'spEffectID24': ('spEffectID24', 's32', 520, 4, None, None, 1), 'spEffectID25': ('spEffectID25', 's32', 524, 4, None, None, 1), 'spEffectID26': ('spEffectID26', 's32', 528, 4, None, None, 1), 'spEffectID27': ('spEffectID27', 's32', 532, 4, None, None, 1), 'spEffectID28': ('spEffectID28', 's32', 536, 4, None, None, 1), 'spEffectID29': ('spEffectID29', 's32', 540, 4, None, None, 1), 'spEffectID30': ('spEffectID30', 's32', 544, 4, None, None, 1), 'spEffectID31': ('spEffectID31', 's32', 548, 4, None, None, 1)}
SF={'maxHpRate': ('maxHpRate', 'f32', 16, 4, None, None, 1), 'cycleOccurrenceSpEffectId': ('cycleOccurrenceSpEffectId', 's32', 296, 4, None, None, 1)}

ROOT=Path(__file__).resolve().parent
PHYSICAL=['neutralDamageCutRate','slashDamageCutRate','blowDamageCutRate','thrustDamageCutRate']
CLONES={8353181:31810001,8352190:21900078,8353252:32520001}

def sha(b):return hashlib.sha256(b).hexdigest()
def unpack(blob,key):
 d=Cipher(algorithms.AES(key),modes.CBC(blob[:16])).decryptor();p=d.update(blob[16:])+d.finalize()
 assert p[:4]==b'DCX\0'
 size,cs=struct.unpack_from('>II',p,28)
 raw=zstandard.ZstdDecompressor().decompress(p[76:76+cs],max_output_size=size) if p[40:44]==b'ZSTD' else zlib.decompress(p[76:76+cs])
 assert len(raw)==size
 return p[:76],raw

def encrypt(header,raw,key):
 h=bytearray(header);c=zstandard.ZstdCompressor(level=15).compress(raw) if h[40:44]==b'ZSTD' else zlib.compress(raw,9)
 struct.pack_into('>II',h,28,len(raw),len(c));pad=PKCS7(128).padder();p=pad.update(bytes(h)+c)+pad.finalize()
 iv=os.urandom(16);e=Cipher(algorithms.AES(key),modes.CBC(iv)).encryptor();return iv+e.update(p)+e.finalize()

def put(data,f,value):
 _,typ,pos,size,bits,_,_=f;assert bits is None
 struct.pack_into('<'+{'f32':'f','s32':'i','u32':'I'}[typ],data,pos,value)

def map_targets(blob):
 raw=dcx_unpack(blob);pos=16;result=[]
 while pos:
  _,count,noff=struct.unpack_from('<iiq',raw,pos);end=noff
  while raw[end:end+2]!=b'\0\0':end+=2
  title=raw[noff:end].decode('utf-16le');offs=struct.unpack_from('<'+'q'*count,raw,pos+16)
  if title=='PARTS_PARAM_ST':
   for off in offs[:-1]:
    if struct.unpack_from('<i',raw,off+12)[0]!=2:continue
    nameoff=off+struct.unpack_from('<q',raw,off)[0];end=nameoff
    while raw[end:end+2]!=b'\0\0':end+=2
    name=raw[nameoff:end].decode('utf-16le');superoff=off+struct.unpack_from('<q',raw,off+0x60)[0]
    entity=struct.unpack_from('<I',raw,superoff)[0];suboff=off+struct.unpack_from('<q',raw,off+0x68)[0];nppos=suboff+12
    if entity==14000850: result.append((name,entity,nppos,8353181))
    elif entity==14000846: result.append((name,entity,nppos,8352190))
    elif name in ('c2031_9004','c2031_9002'):result.append((name,entity,nppos,8353252))
  pos=offs[-1]
 assert len(result)==4 and {x[0] for x in result}=={'c3181_9000','c4500_9000','c2031_9004','c2031_9002'}
 return raw,result

def build(regulation,map_path,output,key):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 blob=Path(regulation).read_bytes();h,raw=unpack(blob,key);parts=bnd_entries(raw)
 npcraw=parts['NpcParam.param'][1];spraw=parts['SpEffectParam.param'][1]
 nt=read_param(npcraw,'n');st=read_param(spraw,'s');np=nt['rows'];sp=st['rows']
 nf=NF;sf=SF
 assert nt['row_size']==736 and st['row_size']==912
 assert not set(CLONES)&set(np)
 nc={};na={};sa={};audit=[]
 ids_death=sorted(r for r in np if str(r).startswith('507'))
 ids_chief=sorted(r for r in np if str(r).startswith('5081'))
 ids_lamp=sorted(r for r in np if str(r).startswith('5061'))
 assert len(ids_death)==6 and len(ids_chief)==12 and len(ids_lamp)==7,(len(ids_death),len(ids_chief),len(ids_lamp))
 # Preserve shared scaling rows: clone only HP-changing nodes and their cycle ancestors.
 def neutral_hp(body):
  roots=[decode(body,nf['spEffectID'+str(i)]) for i in range(32)];reachable=set();todo=list(roots)
  while todo:
   rid=todo.pop()
   if rid<=0 or rid in reachable or rid not in sp:continue
   reachable.add(rid);nxt=decode(sp[rid]['data'],sf['cycleOccurrenceSpEffectId'])
   if nxt>0:todo.append(nxt)
  marked={r for r in reachable if decode(sp[r]['data'],sf['maxHpRate'])!=1}
  while True:
   parents={r for r in reachable if decode(sp[r]['data'],sf['cycleOccurrenceSpEffectId']) in marked}
   if parents<=marked:break
   marked|=parents
  mapping={r:8355000+r for r in marked}
  # Large private IDs remain signed32-safe; reject existing directory collisions.
  assert all(v not in sp for v in mapping.values())
  for r,new in mapping.items():
   d=bytearray(sp[r]['data']);put(d,sf['maxHpRate'],1.0)
   nxt=decode(d,sf['cycleOccurrenceSpEffectId'])
   if nxt in mapping:put(d,sf['cycleOccurrenceSpEffectId'],mapping[nxt])
   if new in sa:assert sa[new]==bytes(d)
   sa[new]=bytes(d)
  for i,r in enumerate(roots):
   if r in mapping:put(body,nf['spEffectID'+str(i)],mapping[r])
  return sorted(mapping.items())
 for rid in ids_death+ids_chief:
  d=bytearray(np[rid]['data']);target=150000 if rid in ids_death else 136000
  mappings=neutral_hp(d);put(d,nf['hp'],target)
  if rid in ids_death:put(d,nf['darkDamageCutRate'],1.4)
  nc[rid]=bytes(d);audit.append({'npc':rid,'target_ng0_hp':target,'private_hp_effects':mappings})
 for rid in ids_lamp:
  d=bytearray(np[rid]['data']);put(d,nf['darkDamageCutRate'],1.2);nc[rid]=bytes(d)
 for new,old in CLONES.items():
  d=bytearray(np[old]['data'])
  for k in PHYSICAL:put(d,nf[k],0.9)
  if new==8352190:neutral_hp(d);put(d,nf['hp'],180000)
  na[new]=bytes(d)
 nnew=param_rebuild(npcraw,nc,na,nt['row_size']);snew=param_rebuild(spraw,{},sa,st['row_size'])
 changed=bnd_patch(raw,{'NpcParam.param':nnew,'SpEffectParam.param':snew})
 reread=bnd_entries(changed);nverify=read_param(reread['NpcParam.param'][1],'n')['rows'];sverify=read_param(reread['SpEffectParam.param'][1],'s')['rows']
 for rid,r in np.items():assert nverify[rid]['data']==nc.get(rid,r['data'])
 for rid,r in sp.items():assert sverify[rid]['data']==r['data']
 for n,(_,data) in parts.items():
  if n not in ['NpcParam.param','SpEffectParam.param']:assert reread[n][1]==data
 # Exact NG0 HP even when the original resident chain had multiple multipliers.
 for rid in ids_death+ids_chief+[8352190]:
  d=nverify[rid]['data'];todo=[decode(d,nf['spEffectID'+str(i)]) for i in range(32)];seen=set();factor=1
  while todo:
   r=todo.pop()
   if r<=0 or r in seen or r not in sverify:continue
   seen.add(r);sd=sverify[r]['data'];factor*=decode(sd,sf['maxHpRate']);todo.append(decode(sd,sf['cycleOccurrenceSpEffectId']))
  assert factor==1 and decode(d,nf['hp'])== (180000 if rid==8352190 else 150000 if rid in ids_death else 136000)
 assert nverify[21900078]['data']==np[21900078]['data']
 assert nverify[32520001]['data']==np[32520001]['data']
 mapblob=Path(map_path).read_bytes();mraw,targets=map_targets(mapblob);mout=bytearray(mraw);allow=set();ma=[]
 for name,entity,pos,new in targets:
  old=struct.unpack_from('<i',mraw,pos)[0];assert old==CLONES[new]
  struct.pack_into('<i',mout,pos,new);allow.update(range(pos,pos+4));ma.append({'name':name,'entity':entity,'before':old,'after':new})
 assert all(i in allow for i,(a,b) in enumerate(zip(mraw,mout)) if a!=b)
 mapout=dcx_pack(mout);assert dcx_unpack(mapout)==mout
 result=encrypt(h,changed,key);assert unpack(result,key)[1]==changed
 (output/'regulation.bin').write_bytes(result);(output/'m14_00_00_00.msb.dcx').write_bytes(mapout)
 report={'baseline_regulation_sha256':sha(blob),'regulation_sha256':sha(result),'baseline_map_sha256':sha(mapblob),'map_sha256':sha(mapout),'death_knight_rows':ids_death,'chief_bloodfiend_rows':ids_chief,'large_lamprey_rows':ids_lamp,'hp_changes':audit,'private_npc_clones':CLONES,'private_sp_effect_count':len(sa),'map_changes':ma,'all_existing_sp_effect_rows_preserved':True,'all_non_target_npc_rows_preserved':True,'final_radagon_preserved':True,'other_loretta_preserved':True,'other_tables_preserved':True,'map_only_four_npc_references_changed':True,'encrypted_readback':'passed','exact_ng0_resident_hp_check':'passed','game_test':'NOT RUN','ng_and_coop':'retain original external scaling'}
 (output/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');return report
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--regulation',required=True);a.add_argument('--map',required=True);a.add_argument('--output',required=True);args=a.parse_args()
 build(args.regulation,args.map,args.output,bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX']))
