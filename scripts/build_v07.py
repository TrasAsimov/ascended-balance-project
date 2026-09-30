"""Audit every player Magic row and rebalance linked spell hitboxes and FP."""
from __future__ import annotations
import csv, hashlib, json, struct, sys
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parent/'work'))
from field_diff import defs,fields,decode,names
from analyze_regulation import read_bnd
from build_v04 import decrypt_official
from build_v05 import active_rows,encrypt_native

STATS=('atkPhys','atkMag','atkFire','atkThun','atkDark')
STATUS=('Poison','Rotten','Ekzykes','Borealis','Dragonice','Frost','Blood','Flies','Scarlet','Madness','Frenzy','Death','Sleep','Magma','Rancor','Mist','Thorns','Bayle')
BREATHE=('Breath','Flame','Dragonfire','Dragonice','Dragonclaw','Dragonmaw','Greyoll')


def main():
 source=ROOT/'work/v06.bnd'; raw=bytearray(source.read_bytes())
 _,mod=read_bnd(source);_,van=read_bnd(ROOT/'work/vanilla_117.bnd')
 f={t:{x[0]:x for x in fields(defs()[mod[t]['ptype']])[0]} for t in ('Magic','Bullet','AtkParam_Pc','SpEffectParam')}
 offs={t:active_rows(raw,t) for t in ('Magic','AtkParam_Pc','SpEffectParam')}
 spellnames=names('Magic')
 def value(table,rid,name,db=mod):return decode(db[table]['rows'][rid]['data'],f[table][name])
 def change(table,rid,name,new):
  old=value(table,rid,name)
  if old==new:return False
  field=f[table][name];assert field[4] is None and field[6]==1
  fmt={'s16':'h','u16':'H'}[field[1]]
  struct.pack_into('<'+fmt,raw,offs[table][rid]+field[2],new)
  return True
 def linked(rid):
  queue=[value('Magic',rid,'refId'+str(j)) for j in range(1,11) if value('Magic',rid,'refId'+str(j))>0]
  seen=set();bullets=set();hits=set()
  while queue:
   item=queue.pop()
   if item in seen:continue
   seen.add(item)
   if item in mod['Bullet']['rows']:
    bullets.add(item)
    aid=value('Bullet',item,'atkId_Bullet')
    if aid>=1000 and aid in mod['AtkParam_Pc']['rows']:hits.add(aid)
    for key in ('HitBulletID','intervalCreateBulletId'):
     child=value('Bullet',item,key)
     if child>0 and child!=item:queue.append(child)
   elif item>=1000 and item in mod['AtkParam_Pc']['rows']:hits.add(item)
  return hits,bullets
 player=[rid for rid in sorted(mod['Magic']['rows']) if spellnames.get(rid,'').startswith(('[Sorcery]','[Incantation]'))]
 assert len(player)==217
 refs={rid:linked(rid) for rid in player}
 desired=defaultdict(list)
 detail=[]
 for rid in player:
  label=spellnames[rid]; kind='魔法' if label.startswith('[Sorcery]') else '祷告'
  base=value('Magic',rid,'mp',van);before=value('Magic',rid,'mp')
  # The old sweeping 2x FP cost is unsuited to the new 650 FP pool.
  proposed=round(base*1.5) if base>0 else before
  if base>0:proposed=max(base,proposed)
  cost_changed=change('Magic',rid,'mp',proposed)
  charge_base=value('Magic',rid,'mp_charge',van);charge_before=value('Magic',rid,'mp_charge')
  charge_new=round(charge_base*1.5) if charge_base>0 else charge_before
  charge_changed=change('Magic',rid,'mp_charge',charge_new)
  hits,bullets=refs[rid]
  category='状态或持续' if any(x in label for x in STATUS) else ('吐息或多段' if any(x in label for x in BREATHE) or len(hits)>=5 else '普通直击')
  target=1.25 if category=='状态或持续' else (1.5 if category=='吐息或多段' else 1.75)
  for aid in hits:
   if aid not in van['AtkParam_Pc']['rows']:continue
   for field in STATS:
    baseline=value('AtkParam_Pc',aid,field,van)
    if baseline>0:
     desired[(aid,field)].append((rid,target))
  detail.append([rid,kind,label,base,before,proposed,charge_base,charge_before,charge_new,
                 category,len(hits),len(bullets),','.join(map(str,sorted(hits))),
                 '需验证特效链' if not hits else '已追踪攻击判定'])
 changed=[];shared=[]
 for (aid,field),refs_for_hit in sorted(desired.items()):
  baseline=value('AtkParam_Pc',aid,field,van)
  # Shared hitboxes receive the conservative target from their linked spells.
  target=min(x[1] for x in refs_for_hit)
  proposed=max(1,round(baseline*target))
  before=value('AtkParam_Pc',aid,field)
  if change('AtkParam_Pc',aid,field,proposed):
   changed.append([aid,field,baseline,before,proposed,','.join(str(x[0]) for x in refs_for_hit)])
  if len(refs_for_hit)>1:shared.append((aid,field))
 # Restore the functional structure of indirect spells. Ascended changed
 # enchant flags, effect categories and targeting on several weapon buffs.
 effect_rows={};effect_audit=[]
 for rid in player:
  if refs[rid][0]:continue
  magic_row=mod['Magic']['rows'][rid]['data']
  effect_ids=set()
  for j in range(1,11):
   ref=decode(magic_row,f['Magic']['refId'+str(j)])
   cat=decode(magic_row,f['Magic']['refCategory'+str(j)])
   if cat==2 and ref in mod['SpEffectParam']['rows']:effect_ids.add(ref)
   if cat==1 and ref in mod['Bullet']['rows']:
    bullet_row=mod['Bullet']['rows'][ref]['data']
    for k in range(5):
     linked_id=decode(bullet_row,f['Bullet']['spEffectId'+str(k)])
     if linked_id in mod['SpEffectParam']['rows']:effect_ids.add(linked_id)
  for eid in sorted(effect_ids):
   if eid not in van['SpEffectParam']['rows']:continue
   old=mod['SpEffectParam']['rows'][eid]['data'];original=van['SpEffectParam']['rows'][eid]['data']
   if eid in effect_rows:
    assert effect_rows[eid]==rid or original==old
    continue
   if old==original:continue
   effect_rows[eid]=rid
   row=bytearray(original)
   endurance=f['SpEffectParam']['effectEndurance']
   base_duration=decode(original,endurance)
   # Keep limited duration buffs usable while avoiding 30-minute effects.
   if base_duration>0:
    struct.pack_into('<f',row,endurance[2],min(270.0,base_duration*1.5))
   for name in ('magicAttackPower','fireAttackPower','thunderAttackPower','darkAttackPower','physicsAttackPower'):
    field=f['SpEffectParam'][name]
    baseline=decode(original,field)
    if baseline>0 and decode(old,field)!=baseline:
     struct.pack_into('<i',row,field[2],round(baseline*1.5))
   if eid==1685000: # Bestial Vitality heals with a negative changeHpPoint.
    field=f['SpEffectParam']['changeHpPoint']
    struct.pack_into('<i',row,field[2],-8)
   pos=offs['SpEffectParam'][eid]
   raw[pos:pos+len(row)]=row
   effect_audit.append([rid,spellnames[rid],eid,
                        decode(old,endurance),base_duration,decode(row,endurance),
                        sum(decode(old,field)!=decode(original,field) for field in f['SpEffectParam'].values()),
                        '恢复原版效果结构，持续时间约 1.5 倍；更改过的附魔定值约 1.5 倍'])
 audit=ROOT/'changes/v0.7_spell_audit.csv';audit.parent.mkdir(exist_ok=True)
 with audit.open('w',encoding='utf-8-sig',newline='') as w:
  out=csv.writer(w);out.writerow(('法术ID','类别','英文名','原版FP','v0.6 FP','v0.7 FP','原版追加FP','v0.6追加FP','v0.7追加FP','伤害类别','追踪攻击数','追踪弹道数','攻击ID','审核状态'));out.writerows(detail)
 with (ROOT/'changes/v0.7_hitbox_changes.csv').open('w',encoding='utf-8-sig',newline='') as w:
  out=csv.writer(w);out.writerow(('攻击ID','属性字段','原版','v0.6','v0.7','关联法术ID'));out.writerows(changed)
 with (ROOT/'changes/v0.7_effect_audit.csv').open('w',encoding='utf-8-sig',newline='') as w:
  out=csv.writer(w);out.writerow(('法术ID','英文名','效果ID','v0.6持续时间','原版持续时间','v0.7持续时间','与原版不同字段数','处理'));out.writerows(effect_audit)
 target=ROOT/'work/v07.bnd';target.write_bytes(raw)
 ver,check=read_bnd(target);assert ver=='11711000' and len(check)==194
 changed_spell=set(player);changed_hits={x[0] for x in changed}
 for table in mod:
  for rid,row in mod[table]['rows'].items():
   if (table=='Magic' and rid in changed_spell or table=='AtkParam_Pc' and rid in changed_hits
       or table=='SpEffectParam' and rid in effect_rows):continue
   assert check[table]['rows'][rid]['data']==row['data'],(table,rid)
 for rid in player:
  for key in ('mp','mp_charge'):
   row=check['Magic']['rows'][rid]['data'];a=decode(row,f['Magic'][key]);b=next(x for x in detail if x[0]==rid)[5 if key=='mp' else 8]
   assert a==b,(rid,key,a,b)
 template,_=decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
 binary=encrypt_native(template,bytes(raw));assert decrypt_official(binary)[1]==bytes(raw)
 (ROOT/'output/v07_regulation.bin').write_bytes(binary)
 summary={'version':'v0.7-test','player_spells_reviewed':len(player),'npc_spell_rows_excluded':len(mod['Magic']['rows'])-len(player),
          'fp_rows_changed':sum(x[4]!=x[5] or x[7]!=x[8] for x in detail),'damage_fields_changed':len(changed),
          'untraced_spell_ids':[x[0] for x in detail if x[-1]=='需验证特效链'],
          'shared_hitbox_fields':len(shared),'regulation_sha256':hashlib.sha256(binary).hexdigest()}
 summary['indirect_effect_rows_repaired']=len(effect_audit)
 (ROOT/'output/v07_manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
