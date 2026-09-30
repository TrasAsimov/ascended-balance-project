"""Stage neutral use marker for the one reusable starter Empowered Soul."""
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parent/'work'))
from analyze_regulation import read_bnd
from field_diff import defs,fields,decode
from build_v04 import decrypt_official
from build_v05 import active_rows,encrypt_native

SOURCE=ROOT/'work/pending_remembrance_attack.bnd'
OUT=ROOT/'work/pending_heart_marker.bnd'
REG=ROOT/'output/pending_heart_marker_regulation.bin'

def main():
 data=bytearray(SOURCE.read_bytes());_,m=read_bnd(SOURCE)
 t='EquipParamGoods';g=m[t]['rows'];f={x[0]:x for x in fields(defs()[m[t]['ptype']])[0]}
 effect=m['SpEffectParam']['rows'][321422]['data']
 ef={x[0]:x for x in fields(defs()[m['SpEffectParam']['ptype']])[0]}
 for field in ('maxHpRate','maxMpRate','maxStaminaRate','physicsAttackPowerRate',
               'magicAttackPowerRate','fireAttackPowerRate','thunderAttackPowerRate','darkAttackPowerRate'):
  assert decode(effect,ef[field])==1.0,(field,decode(effect,ef[field]))
 assert decode(g[2001431]['data'],f['refId_default'])==321412
 assert decode(g[2001431]['data'],f['isConsume'])==0
 assert not any(struct.pack('<i',321422) in row['data'] for table in m.values() for row in table['rows'].values())
 offset=active_rows(data,t)[2001431]+f['refId_default'][2]
 struct.pack_into('<i',data,offset,321422)
 OUT.write_bytes(data);_,check=read_bnd(OUT)
 for table,metadata in m.items():
  for rid,row in metadata['rows'].items():
   expected=bytearray(row['data'])
   if (table,rid)==(t,2001431):struct.pack_into('<i',expected,f['refId_default'][2],321422)
   assert check[table]['rows'][rid]['data']==bytes(expected),(table,rid)
 template,_=decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
 encrypted=encrypt_native(template,bytes(data))
 assert decrypt_official(encrypted)[1]==bytes(data)
 REG.write_bytes(encrypted)
 print('staged one neutral use marker (effect 321422) for Goods 2001431')

if __name__=='__main__':main()
