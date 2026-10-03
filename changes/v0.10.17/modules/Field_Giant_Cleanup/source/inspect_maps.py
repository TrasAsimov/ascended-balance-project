from pathlib import Path
import struct,zipfile,zlib,json
def q(b,o):return struct.unpack_from('<q',b,o)[0]
def i(b,o):return struct.unpack_from('<i',b,o)[0]
def text(b,o):
    e=o
    while b[e:e+2]!=b'\0\0':e+=2
    return b[o:e].decode('utf-16-le')
def sections(b):
    assert b[:4]==b'MSB '
    out={};o=16;seen=set()
    while o:
        assert o not in seen;seen.add(o)
        count=i(b,o+4);name=text(b,q(b,o+8));entries=[q(b,o+16+j*8) for j in range(count-1)]
        out[name]=entries;o=q(b,o+16+(count-1)*8)
    return out
def actors(b):
    s=sections(b);models=[text(b,o+q(b,o)) for o in s['MODEL_PARAM_ST']]
    out=[]
    for idx,o in enumerate(s['PARTS_PARAM_ST']):
        typ=i(b,o+12)
        if typ not in (2,10):continue
        td=o+q(b,o+104);ed=o+q(b,o+96)
        out.append(dict(index=idx,offset=o,name=text(b,o+q(b,o)),model=models[i(b,o+20)],type=typ,pos=struct.unpack_from('<3f',b,o+32),edition_disable=i(b,o+68),entity=i(b,ed),think=i(b,td+8),npc=i(b,td+12)))
    return out
if __name__=='__main__':
    reports=[]
    with zipfile.ZipFile('boss_hp_t2/Evernight_Reforged_Boss_HP_T2_Full_Test.zip') as z:
        for n in z.namelist():
            if not n.endswith('.msb.dcx') or '/m60_' not in n:continue
            blob=z.read(n)
            if blob[40:44]!=b'DFLT':continue
            b=zlib.decompress(blob[76:]);a=actors(b)
            targets=[x for x in a if x['model']=='c4760']
            if targets:
                print(n.split('/')[-1],json.dumps(targets,ensure_ascii=False))
                reports.append({'map':n.split('/')[-1],'actors':targets})
    Path('field_giants/source/fire_giant_inventory.json').write_text(json.dumps(reports,indent=2))
