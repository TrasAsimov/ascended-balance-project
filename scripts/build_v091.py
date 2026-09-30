"""Raise Arrow's Sting damage coefficient from 1.5 to 2.0 on v0.9."""
from __future__ import annotations
import csv, hashlib, json, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parent/'work'))
from field_diff import defs,fields,decode
from analyze_regulation import read_bnd
from build_v04 import decrypt_official
from build_v05 import active_rows,encrypt_native
from build_v09 import DAMAGE

def main():
 source=ROOT/'work/v09.bnd';data=bytearray(source.read_bytes())
 _,mod=read_bnd(source)
 aid=2150;eid=struct.unpack_from('<i',mod['EquipParamAccessory']['rows'][aid]['data'],4)[0]
 assert eid==321500
 f={x[0]:x for x in fields(defs()[mod['SpEffectParam']['ptype']])[0]}
 offset=active_rows(data,'SpEffectParam')[eid]
 changes=[]
 for field in DAMAGE:
  old=decode(mod['SpEffectParam']['rows'][eid]['data'],f[field]);assert old==1.5,(field,old)
  assert f[field][1]=='f32' and f[field][4] is None
  struct.pack_into('<f',data,offset+f[field][2],2.0)
  changes.append((aid,'硬箭护符',eid,field,old,2.0,'箭矢与弩箭伤害增加 100%；弓本体属性另计'))
 target=ROOT/'work/v091.bnd';target.write_bytes(data)
 version,check=read_bnd(target);assert version=='11711000' and len(check)==194
 for table in mod:
  for rid,record in mod[table]['rows'].items():
   if table=='SpEffectParam' and rid==eid:
    expected=bytearray(record['data'])
    for key in DAMAGE:struct.pack_into('<f',expected,f[key][2],2.0)
    assert check[table]['rows'][rid]['data']==bytes(expected)
    continue
   assert check[table]['rows'][rid]['data']==record['data'],(table,rid)
 assert all(decode(check['SpEffectParam']['rows'][eid]['data'],f[key])==2.0 for key in DAMAGE)
 template,_=decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
 binary=encrypt_native(template,bytes(data));assert decrypt_official(binary)[1]==bytes(data)
 (ROOT/'output/v091_regulation.bin').write_bytes(binary)
 with (ROOT/'changes/v0.9.1_arrow_talisman.csv').open('w',encoding='utf-8-sig',newline='') as out:
  w=csv.writer(out);w.writerow(('护符ID','中文名','效果ID','字段','v0.9','v0.9.1','含义'));w.writerows(changes)
 summary={'version':'v0.9.1-test','talisman_id':aid,'effect_id':eid,'field_edits':len(changes),
          'arrow_talisman_damage_coefficient':2.0,'regulation_sha256':hashlib.sha256(binary).hexdigest()}
 (ROOT/'output/v091_manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
