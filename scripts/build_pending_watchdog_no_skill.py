"""Remove every Watchdog's Staff skill variant; pending major-version release."""
from __future__ import annotations
import csv,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parent/'work'))
from analyze_regulation import read_bnd
from field_diff import defs,fields,decode
from build_v04 import decrypt_official
from build_v05 import active_rows,encrypt_native

SOURCE=ROOT/'work/pending_class_loadouts.bnd'
OUT=ROOT/'work/pending_watchdog_no_skill.bnd'
REG=ROOT/'output/pending_watchdog_no_skill_regulation.bin'
CHANGES={
 'EquipParamWeapon':{23010000:{'swordArtsParamId':10,'gemMountType':0,'disableGemAttr':1}},
 'EquipParamCustomWeapon':{309:{'gemId':30900},329:{'gemId':30900}},
}

def main():
 data=bytearray(SOURCE.read_bytes());_,mod=read_bnd(SOURCE);log=[]
 assert 10 in mod['SwordArtsParam']['rows'] and 30900 in mod['EquipParamGem']['rows']
 ff={t:{x[0]:x for x in fields(defs()[mod[t]['ptype']])[0]} for t in CHANGES}
 gemfields={x[0]:x for x in fields(defs()[mod['EquipParamGem']['ptype']])[0]}
 assert decode(mod['EquipParamGem']['rows'][30900]['data'],gemfields['swordArtsParamId'])==10
 assert {rid for rid,r in mod['EquipParamCustomWeapon']['rows'].items()
         if decode(r['data'],ff['EquipParamCustomWeapon']['baseWepId'])==23010000}=={309,329}
 for table,rows in CHANGES.items():
  offs=active_rows(data,table);f=ff[table]
  for rid,changes in rows.items():
   old=mod[table]['rows'][rid]['data']
   for key,new in changes.items():
    spec=f[key];value=decode(old,spec);assert value!=new,(table,rid,key)
    if spec[4] is not None:
     assert spec[1]=='u8' and spec[4]==1
     mask=1<<spec[5];at=offs[rid]+spec[2]
     data[at]=(data[at]&~mask)|(new<<spec[5])
    else:
     fmt={'s32':'i','u8':'B'}[spec[1]]
     struct.pack_into('<'+fmt,data,offs[rid]+spec[2],new)
    log.append((table,rid,key,value,new))
 OUT.write_bytes(data);version,check=read_bnd(OUT)
 assert version=='11711000' and len(check)==194
 for table in mod:
  for rid,record in mod[table]['rows'].items():
   expected=bytearray(record['data'])
   for key,new in CHANGES.get(table,{}).get(rid,{}).items():
    spec=ff[table][key]
    if spec[4] is not None:
     mask=1<<spec[5];expected[spec[2]]=(expected[spec[2]]&~mask)|(new<<spec[5])
    else:struct.pack_into('<'+{'s32':'i','u8':'B'}[spec[1]],expected,spec[2],new)
   assert check[table]['rows'][rid]['data']==bytes(expected),(table,rid)
 with (ROOT/'changes/pending_watchdog_no_skill.csv').open('w',encoding='utf-8-sig',newline='') as fp:
  w=csv.writer(fp);w.writerow(('参数表','行ID','字段','原值','新值'));w.writerows(log)
 template,_=decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
 enc=encrypt_native(template,bytes(data));assert decrypt_official(enc)[1]==bytes(data)
 REG.write_bytes(enc)
 print('changed fields',len(log),'rows',list(CHANGES['EquipParamWeapon'])+list(CHANGES['EquipParamCustomWeapon']))
if __name__=='__main__':main()
