"""Patch only audited regeneration captions; preserve armor Effect layout.

Accepts owned English or zhocn archives. The Chinese JSON is merge data,
not an installable zhocn archive. Equipment IDs are discovered from the
latest regulation rather than guessed from old captions.
"""
import argparse,json,os,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from disable_player_debuffs import unpack,sha
from normalize_fp_regen import TARGETS
from analyze_regulation import read_param
from field_diff import fields,decode
from formats import bnd_entries,bnd_patch,dcx_unpack,dcx_pack
from fmg import fmg_read,fmg_write

def targets(raw,defs):
    parts=bnd_entries(raw);result={}
    for table,definition,prefix in [('EquipParamProtector','EquipParamProtector','Protector'),('EquipParamWeapon','EquipParamWeapon','Weapon'),('EquipParamAccessory','EquipParamAccessory','Accessory')]:
        param=read_param(parts[table+'.param'][1],table);layout={f[0]:f for f in fields(defs/(definition+'.xml'))[0]}
        keys=[k for k in layout if ('speffect' in k.lower() and 'msg' not in k.lower()) or k=='refId']
        result[prefix]={}
        for rid,rec in param['rows'].items():
            ids={decode(rec['data'],layout[k]) for k in keys}
            rates={TARGETS[e] for e in ids if e in TARGETS}
            if rates:assert len(rates)==1;result[prefix][rid]=rates.pop()
    result['Goods']={1290:5,2951:5,11025:5} # 11025 already shares equipment effect 6202041.
    return result

EN_RE=re.compile(r'(?:restores?\s+\d+\s+fp\s+(?:every\s+\d+\s*s(?:econds)?|per\s+second)|(?:(?:grants|increases)\s+)?\d+\s+fp\s+regen(?:eration)?|increases\s+fp\s+regen\s+by\s+\d+)',re.I)
ZH_RE=re.compile(r'每\s*\d+(?:\.\d+)?\s*秒(?:恢复|回复)\s*\d+\s*(?:FP|法力)',re.I)

def revise(value,prefix,rid,rate,lang):
    text=value or ''
    clause=f'Restores {rate} FP every second' if lang=='en' else f'每秒恢复{rate} FP'
    rx=EN_RE if lang=='en' else ZH_RE
    new,n=rx.subn(clause,text)
    label='Effect: ' if lang=='en' else '效果：'
    if prefix=='Goods' and rid==2951:
        # Keep the existing body-buff description and append its FP value once.
        marker=clause+('.' if lang=='en' else '。')
        if marker not in new:
            lines=new.splitlines();at=next((i for i,s in enumerate(lines) if s.strip().startswith(('Effect:','效果'))),None)
            if at is None:new=new.rstrip()+'\n\n'+label+marker
            else:lines[at]=lines[at].rstrip()+('；' if lang=='zh' else '; ')+marker;new='\n'.join(lines)
    elif n==0 and clause not in new:
        new=new.rstrip()+'\n\n'+label+clause+('.' if lang=='en' else '。')
    if prefix=='Goods' and rid==1290:
        duration='FP regeneration lasts 30 minutes.' if lang=='en' else '法力恢复持续30分钟。'
        if duration not in new:new=new.rstrip()+'\n\n'+duration
    return new

def patch(blob,selected,lang):
    raw=dcx_unpack(blob);parts=bnd_entries(raw);updates={};ledger=[];caption_seen={p:set() for p in selected}
    for n,v in parts.items():
        m=re.fullmatch(r'(Goods|Weapon|Protector|Accessory)(Caption|Info)(?:_dlc0[12])?\.fmg',n)
        if not m:continue
        prefix,kind=m.groups();d=fmg_read(v[1]);original=dict(d)
        for rid,rate in selected[prefix].items():
            if rid not in d or not d[rid]:continue
            if kind=='Caption':
                caption_seen[prefix].add(rid);d[rid]=revise(d[rid],prefix,rid,rate,lang)
            elif prefix=='Accessory' or (prefix=='Goods' and rid in [1290,11025]):
                d[rid]=f'Restores {rate} FP every second' if lang=='en' else f'每秒恢复{rate} FP'
            if d[rid]!=original[rid]:ledger.append({'fmg':n,'id':rid,'rate':rate,'before':original[rid],'after':d[rid]})
        if d!=original:updates[n]=fmg_write(d)
    for prefix,ids in caption_seen.items():assert ids,('missing caption table',prefix)
    if not updates:return blob,ledger
    result=dcx_pack(bnd_patch(raw,updates));after=bnd_entries(dcx_unpack(result));changed={(x['fmg'],x['id']) for x in ledger}
    for n,v in parts.items():
        if n not in updates:assert after[n][1]==v[1]
        else:
            old=fmg_read(v[1]);new=fmg_read(after[n][1]);assert old.keys()==new.keys()
            assert all(new[k]==val for k,val in old.items() if (n,k) not in changed)
    return result,ledger

def patch_metadata(data,selected,prefix,lang):
    result=dict(data);changed=[]
    for k,value in data.items():
        if k.isdigit() and int(k) in selected[prefix] and isinstance(value,str) and value:
            result[k]=revise(value,prefix,int(k),selected[prefix][int(k)],lang)
            if result[k]!=value:changed.append(k)
    assert result.keys()==data.keys()
    assert all(result[k]==v for k,v in data.items() if k not in changed)
    return result,changed

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--regulation',type=Path,required=True)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--paramdefs',type=Path,required=True);p.add_argument('--language',choices=['en','zh'],default='en')
    p.add_argument('--metadata-input',type=Path,help='Optional latest Armor_Core JSON directory')
    a=p.parse_args();_,raw=unpack(a.regulation.read_bytes(),bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX']))
    selected=targets(raw,a.paramdefs);a.output.mkdir(parents=True,exist_ok=True);reports=[]
    for suffix in ['01','02']:
        source=a.input/('item_dlc'+suffix+'.msgbnd.dcx');blob=source.read_bytes();out,ledger=patch(blob,selected,a.language)
        assert patch(out,selected,a.language)[0]==out
        name='01_FP_Regen_20261002_'+('engus' if a.language=='en' else 'zhocn')+'_item_dlc'+suffix+'.msgbnd.dcx'
        (a.output/name).write_bytes(out)
        reports.append({'source':str(source),'input_sha256':sha(blob),'output':name,'output_sha256':sha(out),'changes':ledger,'idempotence':True})
    metadata=[]
    if a.metadata_input:
        for name,lang in [('description_en.json','en'),('description_zh.json','zh')]:
            data=json.loads((a.metadata_input/name).read_text());new,changed=patch_metadata(data,selected,'Protector',lang)
            assert patch_metadata(new,selected,'Protector',lang)[0]==new
            target='01_FP_Regen_20261002_armor_'+name
            (a.output/target).write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
            metadata.append({'output':target,'changed_ids':changed,'other_entries_unchanged':True})
        name='shield_description_en.json';data=json.loads((a.metadata_input/name).read_text());new={};changed={}
        for k,v in data.items():
            new[k],changed[k]=patch_metadata(v,selected,'Weapon','en')
            assert patch_metadata(new[k],selected,'Weapon','en')[0]==new[k]
        target='01_FP_Regen_20261002_'+name
        (a.output/target).write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
        metadata.append({'output':target,'changed_ids':changed,'other_entries_unchanged':True})
    (a.output/'01_FP_Regen_20261002_text_audit.json').write_text(json.dumps({'targets':selected,'archives':reports,'metadata':metadata,'other_entries_unchanged':True},ensure_ascii=False,indent=2)+'\n')
    (a.output/'01_FP_Regen_20261002_description_zh.json').write_text(json.dumps({'status':'merge data, not a zhocn game archive','equipment_fp_per_second':selected,'special':{'1290':'每秒恢复5 FP，持续30分钟。','2951':'保留现有体增益；其中法力恢复为每秒5 FP。'},'same_id_stacking':'未修改，待实测'},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'target_configurations':{k:len(v) for k,v in selected.items()},'caption_changes':[len(x['changes']) for x in reports],'idempotence':True}))
if __name__=='__main__':main()
