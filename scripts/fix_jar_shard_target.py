"""Correct v0.10.10's talisman target using v0.10.9 as the restoration baseline."""
import argparse,json,struct,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from build_v03 import KEY
from disable_player_debuffs import unpack
from build_minor_boss_heart import pack_regulation
from analyze_regulation import read_param
from field_diff import fields,decode
from formats import bnd_entries,bnd_repack,param_patch,dcx_unpack,dcx_pack,bnd_patch
from fmg import fmg_read,fmg_write
from package_v0109 import compact_text
from set_alexander_and_player_hp import RATES,sha

def remove_row(raw,rid):
 count=struct.unpack_from('<H',raw,10)[0];end=64+24*count
 records=[struct.unpack_from('<iIQQ',raw,64+24*i) for i in range(count)]
 assert sum(r[0]==rid for r in records)==1
 kept=[r for r in records if r[0]!=rid]
 out=bytearray(raw[:64]+bytes(24*len(kept))+raw[end:])
 for pos,fmt in [(0,'I'),(0x10,'Q'),(0x30,'Q')]:
  old=struct.unpack_from('<'+fmt,raw,pos)[0]
  if old:assert old>=end;struct.pack_into('<'+fmt,out,pos,old-24)
 struct.pack_into('<H',out,10,len(kept))
 for i,(r,p,o,n) in enumerate(kept):struct.pack_into('<iIQQ',out,64+24*i,r,p,o-24,n-24 if n else 0)
 return bytes(out)

def patch(raw,baseline,defs):
 parts=bnd_entries(raw);old=bnd_entries(baseline);updates={}
 for table,definition in [('EquipParamAccessory','EquipParamAccessory'),('SpEffectParam','SpEffect')]:
  name=table+'.param';data=parts[name][1];rows=read_param(data,table)['rows'];base=read_param(old[name][1],table)['rows'];layout,size=fields(defs/(definition+'.xml'));fm={f[0]:f for f in layout}
  if table=='EquipParamAccessory':
   assert decode(rows[1230]['data'],fm['refId'])==312300
   changes={1231:base[1231]['data']}
  else:
   assert rows[312310]['data']==base[312310]['data']
   body=bytearray(rows[312300]['data'])
   for f in RATES:
    value=decode(body,fm[f]);assert abs(value-1.2)<1e-6 or abs(value-1.4)<1e-6
    struct.pack_into('<f',body,fm[f][2],1.4)
   assert [decode(body,fm[f]) for f in ['magicSubCategoryChange1','magicSubCategoryChange2']]==[112,111]
   changes={312300:bytes(body)}
  changed=param_patch(data,changes,{},size)
  if table=='SpEffectParam' and 78212310 in rows:changed=remove_row(changed,78212310)
  after=read_param(changed,table)['rows'];assert set(after)==set(rows)-({78212310} if table=='SpEffectParam' else set())
  for rid,row in after.items():assert row['data']==changes.get(rid,rows[rid]['data']) and row['name']==rows[rid]['name']
  if changed!=data:updates[name]=changed
 result=bnd_repack(raw,updates) if updates else raw
 assert all(bnd_entries(result)[n][1]==b for n,(_,b) in parts.items() if n not in updates)
 return result

def text_patch(blob,baseline):
 raw=dcx_unpack(blob);parts=bnd_entries(raw);base=bnd_entries(dcx_unpack(baseline));updates={}
 for name in ['AccessoryInfo.fmg','AccessoryCaption.fmg']:
  entries=fmg_read(parts[name][1]);original=dict(entries);old=fmg_read(base[name][1]);entries[1231]=old[1231]
  small=old[1230]
  if name=='AccessoryInfo.fmg':entries[1230]='Increases skill damage by 40%.'
  else:
   assert '20%' in small,(name,small)
   entries[1230]=small.replace('20%','40%')
  assert all(entries[k]==v for k,v in original.items() if k not in (1230,1231))
  if entries!=original:updates[name]=fmg_write(entries)
 if not updates:return blob
 result=dcx_pack(compact_text(bnd_patch(raw,updates)));check=bnd_entries(dcx_unpack(result))
 assert all(check[n][1]==b for n,(_,b) in parts.items() if n not in updates)
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for f in ['current','baseline','defs','output']:p.add_argument('--'+f,type=Path,required=True)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(a.current) as z,zipfile.ZipFile(a.baseline) as old:
  def get(archive,suffix):return archive.read(next(n for n in archive.namelist() if n.endswith('/ModEngine/mod/'+suffix)))
  source=get(z,'regulation.bin');header,raw=unpack(source,KEY);base=unpack(get(old,'regulation.bin'),KEY)[1]
  result=patch(raw,base,a.defs);assert patch(result,base,a.defs)==result
  encrypted=pack_regulation(header,result,KEY);assert unpack(encrypted,KEY)[1]==result
  (a.output/'regulation.bin').write_bytes(encrypted)
  for s in ['01','02']:
   name=f'item_dlc{s}.msgbnd.dcx';blob=text_patch(get(z,'msg/engus/'+name),get(old,'msg/engus/'+name))
   assert text_patch(blob,get(old,'msg/engus/'+name))==blob
   (a.output/name).write_bytes(blob)
  report={'small_item':1230,'small_effect':312300,'skill_multiplier_before':1.2,'skill_multiplier_after':1.4,'large_item':1231,'large_effect':312310,'large_restored_exactly_to':'v0.10.9','removed_wrong_effect':78212310,'player_hp_curve':'unchanged from v0.10.10 (2.5x)','other_tables_and_rows':'byte-identical','text_ids_changed':[1230,1231],'idempotent':True,'encrypted_readback':True,'game_tested':False,'regulation_sha256':sha(encrypted)}
  (a.output/'target_fix_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
