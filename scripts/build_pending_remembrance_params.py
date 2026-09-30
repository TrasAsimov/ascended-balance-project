"""Pending remembrance/heart parameter alignment; event-backed aggregator is separate."""
from __future__ import annotations
import csv,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parent/'work'))
from analyze_regulation import read_bnd
from field_diff import defs,fields,decode
from build_v04 import decrypt_official
from build_v05 import active_rows,encrypt_native

SOURCE=ROOT/'work/pending_watchdog_no_skill.bnd'
OUT=ROOT/'work/pending_remembrance_params.bnd'
REG=ROOT/'output/pending_remembrance_params_regulation.bin'
DLC_IDS=(2002900,2002901,2002902,2002903,2002904,
         2002905,2002907,2002908,2002909,2002910)
EFFECT_IDS=tuple(range(321412,321422))
SPECIAL_BASE_IDS=(2950,2951,2954,2959)
NORMAL_BASE_IDS=(2952,2953,2955,2956,2957,2958,2960,2961,2962,2963,2964)
HEART_LOTS={10401:2001431,10461:2001432,10481:2001433,10551:2001434,
            10561:2001435,10601:2001436,10622:2001437,10632:2001438,
            10641:2001439,10901:2001440}

def main():
 data=bytearray(SOURCE.read_bytes());_,mod=read_bnd(SOURCE)
 goods=mod['EquipParamGoods']['rows'];fx=mod['SpEffectParam']['rows']
 lots=mod['ItemLotParam_map']['rows']
 gf={x[0]:x for x in fields(defs()[mod['EquipParamGoods']['ptype']])[0]}
 sf={x[0]:x for x in fields(defs()[mod['SpEffectParam']['ptype']])[0]}
 lf={x[0]:x for x in fields(defs()[mod['ItemLotParam_map']['ptype']])[0]}
 go=active_rows(data,'EquipParamGoods');so=active_rows(data,'SpEffectParam')
 lo=active_rows(data,'ItemLotParam_map')
 logs=[];expected={('EquipParamGoods',rid):bytearray(goods[rid]['data']) for rid in DLC_IDS}
 expected.update({('SpEffectParam',rid):bytearray(fx[rid]['data']) for rid in EFFECT_IDS})
 expected.update({('ItemLotParam_map',rid):bytearray(lots[rid]['data']) for rid in HEART_LOTS})
 def patch_s32(table,rid,field,value):
  f={'EquipParamGoods':gf,'SpEffectParam':sf,'ItemLotParam_map':lf}[table]
  offset={'EquipParamGoods':go,'SpEffectParam':so,'ItemLotParam_map':lo}[table]
  x=f[field];assert x[1]=='s32' and x[4] is None
  old=decode(mod[table]['rows'][rid]['data'],x);assert old!=value,(table,rid,field)
  struct.pack_into('<i',data,offset[rid]+x[2],value)
  struct.pack_into('<i',expected[(table,rid)],x[2],value)
  logs.append((table,rid,field,old,value))
 def patch_f32(table,rid,field,value):
  x=sf[field];assert table=='SpEffectParam' and x[1]=='f32' and x[4] is None
  old=decode(fx[rid]['data'],x);assert old==1.05 and value==1.0,(rid,field,old)
  struct.pack_into('<f',data,so[rid]+x[2],value)
  struct.pack_into('<f',expected[(table,rid)],x[2],value)
  logs.append((table,rid,field,old,value))
 def clear_consume(rid):
  x=gf['isConsume'];assert x[1]=='u8' and x[4]==1
  original=goods[rid]['data'];before=decode(original,x)
  if before==0:return
  assert before==1
  mask=1<<x[5];index=go[rid]+x[2]
  data[index]&=~mask;expected[('EquipParamGoods',rid)][x[2]]&=~mask
  logs.append(('EquipParamGoods',rid,'isConsume',1,0))
 for good,eid in zip(DLC_IDS,EFFECT_IDS):
  assert good in goods and eid in fx
  patch_s32('EquipParamGoods',good,'refId_default',eid)
  clear_consume(good)
  # Match the eleven standard base-game remembrances: HP and attack power,
  # with no 5% FP/stamina bonus on the DLC remembrance itself.
  for field in ('maxMpRate','maxStaminaRate'):patch_f32('SpEffectParam',eid,field,1.0)
  assert decode(fx[eid]['data'],sf['maxHpRate'])==1.05
  for field in ('physicsAttackPowerRate','magicAttackPowerRate','fireAttackPowerRate','thunderAttackPowerRate','darkAttackPowerRate'):
   assert decode(fx[eid]['data'],sf[field])==1.05
 # The original mod stores each extra heart in a separate map item-lot row
 # immediately after the matching remembrance lot. Clear only those rows.
 for lot,heart in HEART_LOTS.items():
  assert decode(lots[lot]['data'],lf['lotItemId01'])==heart
  assert decode(lots[lot]['data'],lf['lotItemCategory01'])==1
  assert decode(lots[lot]['data'],lf['lotItemBasePoint01'])==1000
  assert decode(lots[lot]['data'],lf['getItemFlagId'])==decode(lots[lot-1]['data'],lf['getItemFlagId'])
  # Two adjacent rewards are Miquella's Great Rune and Messmer's Kindling;
  # preserve these story rewards while removing only the extra heart row.
  assert decode(lots[lot-1]['data'],lf['lotItemId01']) in set(DLC_IDS)|(set([2008000,2008021]))
  patch_s32('ItemLotParam_map',lot,'lotItemId01',0)
  patch_s32('ItemLotParam_map',lot,'lotItemCategory01',0)
 assert set(SPECIAL_BASE_IDS+NORMAL_BASE_IDS)==set(range(2950,2965))
 for rid in SPECIAL_BASE_IDS:
  assert goods[rid]['data']==mod['EquipParamGoods']['rows'][rid]['data']
 OUT.write_bytes(data);version,check=read_bnd(OUT)
 assert version=='11711000' and len(check)==194
 for table in mod:
  for rid,row in mod[table]['rows'].items():
   assert check[table]['rows'][rid]['data']==bytes(expected.get((table,rid),row['data'])),(table,rid)
 with (ROOT/'changes/pending_remembrance_params.csv').open('w',encoding='utf-8-sig',newline='') as fp:
  w=csv.writer(fp);w.writerow(('参数表','行ID','字段','原值','待合并值'));w.writerows(logs)
 template,_=decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
 encrypted=encrypt_native(template,bytes(data));assert decrypt_official(encrypted)[1]==bytes(data)
 REG.write_bytes(encrypted)
 print('DLC remembrance rows',len(DLC_IDS),'parameter edits',len(logs),'special base remembrances unchanged',SPECIAL_BASE_IDS)
if __name__=='__main__':main()
