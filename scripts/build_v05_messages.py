"""Reconcile Ascended English talisman captions with the v0.5 PARAM values.

Inputs are FMGs extracted from the owner's Ascended and 1.17.1 message files.
The original archives are not tracked in Git. We preserve Ascended's existing
strings and only add newly missing official DLC entries.
"""
from __future__ import annotations

import csv
from pathlib import Path
import struct
import zlib

ROOT=Path(__file__).resolve().parent.parent
EXTRACTED=ROOT.parent/'work/extracted_msg'
VANILLA=ROOT.parent/'work/vanilla_msg/msg/engus'
OUT=ROOT/'output/v05_text'

REPLACE={
    1000: ('absorb slash+ 8%', 'slash damage negation +9%'),
    1010: ('absorb magic+ 8%', 'magic damage negation +9%'),
    1020: ('stamina recovery speed +15%', 'improves stamina recovery'),
    1021: ('stamina recovery speed +25%', 'improves stamina recovery'),
    1022: ('stamina recovery speed +35%', 'improves stamina recovery'),
    1030: ('equip load -20%', 'equipment weight -20%'),
    1031: ('equip load -40%', 'equipment weight -40%'),
    1032: ('equip load -60%', 'equipment weight -60%'),
    1040: ('equip load -10%', 'maximum equip load +10%'),
    1041: ('equip load -20%', 'maximum equip load +20%'),
    1042: ('equip load -30%', 'maximum equip load +30%'),
    1100: ('raises item discovery by 70%', 'improves item discovery'),
    1150: ('stamina recovery speed +15%', 'improves stamina recovery'),
    2110: ('lower equipment load by 30%', 'lower equipment load by 15%'),
    2120: ('ending a chain of attacks by 285%', 'ending a chain of attacks by 50%'),
    2130: ('charge attacks by 320%', 'charge attacks by 50%'),
    2150: ('arrows and bolts by 300%', 'arrows and bolts by 50%'),
    2200: ('+220% guard counter damage', '+50% guard counter damage'),
    2210: ('thrown jars by 120%', 'thrown jars by 70%'),
    3090: ('by 65%', 'by 30%'),
    4100: ('boosts guarding stability by 10% and shield damage reduction while blocking by 20%',
           'reduces stamina consumed while guarding by 10%'),
    6100: ('grants 80 fp regeneration', 'restores 40 FP every 2 seconds'),
}
DLC_REPLACE={
    2220: ('thrown purfumes by 30%', 'arts employing perfume by 120%'),
    7030: ('stamina recovery speed', 'stamina recovery'),
    8130: ('after rolling or backstepping by 20%', 'after rolling or backstepping by 12%'),
}


def parse_fmg(raw):
    assert raw[:4]==b'\0\0\x02\0' and len(raw)==struct.unpack_from('<i',raw,4)[0]
    groups,total=struct.unpack_from('<ii',raw,12)
    assert struct.unpack_from('<I',raw,20)[0]==255
    pointers=struct.unpack_from('<q',raw,24)[0]
    result={}
    for i in range(groups):
        index,first,last,pad=struct.unpack_from('<iiiI',raw,40+i*16)
        assert pad==0
        for key in range(first,last+1):
            offset=struct.unpack_from('<q',raw,pointers+8*(index+key-first))[0]
            if not offset:result[key]=None
            else:
                end=offset
                while raw[end:end+2]!=b'\0\0':end+=2
                result[key]=raw[offset:end].decode('utf-16le')
    assert len(result)==total
    return result


def write_fmg(entries):
    ids=sorted(entries)
    groups=[];start=last=None;start_index=0
    for i,key in enumerate(ids):
        if start is None:start=last=key;start_index=i
        elif key==last+1:last=key
        else:groups.append((start_index,start,last));start=last=key;start_index=i
    if start is not None:groups.append((start_index,start,last))
    raw=bytearray(40+16*len(groups)+8*len(ids))
    raw[:4]=b'\0\0\x02\0'
    raw[8]=1
    struct.pack_into('<iiIqq',raw,12,len(groups),len(ids),255,40+16*len(groups),0)
    for i,(index,first,last) in enumerate(groups):
        struct.pack_into('<iiiI',raw,40+i*16,index,first,last,0)
    ptrs=40+16*len(groups)
    for i,key in enumerate(ids):
        value=entries[key]
        if value is not None:
            struct.pack_into('<q',raw,ptrs+i*8,len(raw))
            raw.extend(value.encode('utf-16le')+b'\0\0')
    struct.pack_into('<i',raw,4,len(raw))
    assert parse_fmg(bytes(raw))==entries
    return bytes(raw)


def bnd_replace(raw,updates):
    result=bytearray(raw)
    count=struct.unpack_from('<I',raw,12)[0]
    matched=set()
    for i in range(count):
        h=0x40+36*i
        _,_,size,_,off,_,nameoff=struct.unpack_from('<IIQQIII',raw,h)
        end=nameoff
        while raw[end:end+2]!=b'\0\0':end+=2
        name=raw[nameoff:end].decode('utf-16le').split('\\')[-1]
        if name not in updates:continue
        matched.add(name)
        payload=updates[name]
        if len(payload)==size and payload==raw[off:off+size]:continue
        while len(result)%16:result.append(0)
        newoff=len(result)
        result.extend(payload)
        struct.pack_into('<QQI',result,h+8,len(payload),len(payload),newoff)
    assert matched==set(updates),(matched,set(updates))
    return bytes(result)


def dflt_pack(template,raw):
    out=bytearray(template[:0x4c])
    out[0x28:0x2c]=b'DFLT'
    out[0x30]=9
    compressed=zlib.compress(raw,9)
    struct.pack_into('>II',out,0x1c,len(raw),len(compressed))
    out+=compressed
    assert zlib.decompress(out[0x4c:])==raw
    return bytes(out)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    ledger=[]
    # Use the verified 1.16 binder from the user's original archive as the
    # BND header template, and write a DFLT DCX the game already used there.
    import sys,zipfile
    sys.path.insert(0,str(ROOT.parent/'work'))
    from decode_msg import unpack
    z=zipfile.ZipFile(ROOT/'inputs/Ascended_优化版_v0.2_完整包.zip')
    for variant in ('item_dlc01','item_dlc02'):
        relative='Elden_Ascended_Mod_Age of the Endless Mod/ModEngine/mod/msg/engus/'+variant+'.msgbnd.dcx'
        source=z.read(relative)
        raw=unpack(source)
        updates={}
        moddir=EXTRACTED/'ascended'/variant
        officialdir=EXTRACTED/'vanilla'/variant
        for filename in ('AccessoryCaption.fmg','AccessoryCaption_dlc01.fmg'):
            base=parse_fmg((moddir/filename).read_bytes())
            if variant=='item_dlc01':
                # Make the two DLC overlays agree on Ascended's detailed
                # base-game talisman descriptions before editing percentages.
                base=parse_fmg((EXTRACTED/'ascended/item_dlc02'/filename).read_bytes())
            official=parse_fmg((officialdir/filename).read_bytes())
            for rid,value in official.items():
                if rid not in base or base[rid] is None and value is not None:
                    base[rid]=value
                    ledger.append((variant,filename,rid,'',value,'补足新版文本'))
            replacements=REPLACE if filename=='AccessoryCaption.fmg' else DLC_REPLACE
            for rid,(before,after) in replacements.items():
                if rid not in base or base[rid] is None:continue
                if before not in base[rid]:
                    raise ValueError((variant,filename,rid,before,base[rid]))
                previous=base[rid]
                base[rid]=previous.replace(before,after,1)
                ledger.append((variant,filename,rid,previous,base[rid],'对应现行效果'))
            updates[filename]=write_fmg(base)
        # Missing newer DLC gear text may occur in name, summary and captions,
        # not only the two accessory FMGs above. Merge all missing official IDs.
        for p in sorted(officialdir.glob('*.fmg')):
            if p.name in updates or not (moddir/p.name).exists():continue
            old=parse_fmg((moddir/p.name).read_bytes())
            new=parse_fmg(p.read_bytes())
            missing={rid:val for rid,val in new.items() if val is not None and old.get(rid) is None}
            if missing:
                old.update(missing)
                updates[p.name]=write_fmg(old)
                for rid,value in missing.items():
                    ledger.append((variant,p.name,rid,'',value,'补足新版文本'))
        built=bnd_replace(raw,updates)
        candidate=dflt_pack(source,built)
        assert unpack(candidate)==built
        (OUT/(variant+'.msgbnd.dcx')).write_bytes(candidate)
        print(variant,len(source),'->',len(candidate),'updated FMGs',len(updates))
    # The newer official menu has the added class strings 288110/288111 and
    # help strings 297140/297141. Include these archives in the mod overlay.
    for name in ('menu.msgbnd.dcx','menu_dlc01.msgbnd.dcx','menu_dlc02.msgbnd.dcx'):
        (OUT/name).write_bytes((VANILLA/name).read_bytes())
    with (ROOT/'changes/v0.5_message_edits.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f);writer.writerow(('文本包','FMG','ID','原文','新文','原因'));writer.writerows(ledger)
    print('message edits',len(ledger))


if __name__=='__main__':
    main()
