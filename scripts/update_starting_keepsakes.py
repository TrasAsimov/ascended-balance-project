"""Remove starter grace items and align selectable keepsakes with build talismans.

Apply after v0.10.11. Menu source BNDs are extracted from the matching runtime.
"""
import argparse,json,struct,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from build_v03 import KEY
from disable_player_debuffs import unpack
from build_minor_boss_heart import pack_regulation
from analyze_regulation import read_param
from field_diff import fields,decode,TYPES
from formats import bnd_entries,bnd_repack,param_patch,dcx_pack,dcx_unpack,bnd_patch
from fmg import fmg_read,fmg_write
from package_v0109 import compact_text
from set_alexander_and_player_hp import sha
CHOICES={1:(1230,'Warrior Jar Shard','战技'),2:(2080,'Winged Sword Insignia','连击'),3:(2000,'Magic Scorpion Charm','魔法'),4:(2130,'Axe Talisman','蓄力攻击'),5:(2180,'Claw Talisman','跳跃攻击'),6:(2200,'Curved Sword Talisman','防御反击'),7:(2090,'Dagger Talisman','处决'),8:(3001,'Graven-Mass Talisman','魔法施法'),9:(3050,"Flock\'s Canvas Talisman",'祷告'),10:(4100,'Greatshield Talisman','盾防')}

def patch(raw,defs):
 parts=bnd_entries(raw);tables={t:read_param(parts[t+'.param'][1],t) for t in ['CharaInitParam','BaseChrSelectMenuParam','CharMakeMenuListItemParam','EquipParamAccessory']}
 maps={};sizes={}
 for t in tables:
  fs,size=fields(defs/(t+'.xml'));assert size==tables[t]['row_size'];maps[t]={f[0]:f for f in fs};sizes[t]=size
 def get(t,rid,k):return decode(tables[t]['rows'][rid]['data'],maps[t][k])
 def put(body,t,k,v):
  f=maps[t][k];assert f[4] is None and f[6]==1;struct.pack_into('<'+TYPES[f[1]][0],body,f[2],v)
 origins={get('BaseChrSelectMenuParam',rid,'originChrInitParam') for rid in range(2000,2012)}
 previews={get('BaseChrSelectMenuParam',rid,'chrInitParam')+sex for rid in range(2000,2012) for sex in (0,1)}
 assert origins==set(range(3000,3012)) and previews==set(range(3100,3124))
 changes={};removed=[]
 for rid in sorted(origins|previews|set(range(20,24))):
  body=bytearray(tables['CharaInitParam']['rows'][rid]['data'])
  for prefix,count in [('item',10),('secondaryItem',6)]:
   for i in range(1,count+1):
    k=f'{prefix}_{i:02}';nk=f'{prefix}Num_{i:02}'
    if get('CharaInitParam',rid,k) in (115,2050):
     removed.append({'row':rid,'slot':k,'goods_id':get('CharaInitParam',rid,k)})
     put(body,'CharaInitParam',k,-1);put(body,'CharaInitParam',nk,0)
  changes[rid]=bytes(body)
 for choice in range(11):
  rid=2400+choice;source=tables['CharaInitParam']['rows'].get(rid,tables['CharaInitParam']['rows'][2400])['data'];body=bytearray(source)
  for i in range(1,5):put(body,'CharaInitParam',f'equip_Accessory{i:02}',-1)
  for prefix,count in [('item',10),('secondaryItem',6)]:
   for i in range(1,count+1):put(body,'CharaInitParam',f'{prefix}_{i:02}',-1);put(body,'CharaInitParam',f'{prefix}Num_{i:02}',0)
  if choice:
   aid=CHOICES[choice][0];assert aid in tables['EquipParamAccessory']['rows'];put(body,'CharaInitParam','equip_Accessory01',aid)
  changes[rid]=bytes(body)
 rows=tables['CharaInitParam']['rows'];existing={rid:b for rid,b in changes.items() if rid in rows};added={rid:b for rid,b in changes.items() if rid not in rows}
 updates={'CharaInitParam.param':param_patch(parts['CharaInitParam.param'][1],existing,added,sizes['CharaInitParam'])}
 # Add a tenth talisman in the same keepsake group; keep the original nine choice values.
 menu=tables['CharMakeMenuListItemParam']['rows'];template=bytearray(menu[100309]['data']);put(template,'CharMakeMenuListItemParam','value',10);put(template,'CharMakeMenuListItemParam','captionId',297161)
 if 100310 in menu:assert menu[100310]['data']==template
 else:updates['CharMakeMenuListItemParam.param']=param_patch(parts['CharMakeMenuListItemParam.param'][1],{}, {100310:bytes(template)},sizes['CharMakeMenuListItemParam'])
 result=bnd_repack(raw,updates);after=bnd_entries(result)
 for n,(_,b) in parts.items():
  if n not in updates:assert after[n][1]==b
 for t in ['CharaInitParam','CharMakeMenuListItemParam']:
  checked=read_param(after[t+'.param'][1],t)['rows'];before=tables[t]['rows']
  for rid,r in before.items():assert checked[rid]['data']==(changes.get(rid,r['data']) if t=='CharaInitParam' else r['data']) and checked[rid]['name']==r['name']
 checked=read_param(after['CharaInitParam.param'][1],'CharaInitParam')['rows']
 for rid in origins|previews|set(range(20,24)):
  assert all(decode(checked[rid]['data'],maps['CharaInitParam'][f'{p}_{i:02}']) not in (115,2050) for p,c in [('item',10),('secondaryItem',6)] for i in range(1,c+1))
 for value,(aid,_,_) in CHOICES.items():assert decode(checked[2400+value]['data'],maps['CharaInitParam']['equip_Accessory01'])==aid
 return result,{'origin_rows':sorted(origins),'preview_rows':sorted(previews),'common_player_rows':[20,21,22,23],'removed_grace_slots':removed,'none_choice':'empty','choices':CHOICES,'changed_tables':sorted(updates),'game_tested':False}


CAPTIONS={1:297151,2:297152,3:297153,4:297154,5:297156,6:297157,7:297158,8:297159,9:297160,10:297161}
HELP={1:'Skill damage +40%.',2:'Strength +25. Successive attacks raise attack power\nby 5% per tier, up to 20%.',3:'Magic damage +20% against enemies.\nPhysical damage taken +15%.',4:'Charged heavy attack damage +300%.',5:'Jump attack damage +100%.',6:'Guard counter damage +300%.',7:'Critical damage +400%.',8:'Sorcery damage +30%.',9:'Incantation damage +30%.',10:'Reduces stamina consumed when guarding by 80%.'}

def patch_menu(raw):
 parts=bnd_entries(raw);updates={};records=[]
 for name in ['GR_MenuText.fmg','GR_LineHelp.fmg']:
  before=fmg_read(parts[name][1]);entries=dict(before)
  for choice,caption in CAPTIONS.items():
   target=CHOICES[choice][1] if name=='GR_MenuText.fmg' else HELP[choice]
   assert caption in entries
   entries[caption]=target
  if name=='GR_LineHelp.fmg':entries[297150]='No keepsake. Receive no additional talisman.'
  allowed=set(CAPTIONS.values())|({297150} if name=='GR_LineHelp.fmg' else set())
  assert entries.keys()==before.keys() and all(entries[k]==v for k,v in before.items() if k not in allowed)
  if entries!=before:updates[name]=fmg_write(entries)
  records.append({'fmg':name,'changed_ids':[k for k,v in entries.items() if v!=before[k]]})
 if not updates:return raw,records
 result=compact_text(bnd_patch(raw,updates));checked=bnd_entries(result)
 assert all(checked[n][1]==b for n,(_,b) in parts.items() if n not in updates)
 return result,records

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for f in ['base_zip','defs','menu_source','output']:p.add_argument('--'+f.replace('_','-'),type=Path,required=True)
 a=p.parse_args();a.output.mkdir(exist_ok=True,parents=True)
 with zipfile.ZipFile(a.base_zip) as z:
  get=lambda suffix:z.read(next(n for n in z.namelist() if n.endswith('/ModEngine/mod/'+suffix)))
  header,raw=unpack(get('regulation.bin'),KEY);result,audit=patch(raw,a.defs);assert patch(result,a.defs)[0]==result
  blob=pack_regulation(header,result,KEY);assert unpack(blob,KEY)[1]==result;(a.output/'regulation.bin').write_bytes(blob)
  audit['regulation_sha256']=sha(blob);audit['idempotence_and_encrypted_readback']=True
  audit['menus']=[]
  for name in ['menu','menu_dlc01','menu_dlc02']:
   rawmenu=(a.menu_source/(name+'.msgbnd.dcx.bnd')).read_bytes();newmenu,records=patch_menu(rawmenu)
   assert patch_menu(newmenu)[0]==newmenu
   packed=dcx_pack(newmenu);assert dcx_unpack(packed)==newmenu
   (a.output/(name+'.msgbnd.dcx')).write_bytes(packed)
   audit['menus'].append({'name':name,'sha256':sha(packed),'entries':records,'non_target_fmg_and_entries':'byte-identical','idempotent':True})
  (a.output/'starter_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(json.dumps(audit,ensure_ascii=False))
if __name__=='__main__':main()
