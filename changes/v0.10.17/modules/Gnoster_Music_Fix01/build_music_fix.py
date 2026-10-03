from pathlib import Path
import sys,json,struct,copy,hashlib,zipfile,re
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'boss_hp_t2/source'))
from formats import Emevd,dcx_unpack,dcx_pack,instruction_builder
BASE=R.parent/'boss_hp_t2/Evernight_Reforged_Boss_HP_T2_Full_Test.zip';BASE_SHA='dd57506cfcf913fe264589c230cce5459eedbd0a5f752c12e2623fa16b73eb0f';PREFIX='Evernight_Reforged_Boss_HP_T2/'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 assert sha(BASE.read_bytes())==BASE_SHA
 with zipfile.ZipFile(BASE) as z:files={n[len(PREFIX):]:z.read(n) for n in z.namelist()}
 path='ModEngine/mod/event/m12_02_00_00.emevd.dcx';orig=files[path];e=Emevd(dcx_unpack(orig));before=copy.deepcopy(e.events);I=instruction_builder(R/'source/er-common.emedf.json');entry=next(x for x in e.events if x['id']==12022810);assert not entry['params']
 authority=[I(1003,12,2,1),I(2009,6,0),I(2004,28,12025800,8192)]
 idx=next(i for i,ins in enumerate(entry['ins']) if ins[:2]==(1014,2));entry['ins'][idx+1:idx+1]=authority
 bar=I(2003,11,1,12020800,0,904910001);idx=entry['ins'].index(bar);ready=[I(1003,12,1,1),I(2003,69,0,12022805,1)];entry['ins'][idx+1:idx+1]=ready
 for old,new in zip(before,e.events):
  if old['id']!=12022810:assert old==new
  else:
   restored=new['ins'].copy()
   for block in [authority,ready]:
    matches=[i for i in range(len(restored)) if restored[i:i+len(block)]==block];assert len(matches)==1;pos=matches[0];del restored[pos:pos+len(block)]
   assert restored==old['ins'] and new['rest']==old['rest']
 new=dcx_pack(e.write());assert Emevd(dcx_unpack(new)).events==e.events
 fog=next(x for x in e.events if x['id']==12022849);music=[struct.unpack('<'+'I'*(len(i[2])//4),i[2]) for i in fog['ins'] if i[:2]==(2000,6) and struct.unpack_from('<I',i[2],4)[0]==9005822];assert music==[(0,9005822,12020900,931000,12022805,12022806,0,12020903,0,0)]
 # Both fresh and retry join Label2. Dead branch ends before Label0/Label2.
 assert entry['ins'].index(I(1000,103,2))<entry['ins'].index(I(1014,2))
 assert entry['ins'].index(I(1000,4,0))<entry['ins'].index(I(1014,0))
 cases=[]
 for world in [0,1]:
  notified=False;auth=None;flag=False;pc=0
  for block in [authority,ready]:
   pc=0
   while pc<len(block):
    ins=block[pc];pc+=1
    if ins[:2]==(1003,12):skip,w=struct.unpack('<BB2x',ins[2]);pc+=skip if world==w else 0
    elif ins[:2]==(2009,6):notified=True
    elif ins[:2]==(2004,28):auth=struct.unpack('<Ii',ins[2])
    elif ins[:2]==(2003,69):flag=True
    else:raise AssertionError(ins[:2])
  assert (notified and flag and auth==(12025800,8192)) if world==0 else (not notified and not flag and auth is None);cases.append({'world':world,'notify':notified,'authority':auth,'host_battle_flag_set':flag})
 patch={path:new,'ModEngine/mod/regulation.bin':files['ModEngine/mod/regulation.bin']}
 check='ModEngine/check_gnoster_t1.ps1';ps=files[check].decode('utf-8-sig');assert ps.count(sha(orig))==1;ps=ps.replace(sha(orig),sha(new)).replace('Boss HP T2 complete runtime verified.','Boss HP T2 + Gnoster music fix runtime verified.');patch[check]=b'\xef\xbb\xbf'+ps.encode()
 audit={'version':'Gnoster Music Fix01 over Boss HP T2','baseline_SHA256':BASE_SHA,'modified_game_event_only':12022810,'inserted_instruction_count':5,'all_other_map_events_unchanged':True,'fresh_and_retry_share_Label2':True,'defeated_branch_skips_new_notifications':True,'host_visitor_instruction_cases':cases,'native_music_handler_retained':music,'music_id':931000,'music_native_Wwise_conversion':'MidBoss_Cave','music_parameters':{'defeat':12020900,'host_entered':12022805,'visitor_entered':12022806,'phase':12020903},'parameter_HP_resistance_attack_models_map_AI_DLLs_preserved_from_T2':True,'new_regulation_changes':False,'diagnosis':'Static: donor entry omitted boss room notification and explicit host-entered flag required by retained native music condition. Exact client-state cause is not observed; fix remains candidate.','before_map_SHA256':sha(orig),'after_map_SHA256':sha(new),'game_test':'NOT RUN'}
 patch['Gnoster_Music_Fix01/audit.json']=json.dumps(audit,ensure_ascii=False,indent=2).encode();patch['Gnoster_Music_Fix01/build_music_fix.py']=Path(__file__).read_bytes();patch['Gnoster_Music_Fix01/source/formats.py']=(R.parent/'boss_hp_t2/source/formats.py').read_bytes();patch['Gnoster_Music_Fix01/source/er-common.emedf.json']=(R/'source/er-common.emedf.json').read_bytes()
 note='''双虫音乐修正01（累积最新HP T2）
应安装在已含双虫的Gnoster T1或HP T2完整包上；本小包不包含虫子模型等资源。
彻底退出游戏，把全部解压内容覆盖到当前完整包根目录（与ModEngine同级），继续运行ModEngine/launchmod_eldenring.bat。传送离开导水桥再返回，或完全重启游戏以重载地图。
保留原场地原生931000/MidBoss_Cave配乐；不是黑夜君临双虫原曲，未使用CMI/新音乐素材。补齐首次/重试共同入场路径中的主机战斗通知、Boss组网络权限和12022805战斗入场标记，保留原生音乐处理器/骑乘阶段12020903和击败12020900停止条件。访客沿用原生12022806逻辑，本地静态检查不等于联机验收。
本包同时带HP T2 regulation和更新后的启动哈希：Caligo1125000、Gnoster585384、Faurtis914616（NG0名义，周目/联机另缩放），冰龙60%转阶段，双虫原比例保持；HP T2的参数原件保持，不再次乘血量。不要只复制event，否则旧启动校验拒绝启动。
静态/文件检查通过，未运行Windows游戏。此次未读取用户游戏音量/运行事件状态，音乐缺失确切客户端原因未证实；请复测首次入场、赐福重试、骑乘阶段、击败后音乐停止。既有源资源缺引用限制保持。
'''
 patch['Gnoster_Music_Fix01/README.txt']=note.encode('utf-8-sig');readme=files['README.txt'].decode('utf-8-sig');patch['README.txt']=b'\xef\xbb\xbf'+('已应用双虫音乐修正01；详见Gnoster_Music_Fix01/README.txt。\n'+readme).encode()
 final={**files,**patch};manifest={k:sha(v) for k,v in final.items() if k!='Gnoster_Test/manifest.json'};patch['Gnoster_Test/manifest.json']=json.dumps(manifest,indent=2).encode();final.update(patch)
 checks=re.findall(r" '([^']+)'='([0-9a-f]{64})'",ps)
 for p,h in checks:assert sha(final['ModEngine/'+p.replace('\\','/')])==h
 for k,v in files.items():
  if k not in patch:assert final[k]==v
 package=R/'Gnoster_Music_Fix01_With_HP_T2_Update.zip'
 with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for k,v in sorted(patch.items()):z.writestr(k,v)
 with zipfile.ZipFile(package) as z:
  assert z.testzip() is None
  for k,v in patch.items():assert z.read(k)==v
 summary={'zip':str(package),'size':package.stat().st_size,'sha256':sha(package.read_bytes()),'PS1_verified_files':len(checks),'audit':audit};(R/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
