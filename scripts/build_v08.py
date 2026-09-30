"""Restore original riposte rules and rebalance gauge display and stamina."""
from __future__ import annotations
import csv,hashlib,json,struct,sys,zipfile
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parent/'work'))
from field_diff import defs,fields,decode,names
from analyze_regulation import read_bnd
from build_v04 import decrypt_official
from build_v05 import active_rows,encrypt_native

def main():
 source=ROOT/'work/v07.bnd';raw=bytearray(source.read_bytes())
 _,mod=read_bnd(source);_,van=read_bnd(ROOT/'work/vanilla_117.bnd')
 defs_by={t:{f[0]:f for f in fields(defs()[mod[t]['ptype']])[0]} for t in ('MenuCommonParam','CalcCorrectGraph','ThrowParam','NpcParam')}
 offsets={t:active_rows(raw,t) for t in defs_by}
 edits=[]
 def set_field(table,rid,name,new,reason):
  field=defs_by[table][name];assert field[4] is None
  before=decode(mod[table]['rows'][rid]['data'],field)
  if before==new:return
  fmt={'s32':'i','u32':'I','f32':'f'}[field[1]]
  assert struct.calcsize(fmt)==field[3]
  struct.pack_into('<'+fmt,raw,offsets[table][rid]+field[2],new)
  edits.append((table,rid,name,before,new,reason))
 for field,old,new,reason in (
  ('playerMaxHpLimit',28520,42780,'血条显示长度再缩至 1/1.5'),
  ('playerMaxMpLimit',3300,6600,'蓝条显示长度缩至一半'),
  ('playerMaxSpLimit',1920,960,'绿条显示长度扩大至 2 倍（实际精力另调整）')):
  assert decode(mod['MenuCommonParam']['rows'][0]['data'],defs_by['MenuCommonParam'][field])==old
  set_field('MenuCommonParam',0,field,new,reason)
 # Official Endurance 99 is 170, Ascended had reduced it to 120. A heavy
 # greatsword action typically costs 25-35 SP and the 90th percentile of
 # positive player actions is 36. 220 supports ~6 such attacks before rest.
 for name,before,new in [('stageMaxGrowVal0',80.0,80.0),
                         ('stageMaxGrowVal1',90.0,110.0),
                         ('stageMaxGrowVal2',100.0,145.0),
                         ('stageMaxGrowVal3',110.0,185.0),
                         ('stageMaxGrowVal4',120.0,220.0)]:
  assert decode(mod['CalcCorrectGraph']['rows'][104]['data'],defs_by['CalcCorrectGraph'][name])==before
  set_field('CalcCorrectGraph',104,name,new,'集中力以外，恢复并扩展耐力成长；99 耐力基础精力约 220')
 # The 1.16 mod changed 179 shared throw definitions. The updated official
 # version has every row and animation pairing. Restore all changed records;
 # never invent finishers for an originally unripostable monster.
 throw_restored=[];size=mod['ThrowParam']['row_size']
 assert size==van['ThrowParam']['row_size']
 assert mod['ThrowParam']['rows'].keys()==van['ThrowParam']['rows'].keys()
 for rid,record in mod['ThrowParam']['rows'].items():
  original=van['ThrowParam']['rows'][rid]['data']
  if record['data']==original:continue
  raw[offsets['ThrowParam'][rid]:offsets['ThrowParam'][rid]+size]=original
  throw_restored.append(rid)
  edits.append(('ThrowParam',rid,'whole_official_row','Ascended v0.7','official 1.17.1',
                '恢复原版处决位置、角度、动作和跟随时间'))
 assert len(throw_restored)==179
 # Two observed families have modded encounter height; official model anims
 # are installed separately in the package, including all mod-only variants.
 targeted_models={3010:'失乡骑士',4820:'噩兆猎人'}
 target_npc=[]
 for rid,rec in mod['NpcParam']['rows'].items():
  model=rid//10000
  if model not in targeted_models:continue
  base=van['NpcParam']['rows'].get(rid) or van['NpcParam']['rows'].get(model*10000)
  assert base is not None,(rid,model)
  for name in ('hitHeight','hitRadius'):
   original=decode(base['data'],defs_by['NpcParam'][name])
   before=decode(rec['data'],defs_by['NpcParam'][name])
   if before!=original:
    set_field('NpcParam',rid,name,original,'恢复原版处决接触范围；含 Ascended 新增同模型变体')
    target_npc.append(rid)
 audit=ROOT/'changes/v0.8_enemy_audit.csv';audit.parent.mkdir(exist_ok=True)
 npc_names=names('NpcParam')
 models_with_throw=defaultdict(list)
 for rid,rec in van['ThrowParam']['rows'].items():
  model=decode(rec['data'],defs_by['ThrowParam']['DefChrId'])
  if model>0:models_with_throw[model].append(rid)
 z=zipfile.ZipFile(ROOT/'output/Ascended_Balance_v0.7_Test.zip')
 replaced_anim={3010,4820}
 mod_anim={int(p.split('/')[-1][1:5]) for p in z.namelist()
           if p.endswith('.anibnd.dcx') and '/chr/c' in p and p.split('/')[-1][1:5].isdigit()}
 with audit.open('w',encoding='utf-8-sig',newline='') as out:
  w=csv.writer(out);w.writerow(('NPC 行 ID','Paramdex 名称','角色模型','新版原版有此 NPC 行','官方处决配对数','Ascended 覆盖动画','v0.8 恢复官方动画','处决参数','说明'))
  for rid in sorted(mod['NpcParam']['rows']):
   model=rid//10000; official=rid in van['NpcParam']['rows']
   status=('同模型新增变体；沿用官方处决配对' if not official and model in models_with_throw
           else 'Ascended 新行；官方无同模型处决配对' if not official else
           '原版存在；配对已恢复' if model in models_with_throw else '原版存在；未定义官方处决配对')
   w.writerow((rid,npc_names.get(rid,''),model,'是' if official else '否',len(models_with_throw[model]),
               '是' if model in mod_anim else '否','是' if model in replaced_anim else '否',
               '官方 1.17.1' if model in models_with_throw else '原版无',status))
 built=bytes(raw);target=ROOT/'work/v08.bnd';target.write_bytes(built)
 version,check=read_bnd(target);assert version=='11711000' and len(check)==194
 changed_npc=set(target_npc)
 for table in mod:
  for rid,row in mod[table]['rows'].items():
   if (table=='MenuCommonParam' and rid==0 or table=='CalcCorrectGraph' and rid==104
       or table=='ThrowParam' and rid in throw_restored or table=='NpcParam' and rid in changed_npc):continue
   assert row['data']==check[table]['rows'][rid]['data'],(table,rid)
 for rid in throw_restored:
  assert check['ThrowParam']['rows'][rid]['data']==van['ThrowParam']['rows'][rid]['data']
 official_template,_=decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
 binary=encrypt_native(official_template,built);assert decrypt_official(binary)[1]==built
 (ROOT/'output/v08_regulation.bin').write_bytes(binary)
 with (ROOT/'changes/v0.8_changes.csv').open('w',encoding='utf-8-sig',newline='') as out:
  w=csv.writer(out);w.writerow(('参数表','行 ID','字段','v0.7','v0.8','原因'));w.writerows(edits)
 summary={'version':'v0.8-test','npc_rows_audited':len(mod['NpcParam']['rows']),
          'npc_rows_new_vs_official':len(mod['NpcParam']['rows'].keys()-van['NpcParam']['rows'].keys()),
          'throw_rows_restored':len(throw_restored),'target_npc_rows_repaired':len(changed_npc),
          'official_animation_models_replaced':sorted(replaced_anim),
          'stamina_at_99_before':120,'stamina_at_99_after':220,
          'regulation_sha256':hashlib.sha256(binary).hexdigest()}
 (ROOT/'output/v08_manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
