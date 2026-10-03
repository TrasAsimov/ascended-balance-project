from pathlib import Path
import sys,struct,json,zipfile,hashlib,copy,re
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'source'))
from build_v03 import decrypt,encrypt
from analyze_regulation import read_bnd
from formats import bnd_entries,param_patch
from field_diff import fields,decode
BASE=R.parent/'gnoster_recovery/Evernight_Reforged_Gnoster_T1_Full_Test.zip';BASHA='de1b6b69738af82a3dc8eb11462880467804d01b2bcdab7ece2ceb8bd6d1c333';OLD='Evernight_Reforged_Gnoster_T1/';NEW='Evernight_Reforged_Boss_HP_T2/'
PLAN={49010010:(62500,93750),75200000:(24391,48782),75300000:(38109,76218)}
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 assert sha(BASE.read_bytes())==BASHA
 with zipfile.ZipFile(BASE) as z:
  assert z.testzip() is None; files={n[len(OLD):]:z.read(n) for n in z.namelist()};infos={n[len(OLD):]:copy.copy(z.getinfo(n)) for n in z.namelist()}
 reg=files['ModEngine/mod/regulation.bin'];template,raw=decrypt(reg);(R/'before.bnd').write_bytes(raw);ver,T=read_bnd(R/'before.bnd');assert ver=='11711000'
 fs,size=fields(R/'source/NpcParam.xml');hp=next(x for x in fs if x[0]=='hp');assert hp==('hp','u32',36,4,None,None,1) and size==T['NpcParam']['row_size']==736
 changes={};changed_rows=[]
 for rid,(old,new) in PLAN.items():
  row=T['NpcParam']['rows'][rid]['data'];assert decode(row,hp)==old
  body=bytearray(row);struct.pack_into('<I',body,hp[2],new);assert body[:36]==row[:36] and body[40:]==row[40:];changes[rid]=bytes(body);changed_rows.append({'NPC':rid,'old_base_HP':old,'new_base_HP':new,'old_NG0_nominal_HP':old*12,'new_NG0_nominal_HP':new*12})
 members=bnd_entries(raw);head,npc=members['NpcParam.param'];np=param_patch(npc,changes,{},size);off=struct.unpack_from('<I',raw,head+24)[0];out=bytearray(raw);out[off:off+len(np)]=np
 allowed=set()
 for rid,pad,data,name in (struct.unpack_from('<iIQQ',npc,64+24*i) for i in range(struct.unpack_from('<H',npc,10)[0])):
  if rid in PLAN:allowed.update(range(off+data+36,off+data+40))
 diffs=[i for i,(x,y) in enumerate(zip(raw,out)) if x!=y];assert len(out)==len(raw) and diffs and set(diffs)<=allowed
 merged=encrypt(template,bytes(out));assert decrypt(merged)[1]==out;(R/'after.bnd').write_bytes(out);v,M=read_bnd(R/'after.bnd');assert v==ver
 preserved=0
 for table,t in T.items():
  assert M[table]['rows'].keys()==t['rows'].keys()
  for rid,row in t['rows'].items():
   if table=='NpcParam' and rid in PLAN:assert M[table]['rows'][rid]['data']==changes[rid]
   else:assert M[table]['rows'][rid]['data']==row['data'];preserved+=1
 # Validate the 12x HP region directly by its current layout: fetch SpEffect schema.
 fxfs,_=fields(R/'source/SpEffect.xml');maxhp=next(x for x in fxfs if x[0]=='maxHpRate');assert decode(M['SpEffectParam']['rows'][7180]['data'],maxhp)==12
 patch={'ModEngine/mod/regulation.bin':merged}
 check='ModEngine/check_gnoster_t1.ps1';ps=files[check].decode('utf-8-sig');assert ps.count(sha(reg))==1;ps=ps.replace(sha(reg),sha(merged)).replace('Gnoster T1 complete runtime verified.','Boss HP T2 complete runtime verified.');patch[check]=b'\xef\xbb\xbf'+ps.encode()
 readme=files['README.txt'].decode('utf-8-sig').replace('Gnoster/Faurtis T1完整内测包','Boss HP T2完整内测包').replace('双虫合计名义单周目750000','双虫合计名义单周目1500000').replace('Gnoster约292692','Gnoster约585384').replace('Faurtis约457308','Faurtis约914616')
 readme=readme.replace('包含v0.10.16全部核心与Caligo','本版冰龙Caligo从750000提高50%至1125000；二阶段保持当前最大血量60%，NG0名义675000时转阶段。双虫两只各在T1基础上翻倍；本轮仅三只NPC的hp字段修改。周目/联机另缩放，原HP模块保留，未运行Windows游戏。\nGnoster_Test下旧审计为T1历史，本轮当前数值见Boss_HP_T2/audit.json。\n\n包含v0.10.16全部核心与Caligo');patch['README.txt']=b'\xef\xbb\xbf'+readme.encode()
 hist=json.loads(files['Gnoster_Test/audit.json']);hist['scope']='Historical T1 integration audit. Current HP superseded by Boss_HP_T2/audit.json.';patch['Gnoster_Test/audit.json']=json.dumps(hist,ensure_ascii=False,indent=2).encode()
 audit={'version':'Boss HP T2','baseline_SHA256':BASHA,'NPC_changes':changed_rows,'only_gameplay_changes':'three private NPC hp fields','raw_regulation_byte_changes':len(diffs),'preserved_other_PARAM_rows':preserved,'regional_HP_scale':12,'Caligo_phase':{'ratio':0.6,'NG0_nominal_HP':675000,'AI_and_event_bytes_preserved':True},'bug_stage_ratios_preserved':True,'attack_resistance_rewards_player_shared_HP_effect_DLLs_unchanged':True,'source_missing_dependencies_carried_from_T1':True,'before_regulation_SHA256':sha(reg),'after_regulation_SHA256':sha(merged),'game_test':'NOT RUN'}
 patch['Boss_HP_T2/audit.json']=json.dumps(audit,ensure_ascii=False,indent=2).encode();patch['Boss_HP_T2/build_hp_t2.py']=Path(__file__).read_bytes()
 for p in (R/'source').iterdir():
  if p.is_file():patch['Boss_HP_T2/source/'+p.name]=p.read_bytes()
 files.update(patch)
 assert all(files[k]==v for k,v in {k:files[k] for k in []}.items())
 pschecks=re.findall(r" '([^']+)'='([0-9a-f]{64})'",ps);assert len(pschecks)==1014
 for p,h in pschecks:assert sha(files['ModEngine/'+p.replace('\\','/')])==h,(p,h)
 manifest={k:sha(v) for k,v in files.items() if k!='Gnoster_Test/manifest.json'};files['Gnoster_Test/manifest.json']=json.dumps(manifest,indent=2).encode();patch['Gnoster_Test/manifest.json']=files['Gnoster_Test/manifest.json']
 update=R/'Evernight_Boss_HP_T2_Update.zip'
 guide='只适用于已安装的完整Gnoster/Faurtis T1包。彻底退出游戏，将本更新的ModEngine、Gnoster_Test、Boss_HP_T2和README.txt覆盖到T1包根目录。继续运行ModEngine/launchmod_eldenring.bat。传送离开再返回，或完全重启游戏，重新载入Boss。不要只复制regulation.bin，启动校验也已更新。\nCaligo1125000；Gnoster585384；Faurtis914616。其它攻击/抗性/奖励/阶段比例保持。本更新不能把不含虫子的v0.10.16变成完整双虫版本；尚未Windows实机验证。\n'
 with zipfile.ZipFile(update,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for k,v in sorted(patch.items()):z.writestr(k,v)
  z.writestr('HP_T2_Update_说明.txt',guide.encode('utf-8-sig'))
 with zipfile.ZipFile(update) as z:
  assert z.testzip() is None
  for k,v in patch.items():assert z.read(k)==v
 full=R/'Evernight_Reforged_Boss_HP_T2_Full_Test.zip'
 with zipfile.ZipFile(full,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for k,v in sorted(files.items()):
   if k in infos:info=infos[k];info.filename=NEW+k
   else:info=zipfile.ZipInfo(NEW+k,(2026,10,3,12,50,0));info.compress_type=zipfile.ZIP_DEFLATED
   z.writestr(info,v,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
 with zipfile.ZipFile(full) as z:
  assert z.testzip() is None
  for k,h in manifest.items():assert sha(z.read(NEW+k))==h
  assert z.read(NEW+'Gnoster_Test/manifest.json')==files['Gnoster_Test/manifest.json']
 summary={'full_zip':str(full),'full_size':full.stat().st_size,'full_SHA256':sha(full.read_bytes()),'update_zip':str(update),'update_size':update.stat().st_size,'update_SHA256':sha(update.read_bytes()),'changed_existing_relative_paths':[k for k in patch if k in infos],'PS1_verified_files':len(pschecks),'audit':audit};(R/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
