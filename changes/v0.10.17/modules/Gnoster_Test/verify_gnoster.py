from pathlib import Path
import json,sys,re,hashlib,tomllib,struct
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));import build_gnoster as b
baseline=b.BASE/'ModEngine/mod';candidate=b.MOD
flags={12020900,12020901,12020903};found=[];scanned=0
for p in (baseline/'event').glob('*.dcx'):
 e=b.Emevd(b.unpack(p.read_bytes()));scanned+=1
 for event in e.events:
  for ins in event['ins']:
   try:args=b.decode_args(ins)
   except KeyError:continue
   for k,v in args:
    if 'Flag ID' in k and v in flags:found.append([str(p.relative_to(baseline)),event['id'],k,v])
assert not found,found
config=tomllib.loads((b.OUT/'ModEngine/evernight_gnoster_t1.me3').read_text());assert len(config['packages'])==1 and config['packages'][0]['path']=='mod';assert len(config['natives'])==2
for n in config['natives']:assert (b.OUT/'ModEngine'/n['path']).is_file()
assert config['natives'][1]['initializer']['function']=='CaligoHpCapInitialize'
ps=(b.OUT/'ModEngine/check_gnoster_t1.ps1').read_text(encoding='utf-8-sig');pairs=re.findall(r" '([^']+)'='([0-9a-f]{64})'",ps)
for p,h in pairs:assert b.sha((b.OUT/'ModEngine'/p.replace('\\','/')).read_bytes())==h
bat=(b.OUT/'ModEngine/launchmod_eldenring.bat').read_bytes();assert b'\\r\\n' not in bat and b'\r\n' in bat and b'evernight_gnoster_t1.me3' in bat
# Restore each old minor-boss counter result, except replacement only when newly defeated.
e=b.Emevd(b.unpack((candidate/'event/common.emevd.dcx').read_bytes()));tail=next(x for x in e.events if x['id']==20007902)['ins'][72:]
manifest=json.load(open(b.ROOT/'repo/data/minor_boss_heart.json'));minor=[x['flag_id'] for x in manifest['bosses']]
minor=sorted(set(minor));assert minor
count,fx=b.simulate_tail(tail,set(minor),b.I);assert count==len(minor),(count,len(minor))
count,fx=b.simulate_tail(tail,set(minor)|{b.DEFEAT},b.I);assert count==len(minor)-1 and b.PARENT in fx
for flag in minor:
 count,fx=b.simulate_tail(tail,{flag},b.I);assert count==1
# Explicitly retain native Caligo AI, HP clamp, sounds and all snowfield files.
for rel in ['script/490000_battle.luabnd.dcx','event/m60_54_56_00.emevd.dcx']:
 assert (candidate/rel).read_bytes()==(baseline/rel).read_bytes()
for rel in ['CaligoHpCapFix.dll','ExpandedTalismanSlots.dll','ExpandedTalismanSlots.ini']:
 assert (b.OUT/'ModEngine'/rel).read_bytes()==(b.BASE/'ModEngine'/rel).read_bytes()
result={'base_event_files_scanned_for_direct_flag_collision':scanned,'new_flag_collisions':found,'PS1_sha_checks':len(pairs),'minor_reward_cases':len(minor)+2,'Caligo_and_player_Dlls_unchanged':True,'ME3_one_mod_two_natives':True,'game_test':'NOT RUN'}
(b.OUT/'Gnoster_Test/verification.json').write_text(json.dumps(result,indent=2));print(result)
