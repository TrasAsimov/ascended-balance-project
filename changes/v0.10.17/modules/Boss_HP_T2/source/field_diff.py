from __future__ import annotations
from collections import Counter, defaultdict
import csv, json, re, struct, sys, os
from pathlib import Path
import xml.etree.ElementTree as ET
from analyze_regulation import read_bnd

BASE=Path(__file__).parent
DEFROOT=Path(os.environ.get('ARMOR_PARAMDEFS',str(BASE.parent/'inputs/work/Paramdex/ER/Defs')))
NAMEROOT=BASE/'Paramdex/ER/Names'
TYPES={'u8':('B',1),'s8':('b',1),'u16':('H',2),'s16':('h',2),'u32':('I',4),'s32':('i',4),'f32':('f',4)}

def defs():
    result={}
    for p in DEFROOT.glob('*.xml'):
        root=ET.parse(p).getroot()
        key=root.findtext('ParamType')
        if key: result[key]=p
    return result

def fields(path):
    root=ET.parse(path).getroot()
    offset=0;bit_start=None;bit_used=0;bit_width=0;out=[]
    for f in root.findall('./Fields/Field'):
        d=f.attrib['Def'].split(' = ',1)[0]
        match=re.fullmatch(r'(\w+)\s+(\w+)(?:\[(\d+)\])?(?::(\d+))?',d)
        if not match: raise ValueError((path,d))
        typ,name,array,bits=match.groups()
        n=int(array or 1)
        if bits:
            width=(TYPES[typ][1] if typ in TYPES else 1)*8
            if bit_start is None or bit_width!=width or bit_used+int(bits)>width:
                bit_start=offset;offset+=width//8;bit_used=0;bit_width=width
            out.append((name,typ,bit_start,width//8,int(bits),bit_used,n))
            bit_used+=int(bits)
            if bit_used==width:bit_start=None
        else:
            bit_start=None
            width=TYPES[typ][1] if typ in TYPES else (2 if typ=='fixstrW' else 1)
            out.append((name,typ,offset,width*n,None,None,n))
            offset+=width*n
    return out,offset

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

def names(table):
    p=NAMEROOT/(table+'.txt')
    out={}
    if p.exists():
        for l in p.read_text('utf-8-sig',errors='replace').splitlines():
            a=l.split(' ',1)
            if len(a)==2 and a[0].lstrip('-').isdigit():out[int(a[0])]=a[1]
    return out

def main():
    _, mod=read_bnd(BASE/'mod.bnd');_,van=read_bnd(BASE/'vanilla.bnd')
    d=defs()
    field_out=BASE/'field_differences.csv';row_out=BASE/'row_inventory.csv'
    stats=[];missing=[];field_counts=defaultdict(Counter)
    with field_out.open('w',newline='',encoding='utf-8-sig') as ff,row_out.open('w',newline='',encoding='utf-8-sig') as rf:
        fw=csv.writer(ff);rw=csv.writer(rf)
        fw.writerow(['表','行ID','行名(Paramdex)','字段','类型','模组值','新版原版值','字节偏移','归因'])
        rw.writerow(['表','行ID','行名(Paramdex)','类别','Mod行字节数','新版原版行字节数','归因'])
        for table in sorted(mod):
            x,y=mod[table],van[table]
            p=d.get(x['ptype'])
            fd,expected=fields(p) if p else ([],None)
            valid=expected==x['row_size']==y['row_size']
            if not valid and (x['rows'] or y['rows']):missing.append((table,x['ptype'],str(p),expected,x['row_size'],y['row_size']))
            nm=names(table);changed=0;fieldchanges=0
            for rid in sorted(x['rows'].keys()|y['rows'].keys()):
                a=x['rows'].get(rid,{}).get('data');b=y['rows'].get(rid,{}).get('data')
                if a is None or b is None:
                    cls='仅Mod有' if a is not None else '仅新版原版有'
                    rw.writerow([table,rid,nm.get(rid,''),cls,len(a) if a else '',len(b) if b else '', '跨版本差异，来源未确认'])
                    continue
                if a==b:continue
                changed+=1
                rw.writerow([table,rid,nm.get(rid,''),'共有行数值不同',len(a),len(b),'跨版本差异，来源未确认'])
                if not valid:continue
                for field in fd:
                    name,typ,pos,size,bit,shift,n=field
                    if a[pos:pos+size]==b[pos:pos+size]:continue
                    av,bv=decode(a,field),decode(b,field)
                    if av==bv:continue
                    # A changed bitfield may share one byte with unchanged fields.
                    fw.writerow([table,rid,nm.get(rid,''),name,typ,av,bv,pos,'跨版本差异，来源未确认'])
                    field_counts[table][name]+=1;fieldchanges+=1
            stats.append((table,changed,fieldchanges,valid))
    (BASE/'field_counts.json').write_text(json.dumps({t:c.most_common() for t,c in field_counts.items()},ensure_ascii=False,indent=2))
    print('matched table definitions',sum(x[3] for x in stats),'out of',len(stats),'field diff rows',sum(x[2] for x in stats))
    print('unmatched',missing)
    print('top counts',[(t,fc) for t,rc,fc,ok in sorted(stats,key=lambda x:-x[2])[:20]])

if __name__=='__main__':main()
