"""Guarantee the reusable heart on each selectable starting origin.

This parameter-only fix covers fresh characters even if event flag 60000 is
never reached by the flask-award event. Existing saves still need an event fix.
"""
from pathlib import Path
import csv
import struct
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parent/'work'))
from analyze_regulation import read_bnd
from field_diff import fields,defs,decode
from build_v04 import decrypt_official
from build_v05 import active_rows,encrypt_native

SOURCE=ROOT/'work/pending_spell_boss_bonus.bnd'
ASCENDED_BASE=ROOT/'work/v05_reconciled.bnd'
OUT=ROOT/'work/v0101_starter_heart.bnd'
REG=ROOT/'output/v0101_starter_heart_regulation.bin'
LOG=ROOT/'changes/v0.10.1_starter_heart.csv'
HEART=2001431

def main():
 version,mod=read_bnd(SOURCE);assert version=='11711000'
 raw=bytearray(SOURCE.read_bytes())
 t='CharaInitParam';f={x[0]:x for x in fields(defs()[mod[t]['ptype']])[0]}
 menu=mod['BaseChrSelectMenuParam'];mf={x[0]:x for x in fields(defs()[menu['ptype']])[0]}
 origins=sorted({decode(row['data'],mf['originChrInitParam']) for row in menu['rows'].values()
                 if decode(row['data'],mf['originChrInitParam']) in mod[t]['rows']})
 assert set(range(3000,3012))<=set(origins)
 offsets=active_rows(raw,t)
 edits=[]
 for rid in origins:
  data=mod[t]['rows'][rid]['data']
  # The five base classes have no origin-inventory slot; their visible starting
  # loadout comes from existing systems, so no empty slot is assumed here.
  empty=next((i for i in range(1,11) if decode(data,f[f'item_{i:02d}'])==-1),None)
  if empty is None:
   raise AssertionError(('no starter goods slot',rid))
  item=f[f'item_{empty:02d}'];num=f[f'itemNum_{empty:02d}']
  assert decode(data,num)==0 and item[1]=='s32' and num[1]=='u8'
  struct.pack_into('<i',raw,offsets[rid]+item[2],HEART)
  struct.pack_into('<B',raw,offsets[rid]+num[2],1)
  edits.append((rid,item[0],-1,HEART,num[0],0,1))

 # One reusable copy is enough. Prevent the v0.10 common event from adding a
 # second copy if the flask flag becomes true later.
 t='EquipParamGoods';gf={x[0]:x for x in fields(defs()[mod[t]['ptype']])[0]}
 goods=mod[t]['rows'][HEART]['data'];assert decode(goods,gf['maxNum'])==10
 off=active_rows(raw,t)[HEART]+gf['maxNum'][2]
 assert gf['maxNum'][1]=='s16'
 struct.pack_into('<h',raw,off,1)

 # v0.6 replaced Ascended's fixed Gparam 51 with 50 across all weather rows.
 # This also removed the intended night lighting from ordinary weather.
 # Restore the Ascended lighting on normal/rain/snow profiles, while keeping
 # fog-heavy profiles at the brighter value to avoid the previous blackouts.
 weather_ids=(0,1,10,11,20,21,30,40,41,60,82,83)
 _,asc=read_bnd(ASCENDED_BASE)
 wt='WeatherParam';wf={x[0]:x for x in fields(defs()[mod[wt]['ptype']])[0]}
 assert wf['GparamId'][1]=='u32'
 wo=active_rows(raw,wt)
 for rid in weather_ids:
  assert decode(mod[wt]['rows'][rid]['data'],wf['GparamId'])==50
  assert decode(asc[wt]['rows'][rid]['data'],wf['GparamId'])==51
  struct.pack_into('<I',raw,wo[rid]+wf['GparamId'][2],51)

 OUT.write_bytes(raw);_,after=read_bnd(OUT)
 assert len(after)==len(mod)
 for table in mod:
  for rid,row in mod[table]['rows'].items():
   got=after[table]['rows'][rid]['data']
   if table=='CharaInitParam' and rid in origins:
    expected=bytearray(row['data'])
    entry=next(x for x in edits if x[0]==rid)
    struct.pack_into('<i',expected,f[entry[1]][2],HEART)
    struct.pack_into('<B',expected,f[entry[4]][2],1)
    assert got==bytes(expected),(table,rid)
    continue
   if table=='EquipParamGoods' and rid==HEART:
    expected=bytearray(row['data']);struct.pack_into('<h',expected,gf['maxNum'][2],1)
    assert got==bytes(expected)
    continue
   if table=='WeatherParam' and rid in weather_ids:
    expected=bytearray(row['data']);struct.pack_into('<I',expected,wf['GparamId'][2],51)
    assert got==bytes(expected),(table,rid)
    continue
   assert got==row['data'],(table,rid)
 for rid,*_ in edits:
  data=after['CharaInitParam']['rows'][rid]['data']
  assert sum(decode(data,f[f'item_{i:02d}'])==HEART for i in range(1,11))==1
 template,_=decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
 encrypted=encrypt_native(template,bytes(raw))
 assert decrypt_official(encrypted)[1]==bytes(raw)
 REG.write_bytes(encrypted)
 with LOG.open('w',encoding='utf-8-sig',newline='') as file:
  w=csv.writer(file);w.writerow(('起始角色行ID','道具字段','旧值','新值','数量字段','旧值','新值'));w.writerows(edits)
 print('heart starter origins',origins,'night weather profiles',weather_ids,'encrypted size',len(encrypted))

if __name__=='__main__':main()
