"""Align six talisman effects with requested bonuses and audit two others."""
from __future__ import annotations
import csv,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parent/'work'))
from field_diff import defs,fields,decode,names
from analyze_regulation import read_bnd
from build_v04 import decrypt_official
from build_v05 import active_rows,encrypt_native

GOALS={2090:('短剑护符','处决伤害 +400%',5.0),2120:('双头剑护符','攻击链末段伤害 +150%',2.5),
       2130:('斧护符','蓄力攻击伤害 +320%',4.2),2180:('爪护符','跳跃攻击伤害 +150%',2.5),
       2200:('曲剑护符','防御反击伤害 +300%',4.0)}
DAMAGE=('physicsAttackRate','magicAttackRate','fireAttackRate','thunderAttackRate','darkAttackRate')

def main():
 source=ROOT/'work/v08.bnd';data=bytearray(source.read_bytes())
 _,mod=read_bnd(source);_,van=read_bnd(ROOT/'work/vanilla_117.bnd')
 f={x[0]:x for x in fields(defs()[mod['SpEffectParam']['ptype']])[0]}
 offsets=active_rows(data,'SpEffectParam');access=mod['EquipParamAccessory']['rows'];changes=[];changed_ids=set()
 def effect(aid):
  eid=struct.unpack_from('<i',access[aid]['data'],4)[0]
  assert eid in mod['SpEffectParam']['rows']
  return eid
 def put(aid,name,field,value,reason):
  eid=effect(aid);fld=f[field];assert fld[1]=='f32' and fld[4] is None
  old=decode(mod['SpEffectParam']['rows'][eid]['data'],fld)
  assert old!=value,(aid,field)
  struct.pack_into('<f',data,offsets[eid]+fld[2],value)
  changes.append([aid,name,eid,field,old,value,reason]);changed_ids.add(eid)
 for aid,(name,label,mult) in GOALS.items():
  eid=effect(aid)
  for field in DAMAGE:
   old=decode(mod['SpEffectParam']['rows'][eid]['data'],f[field])
   assert old in (1.5,1.8,2.0),(aid,field,old)
   put(aid,name,field,mult,'指定触发条件下，原伤害额外 +'+str(round((mult-1)*100))+'%；仅处理原效果行')
 assert effect(4100)==341000
 put(4100,'大盾护符','guardStaminaCutRate',0.1,'格挡精力消耗降低 90%，原消耗乘 0.1')
 # No false promise of exact final damage: this is a 4x spell *attack
 # power* multiplier; the bow effect is a 1.5x damage coefficient.
 magic=effect(2140);arrow=effect(2150)
 assert magic==321400 and arrow==321500
 assert all(decode(mod['SpEffectParam']['rows'][magic]['data'],f[k])==4.0 for k in
            ('physicsAttackPowerRate','magicAttackPowerRate','fireAttackPowerRate','thunderAttackPowerRate','darkAttackPowerRate'))
 assert all(decode(mod['SpEffectParam']['rows'][arrow]['data'],f[k])==1.5 for k in DAMAGE)
 target=ROOT/'work/v09.bnd';target.write_bytes(data)
 version,check=read_bnd(target);assert version=='11711000' and len(check)==194
 for table in mod:
  for rid,record in mod[table]['rows'].items():
   if table=='SpEffectParam' and rid in changed_ids:continue
   assert check[table]['rows'][rid]['data']==record['data'],(table,rid)
 for aid,_,_,field,_,new,_ in changes:
  assert abs(decode(check['SpEffectParam']['rows'][effect(aid)]['data'],f[field])-new)<1e-5
 template,_=decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
 binary=encrypt_native(template,bytes(data));assert decrypt_official(binary)[1]==bytes(data)
 (ROOT/'output/v09_regulation.bin').write_bytes(binary)
 with (ROOT/'changes/v0.9_talismans.csv').open('w',encoding='utf-8-sig',newline='') as out:
  w=csv.writer(out);w.writerow(('护符ID','中文名','效果ID','字段','v0.8','v0.9','含义'));w.writerows(changes)
 # Every bow has independently modded weapon base damage; expose it so a
 # bow's overall power is not mistaken for the talisman's isolated bonus.
 wf={x[0]:x for x in fields(defs()[mod['EquipParamWeapon']['ptype']])[0]}
 wn=names('EquipParamWeapon')
 keys=tuple(x for x in wf if x.startswith('attackBase'))
 with (ROOT/'changes/v0.9_bow_audit.csv').open('w',encoding='utf-8-sig',newline='') as out:
  w=csv.writer(out);w.writerow(('武器ID','英文名','属性字段','Ascended v0.8','官方1.17.1','说明'))
  for rid,record in sorted(mod['EquipParamWeapon']['rows'].items()):
   if not 40000000<=rid<43000000 or rid not in van['EquipParamWeapon']['rows']:continue
   base=van['EquipParamWeapon']['rows'][rid]['data']
   for key in keys:
    current=decode(record['data'],wf[key]);official=decode(base,wf[key])
    if current!=official:
     w.writerow((rid,wn.get(rid,''),key,current,official,'弓本体改动；与硬箭护符倍率独立'))
 summary={'version':'v0.9-test','talisman_field_edits':len(changes),
          'talisman_ids':sorted(GOALS.keys()|{4100}),'magic_attack_power_multiplier':4.0,
          'arrow_talisman_damage_coefficient':1.5,
          'regulation_sha256':hashlib.sha256(binary).hexdigest()}
 (ROOT/'output/v09_manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
