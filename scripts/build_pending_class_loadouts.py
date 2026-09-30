"""Pending class loadout edits after v0.9.1; do not publish until user approves a major version."""
from __future__ import annotations
import csv,hashlib,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parent/'work'))
from analyze_regulation import read_bnd
from field_diff import defs,fields,decode
from build_v04 import decrypt_official
from build_v05 import active_rows,encrypt_native

SOURCE=ROOT/'work/v091.bnd'
OUT=ROOT/'work/pending_class_loadouts.bnd'
REG=ROOT/'output/pending_class_loadouts_regulation.bin'
CSV=ROOT/'changes/pending_class_loadouts.csv'
# The selection menu references both the origin rows and the two face templates.
# The origin rows determine the starting loadout; the templates also need the
# same equipment so the selection preview cannot show the former bow.
CHANGES={
 3003:{'equip_Wep_Left':30000000,'equip_Arrow':-1,
       'equip_Accessory02':2090},
 3106:{'equip_Subwep_Left':-1,'equip_Arrow':-1,
       'equip_Accessory01':2080,'equip_Accessory02':2090},
 3107:{'equip_Subwep_Left':-1,'equip_Arrow':-1,
       'equip_Accessory01':2080,'equip_Accessory02':2090},
 3000:{'equip_Accessory01':4100},
 3100:{'equip_Accessory01':4100},
 3101:{'equip_Accessory01':4100},
}

def main():
 data=bytearray(SOURCE.read_bytes());_,mod=read_bnd(SOURCE)
 param=mod['CharaInitParam'];f={x[0]:x for x in fields(defs()[param['ptype']])[0]}
 offs=active_rows(data,'CharaInitParam');log=[]
 for rid,changes in CHANGES.items():
  before=param['rows'][rid]['data']
  for key,val in changes.items():
   field=f[key];assert field[1]=='s32' and field[4] is None
   old=decode(before,field);assert old!=val,(rid,key)
   struct.pack_into('<i',data,offs[rid]+field[2],val)
   log.append((rid,key,old,val))
 # Bandit preserves consecutive attack talisman and gains Dagger Talisman.
 assert decode(param['rows'][3003]['data'],f['equip_Accessory01'])==2080
 assert decode(param['rows'][3106]['data'],f['equip_Wep_Left'])==30000000
 assert decode(param['rows'][3107]['data'],f['equip_Wep_Left'])==30000000
 # Buckler's original skill is Buckler Parry (303), and is not overwritten.
 wf={x[0]:x for x in fields(defs()[mod['EquipParamWeapon']['ptype']])[0]}
 assert decode(mod['EquipParamWeapon']['rows'][30000000]['data'],wf['swordArtsParamId'])==303
 OUT.write_bytes(data);version,check=read_bnd(OUT)
 assert version=='11711000' and len(check)==194
 for table in mod:
  for rid,record in mod[table]['rows'].items():
   expected=bytearray(record['data'])
   if table=='CharaInitParam' and rid in CHANGES:
    for key,val in CHANGES[rid].items():struct.pack_into('<i',expected,f[key][2],val)
   assert check[table]['rows'][rid]['data']==bytes(expected),(table,rid)
 with CSV.open('w',encoding='utf-8-sig',newline='') as fp:
  w=csv.writer(fp);w.writerow(('角色行ID','字段','v0.9.1','待发布值'));w.writerows(log)
 template,_=decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
 encrypted=encrypt_native(template,bytes(data));assert decrypt_official(encrypted)[1]==bytes(data)
 REG.write_bytes(encrypted)
 print('changed fields:',len(log),'in rows',sorted(CHANGES),'regulation sha256:',hashlib.sha256(encrypted).hexdigest())
if __name__=='__main__':main()
