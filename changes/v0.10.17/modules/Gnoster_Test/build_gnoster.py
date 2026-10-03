"""Gnoster/Faurtis integration over pinned single-directory v0.10.16."""
from pathlib import Path
import sys,struct,json,csv,copy,math,hashlib,collections,re,tomllib,zipfile,shutil,subprocess,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];TASK=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'repo/scripts'),str(ROOT/'repo/systems/armor/scripts'),str(ROOT/'work'),str(ROOT/'bridge_hotfix'),str(ROOT/'hp_damage_x2'),str(TASK)]
from analyze_regulation import read_bnd
from field_diff import fields,decode,TYPES
from formats import bnd_entries,bnd_repack,bnd_patch,param_patch,dcx_pack,dcx_unpack,Emevd,instruction_builder
from build_v03 import decrypt,encrypt
from inspect_maps import unpack,parse
from build_hotfix import chunks,rebuild,refs
from fmg import fmg_read,fmg_write
from event_inspect import SPEC,FMT,decode_args
from build_t3 import simulate_tail
from lupa import LuaRuntime
BASE=TASK/'baseline/Ascended_Balance_v0.10.16';DONOR=TASK/'incoming/mod';OUT=TASK/'Evernight_Reforged_Gnoster_T1';MOD=OUT/'ModEngine/mod'
FAURTIS=12020800;MOTH=12020801;DEFEAT=12020900;FIRST=12020901;PARENT=7400202;CHILD=7410202
DOCS=ROOT/'ds/DarkScript3/Resources/er-common.emedf.json';I=instruction_builder(DOCS)
AUDIT={'base_version':'v0.10.16','game_test':'NOT RUN','source':'Lwingr Gnoster Overhaul1.2.5 Nexus8406','HP_choice':'user selected total750000; preserve donor relative HP budget','defeat_flag':DEFEAT}
def sha(b):return hashlib.sha256(b).hexdigest()
def runtime_file(p,root):return p.is_file() and not any(x.startswith('.') for x in p.relative_to(root).parts)
def save(rel,b):
 p=MOD/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def binder_files(raw):
 assert raw[:4]==b'BND4' and struct.unpack_from('<Q',raw,32)[0]==36
 out=[]
 for i in range(struct.unpack_from('<I',raw,12)[0]):
  h=64+36*i;flag,unk,size,usize,off,rid,no=struct.unpack_from('<IIQQIII',raw,h);end=no
  while raw[end:end+2]!=b'\0\0':end+=2
  out.append({'flag':flag,'unk':unk,'id':rid,'name':raw[no:end].decode('utf-16le'),'data':raw[off:off+size],'usize':usize})
 return out

def path_hash(path):
 path=path.lower().replace('\\','/');path=path if path.startswith('/') else '/'+path;v=0
 for c in path:v=(v*37+ord(c))&0xffffffff
 return v

def binder_add(raw,additional):
 files=binder_files(raw);known={f['name'].split('\\')[-1] for f in files};nextid=max(f['id'] for f in files)+1
 for f in additional:
  assert f['name'].split('\\')[-1] not in known;f=copy.deepcopy(f);f['id']=nextid;nextid+=1;files.append(f)
 n=len(files);out=bytearray(raw[:64]);struct.pack_into('<I',out,12,n);out.extend(bytes(36*n));names=[]
 for f in files:names.append(len(out));out.extend((f['name']+'\0').encode('utf-16le'))
 if raw[50]==4:
  out.extend(bytes(-len(out)%8));ht=len(out);groups=max(n//7,2)
  while any(groups%i==0 for i in range(2,math.isqrt(groups)+1)):groups+=1
  buckets=[[] for _ in range(groups)]
  for i,f in enumerate(files):h=path_hash(f['name']);buckets[h%groups].append((h,i))
  for bucket in buckets:bucket.sort()
  out.extend(struct.pack('<qI4B',ht+16+groups*8,groups,16,8,8,0));idx=0
  for bucket in buckets:out.extend(struct.pack('<ii',len(bucket),idx));idx+=len(bucket)
  for bucket in buckets:
   for h,i in bucket:out.extend(struct.pack('<Ii',h,i))
  struct.pack_into('<q',out,56,ht)
 else:struct.pack_into('<q',out,56,0)
 struct.pack_into('<Q',out,40,len(out))
 for i,f in enumerate(files):
  out.extend(bytes(-len(out)%16));off=len(out);out.extend(f['data']);struct.pack_into('<IIQQIII',out,64+36*i,f['flag'],f['unk'],len(f['data']),f['usize'],off,f['id'],names[i])
 checked=binder_files(out);assert checked==files
 if raw[50]==4:
  hashes,gn=struct.unpack_from('<qI',out,ht);seen=set()
  for g in range(gn):
   length,index=struct.unpack_from('<ii',out,ht+16+g*8);last=-1
   for k in range(index,index+length):
    h,j=struct.unpack_from('<Ii',out,hashes+8*k);assert h==path_hash(files[j]['name']) and h%gn==g and h>=last;last=h;seen.add(j)
  assert seen==set(range(n))
 return bytes(out)

def params():
 template,raw=decrypt((BASE/'ModEngine/mod/regulation.bin').read_bytes());assert raw==(TASK/'base.bnd').read_bytes()
 ver,B=read_bnd(TASK/'base.bnd');dv,D=read_bnd(TASK/'donor.bnd')
 defs={ET.parse(p).getroot().findtext('ParamType'):p for p in (ROOT/'pd/ER/Defs').glob('*.xml')}
 fs={t:fields(defs[v['ptype']])[0] for t,v in D.items() if v['ptype'] in defs};fm={t:{f[0]:f for f in vv} for t,vv in fs.items()}
 def vals(t,b):return {f[0]:decode(b,f) for f in fs[t]}
 def put(t,b,key,value):
  _,typ,pos,size,bits,shift,n=fm[t][key]
  if bits:
   v=int.from_bytes(b[pos:pos+size],'little');mask=((1<<bits)-1)<<shift;b[pos:pos+size]=((v&~mask)|(int(value)<<shift)).to_bytes(size,'little')
  else:assert n==1 and typ in TYPES;struct.pack_into('<'+TYPES[typ][0],b,pos,value)
 selected=collections.defaultdict(set)
 for p in (DONOR/'[MERGE]').glob('*.csv'):
  selected[p.stem].update(int(r['ID']) for r in csv.DictReader(p.open(encoding='utf-8-sig')))
 for rid in [7520,7521,7530]:
  if rid in D.get('ChrModelParam',{}).get('rows',{}):selected['ChrModelParam'].add(rid)
 # TAE directly applies effects and emits behavior judges, in addition to CSV references.
 tae_audit={}
 for model in [7520,7530]:
  members=bnd_entries(unpack((DONOR/f'chr/c{model}.anibnd.dcx').read_bytes()));tae=next(b for k,(h,b) in members.items() if k.endswith('.tae'))
  n=struct.unpack_from('<i',tae,0x54)[0];ao=struct.unpack_from('<q',tae,0x58)[0];fx=set();judges=set();positions=[]
  for i in range(n):
   aid,ap=struct.unpack_from('<2q',tae,ao+16*i);eh,eg,to,af,ne,ng,nt,z=struct.unpack_from('<4q4i',tae,ap)
   for j in range(ne):
    st,en,ed=struct.unpack_from('<3q',tae,eh+24*j);typ=struct.unpack_from('<i',tae,ed)[0]
    if typ in [66,67,302,401]:rid=struct.unpack_from('<i',tae,ed+16)[0];fx.add(rid);positions.append((ed+16,rid))
    if typ in [1,2]:judges.add(struct.unpack_from('<i',tae,ed+24)[0])
    if typ in [5,304]:judges.add(struct.unpack_from('<i',tae,ed+20)[0])
  selected['SpEffectParam'].update(x for x in fx if x>0);tae_audit[model]={'animations':n,'effects':sorted(fx),'judges':sorted(judges),'positions':positions}
 def references(t,b):
  v=vals(t,b);out=[]
  def add(target,keys):
   for k in keys:
    val=v.get(k,-1)
    if isinstance(val,int) and val>0:out.append((target,val,k))
  if t=='NpcParam':add('SpEffectParam',[f'spEffectID{i}' for i in range(32)]+['GameClearSpEffectID']);add('LockCamParam',['lockCameraParamId'])
  if t=='NpcThinkParam':add('SpEffectParam',['spEffectId_RangedAttack','weaponOffSpecialEffectId','weaponOnSpecialEffectId'])
  if t=='AtkParam_Npc':add('SpEffectParam',[f'spEffectId{i}' for i in range(5)])
  if t=='Bullet':
   add('AtkParam_Npc',['atkId_Bullet']);add('Bullet',['HitBulletID','intervalCreateBulletId']);add('SpEffectParam',['spEffectIDForShooter']+[f'spEffectId{i}' for i in range(5)]);add('NpcThinkParam',['autoSearchNPCThinkID'])
  if t=='BehaviorParam':
   target={0:'AtkParam_Npc',1:'Bullet',2:'SpEffectParam'}.get(v['refType'])
   if target:add(target,['refId'])
  if t=='SpEffectParam':
   add('SpEffectParam',['replaceSpEffectId','cycleOccurrenceSpEffectId','atkOccurrenceSpEffectId','accumuOverFireId','accumuUnderFireId']);add('SpEffectVfxParam',['vfxId']+[f'vfxId{i}' for i in range(1,8)])
  return out
 queue=[(t,r) for t,ids in selected.items() for r in ids];seen=set();missing=[]
 while queue:
  t,r=queue.pop()
  if (t,r) in seen:continue
  seen.add((t,r))
  if r in B[t]['rows']:continue
  if r not in D[t]['rows']:missing.append((t,r));selected[t].discard(r);continue
  selected[t].add(r)
  if t in fs:queue.extend((target,rid) for target,rid,k in references(t,D[t]['rows'][r]['data']))
 additions={t:{r:D[t]['rows'][r]['data'] for r in ids-B[t]['rows'].keys()} for t,ids in selected.items()};additions={t:a for t,a in additions.items() if a}
 for t,a in additions.items():assert B[t]['row_size']==D[t]['row_size'],(t,B[t]['row_size'],D[t]['row_size'])
 originalhp={r:vals('NpcParam',D['NpcParam']['rows'][r]['data'])['hp'] for r in [75200000,75300000]};total=sum(originalhp.values());hp_moth=round(62500*originalhp[75200000]/total);hp={75200000:hp_moth,75300000:62500-hp_moth}
 npc_changes={}
 for rid in hp:
  b=bytearray(additions['NpcParam'][rid]);v=vals('NpcParam',b)
  for k,x in {'hp':hp[rid],'spEffectID15':8324901,'getSoul':240000 if rid==75200000 else 0,'itemLotId_enemy':vals('NpcParam',B['NpcParam']['rows'][47701001 if rid==75300000 else 46800032]['data'])['itemLotId_enemy']}.items():put('NpcParam',b,k,x)
  # Use exactly Caligo's regional scale (12x); remove broken donor 7760 reference.
  for k in [f'spEffectID{i}' for i in range(32)]:
   if v[k]==7080:put('NpcParam',b,k,7180)
   if v[k]==7760:put('NpcParam',b,k,-1)
  for k in ['neutralDamageCutRate','slashDamageCutRate','blowDamageCutRate','thrustDamageCutRate','magicDamageCutRate','thunderDamageCutRate','darkDamageCutRate']:put('NpcParam',b,k,v[k]*.7)
  for k in ['resist_poison','resist_desease','resist_blood','resist_curse','resist_freeze','resist_sleep','resist_madness']:put('NpcParam',b,k,math.ceil(v[k]*1.3))
  additions['NpcParam'][rid]=bytes(b);after=vals('NpcParam',b);npc_changes[rid]={k:[v[k],after[k]] for k in v if v[k]!=after[k]};assert after['fireDamageCutRate']==v['fireDamageCutRate'] and after['def_fire']==v['def_fire']
 # Match Caligo's final nominal damage chain: dedicated Atk base2x + same4x resident.
 attack_changes=[]
 for rid,rawrow in list(additions.get('AtkParam_Npc',{}).items()):
  b=bytearray(rawrow);v=vals('AtkParam_Npc',b);changes={}
  for k in ['atkPhys','atkMag','atkFire','atkThun','atkDark']:
   if v[k]>0:put('AtkParam_Npc',b,k,v[k]*2);changes[k]=[v[k],v[k]*2]
  additions['AtkParam_Npc'][rid]=bytes(b)
  if changes:attack_changes.append({'id':rid,'fields':changes})
 # Every status buildup uses the same2x rule; native shared effects are cloned.
 status_keys=[k for k in fm['SpEffectParam'] if k.endswith('AttackPower') and k.startswith(('poizon','poison','disease','blood','curse','freeze','sleep','madness'))]
 drain_keys=[k for k in fm['SpEffectParam'] if k.startswith('change') and k.endswith('ResistPoint')]
 touched_fx=set(additions.get('SpEffectParam',{}));direct_refs=[]
 for info in tae_audit.values():touched_fx.update(r for p,r in info['positions'])
 for t in ['AtkParam_Npc','Bullet','BehaviorParam','NpcParam']:
  for rid,b in additions.get(t,{}).items():
   direct_refs.extend((t,rid,k,r) for target,r,k in references(t,b) if target=='SpEffectParam');touched_fx.update(r for target,r,k in references(t,b) if target=='SpEffectParam')
 remap={};status_audit=[];nextfx=8327500
 for rid in sorted(touched_fx):
  source=additions.get('SpEffectParam',{}).get(rid,B['SpEffectParam']['rows'].get(rid,{}).get('data'))
  if source is None:continue
  v=vals('SpEffectParam',source);changes={k:v[k]*2 for k in status_keys if v[k]>0};changes.update({k:v[k]*2 for k in drain_keys if v[k]<0})
  if not changes:continue
  b=bytearray(source)
  for k,x in changes.items():put('SpEffectParam',b,k,x)
  if rid not in additions.get('SpEffectParam',{}):
   while nextfx in B['SpEffectParam']['rows'] or nextfx in additions.get('SpEffectParam',{}):nextfx+=1
   remap[rid]=nextfx;dest=nextfx;nextfx+=1
  else:dest=rid
  additions.setdefault('SpEffectParam',{})[dest]=bytes(b);status_audit.append({'source':rid,'dest':dest,'changes':{k:[v[k],x] for k,x in changes.items()}})
 for t,rid,k,r in direct_refs:
  if r in remap:
   b=bytearray(additions[t][rid]);put(t,b,k,remap[r]);additions[t][rid]=bytes(b)
 # Rewire cycles referencing private status clones, preserving all existing rows.
 for rid,row in list(additions.get('SpEffectParam',{}).items()):
  b=bytearray(row)
  for target,r,k in references('SpEffectParam',row):
   if target=='SpEffectParam' and r in remap:put('SpEffectParam',b,k,remap[r])
  additions['SpEffectParam'][rid]=bytes(b)
 # Direct TAE references to native status effects must follow those clones too.
 for model,info in tae_audit.items():
  positions=[(p,remap[r]) for p,r in info.pop('positions') if r in remap]
  if positions:
   path=f'chr/c{model}.anibnd.dcx';rawbnd=unpack((DONOR/path).read_bytes());members=bnd_entries(rawbnd);name=next(k for k in members if k.endswith('.tae'));b=bytearray(members[name][1])
   for p,r in positions:struct.pack_into('<i',b,p,r)
   save(path,dcx_pack(bnd_repack(rawbnd,{name:bytes(b)})))
   info['status_TAE_references_rewired']=positions
 # One remembrance bonus for the whole encounter.
 parent=bytearray(B['SpEffectParam']['rows'][7400201]['data']);put('SpEffectParam',parent,'cycleOccurrenceSpEffectId',CHILD)
 assert PARENT not in B['SpEffectParam']['rows'] and CHILD not in B['SpEffectParam']['rows'];additions['SpEffectParam'][PARENT]=bytes(parent);additions['SpEffectParam'][CHILD]=B['SpEffectParam']['rows'][7410201]['data']
 members=bnd_entries(raw);updates={t+'.param':param_patch(members[t+'.param'][1],{},a,B[t]['row_size']) for t,a in additions.items()};new=bnd_repack(raw,updates);reg=encrypt(template,new);assert decrypt(reg)[1]==new;save('regulation.bin',reg);(TASK/'merged.bnd').write_bytes(new)
 _,M=read_bnd(TASK/'merged.bnd');preserved=0
 for t,table in B.items():
  assert M[t]['rows'].keys()-table['rows'].keys()==set(additions.get(t,{}))
  for rid,row in table['rows'].items():assert M[t]['rows'][rid]['data']==row['data'],(t,rid);preserved+=1
 final_missing=[]
 for t,rows in additions.items():
  if t in fs:
   for rid,row in rows.items():
    for target,r,k in references(t,row):
     if r not in M[target]['rows']:final_missing.append((t,rid,k,target,r))
 AUDIT['params']={'preserved_existing_rows':preserved,'additions':{t:sorted(a) for t,a in additions.items()},'npc_changes':npc_changes,'nominal_single_NG0_HP':{rid:hp[rid]*12 for rid in hp},'total_HP':sum(hp.values())*12,'attack_rows':attack_changes,'damage_chain_nominal':8,'status_buildup':status_audit,'shared_status_clones':remap,'source_missing_before':sorted(set(missing)),'unresolved_final_refs':final_missing,'tae':tae_audit,'fire_weakness_preserved':True,'player_and_Caligo_rows_unchanged':True}
 return B,M

def mapedit():
 raw=(TASK/'target.msb').read_bytes();params=chunks(raw);orig=parse(raw);models=next(s for s in params if s['name']=='MODEL_PARAM_ST')['bodies'];parts=next(s for s in params if s['name']=='PARTS_PARAM_ST')['bodies']
 donor=chunks((TASK/'donor.msb').read_bytes());dm=next(s for s in donor if s['name']=='MODEL_PARAM_ST')['bodies'];dparts=json.loads((TASK/'donor_parts.json').read_text())
 cut=next(i for i,b in enumerate(models) if struct.unpack_from('<I',b,8)[0]!=0);typeid=max(struct.unpack_from('<I',b,12)[0] for b in models if struct.unpack_from('<I',b,8)[0]==0)+1;newmodels=[]
 def entryname(b):
  no=struct.unpack_from('<q',b)[0];end=no
  while b[end:end+2]!=b'\0\0':end+=2
  return bytes(b[no:end]).decode('utf-16le')
 for i,name in enumerate(['c7530','c7520']):
  b=bytearray(next(b for b in dm if entryname(b)==name));struct.pack_into('<I',b,12,typeid+i)
  struct.pack_into('<i',b,24,1);newmodels.append(b)
 # Model indices are shifted; part indices and all part references remain stable.
 for b in parts:
  idx=struct.unpack_from('<i',b,20)[0]
  if idx>=cut:struct.pack_into('<i',b,20,idx+2)
 oldmodelids=[struct.unpack_from('<i',parts[next(p['i'] for p in orig if p['entity']==eid)],20)[0] for eid in [FAURTIS,MOTH]]
 models[cut:cut]=newmodels
 f=next(p for p in orig if p['entity']==MOTH);floor=f['pos'];dF=next(p for p in dparts if p['entity']==39200800);dM=next(p for p in dparts if p['entity']==39200801);mpos=[floor[i]+dM['pos'][i]-dF['pos'][i] for i in range(3)]
 regs=next(s for s in params if s['name']=='POINT_PARAM_ST')['bodies'];entrance=next(b for b in regs if struct.unpack_from('<I',b,struct.unpack_from('<q',b,80)[0]+4)[0]==12022801);ep=struct.unpack_from('<3f',entrance,20);yaw=math.degrees(math.atan2(floor[0]-ep[0],floor[2]-ep[2]))
 edits=[]
 for j,(eid,npc,pos,name) in enumerate([(FAURTIS,75300000,floor,'c7530_9000'),(MOTH,75200000,mpos,'c7520_9001')]):
  p=next(p for p in orig if p['entity']==eid);b=parts[p['i']];struct.pack_into('<i',b,20,cut+j);struct.pack_into('<3f',b,32,*pos);struct.pack_into('<3f',b,44,0,yaw,0);struct.pack_into('<I',b,68,0)
  td=struct.unpack_from('<q',b,104)[0];struct.pack_into('<ii',b,td+8,npc,npc)
  no=struct.unpack_from('<q',b)[0];old=entryname(b);assert len(name)==len(old);b[no:no+len(name)*2]=(name).encode('utf-16le');edits.append({'entity':eid,'name':name,'npc':npc,'pos':pos,'yaw':yaw,'collision_reference':struct.unpack_from('<i',b,td+28)[0]})
  if eid==FAURTIS:
   # Use the known arena-floor collision used by the second native actor.
   struct.pack_into('<i',b,td+28,struct.unpack_from('<i',parts[f['i']],struct.unpack_from('<q',parts[f['i']],104)[0]+28)[0])
 for idx in set(oldmodelids):struct.pack_into('<i',models[idx],24,max(0,struct.unpack_from('<i',models[idx],24)[0]-oldmodelids.count(idx)))
 out=rebuild(raw[:16],params);after=parse(out);assert len(after)==len(orig)
 for a,b in zip(orig,after):
  if a['entity'] not in [FAURTIS,MOTH]:
   for k in ['entity','name','model','pos','rot','instance','game_disable','tile']:assert a[k]==b[k],(a['name'],k)
 assert [(s,i,p,v) for s,i,_,p,v in refs(chunks(raw)) if s!='PARTS_PARAM_ST' or i not in [447,448]]==[(s,i,p,v) for s,i,_,p,v in refs(chunks(out)) if s!='PARTS_PARAM_ST' or i not in [447,448]]
 # No replacement of coffins, assets, regions, summon signs, collisions or ladders.
 for section in ['POINT_PARAM_ST','EVENT_PARAM_ST']:
  assert next(s for s in chunks(raw) if s['name']==section)['bodies']==next(s for s in chunks(out) if s['name']==section)['bodies']
 save('map/MapStudio/m12_02_00_00.msb.dcx',dcx_pack(out));assert dcx_unpack((MOD/'map/MapStudio/m12_02_00_00.msb.dcx').read_bytes())==out
 AUDIT['map']={'parts_count':len(orig),'part_indices_unchanged':True,'model_entries_added':['c7530','c7520'],'actors':edits,'coffin_assets_collision_regions_unchanged':True,'spawn_floor_source':'existing second arena actor; actual landing requires game verification'}

def remap_instruction(ins,emap,fmap,evidmap):
 b,i,args,layer=ins;out=bytearray(args);p=0
 for a in SPEC[b,i]['args']:
  fmt=FMT[a['type']];size=struct.calcsize(fmt);p+=-p%size;v=struct.unpack_from('<'+fmt,args,p)[0];name=a['name']
  new=v
  if a['type'] in [2,5,8]:
   if 'Flag ID' in name:new=fmap.get(v,v)
   elif name=='Event ID':new=evidmap.get(v,v)
   elif 'Entity ID' in name:new=emap.get(v,v)
  if new!=v:struct.pack_into('<'+fmt,out,p,new)
  p+=size
 return b,i,bytes(out),layer

def events():
 target=Emevd(unpack((BASE/'ModEngine/mod/event/m12_02_00_00.emevd.dcx').read_bytes()));before=copy.deepcopy(target.events);donor=Emevd(unpack((DONOR/'event/m39_20_00_00.emevd.dcx').read_bytes()))
 byid={e['id']:e for e in target.events};db={e['id']:e for e in donor.events};phaseids=list(range(39203721,39203739))+[39203740,39203741,39203742]
 newids={rid:12023800+(rid-39203700) for rid in phaseids};assert not set(newids.values())&set(byid)
 emap={39200800:FAURTIS,39200801:MOTH,39202801:12022801};fmap={39200800:DEFEAT,39200801:FIRST,39200803:12020903,39202805:12022805}
 newevents=[]
 for rid in phaseids:
  e=copy.deepcopy(db[rid]);e['id']=newids[rid];e['ins']=[remap_instruction(ins,emap,fmap,newids) for ins in e['ins']]
  if rid==39203721:e['ins']=[ins for ins in e['ins'] if not any(v==39200804 for name,v in decode_args(ins))]
  assert not e['params'];newevents.append(e)
 # Donor entrance retained; native already-cleared flag cannot skip the new boss.
 entrance=copy.deepcopy(db[39202810]);entrance['id']=12022810;entrance['ins']=[remap_instruction(ins,emap,fmap,newids) for ins in entrance['ins']]
 # Restore full HP before the visible battle after original entrance settles.
 idx=next(i for i,ins in enumerate(entrance['ins']) if ins[:2]==(2003,11))
 entrance['ins'][idx:idx]=[I(2004,8,FAURTIS,8324900),I(2004,8,MOTH,8324900),I(1001,1,1)]
 # Native floor actor uses gravity; moth disabled until original80% animation signal.
 byid[12022810].update(entrance)
 # Victory keeps native passage / trophy flags; separate new flag avoids old-credit.
 ins=[I(1003,2,0,1,0,DEFEAT),I(4,14,0,MOTH,5,0,0,1.),I(2004,4,FAURTIS,0),I(1001,0,4.),I(2003,11,0,FAURTIS,0,904910001),I(2003,11,0,MOTH,0,904910002),I(2003,11,0,MOTH,1,904910002),I(2010,2,FAURTIS,5,888880000),I(2008,1,0,0),I(2003,12,FAURTIS,17),I(2003,66,0,DEFEAT,1),I(2003,66,0,12020800,1),I(2003,66,0,9110,1),I(1003,12,1,1),I(2003,66,0,61110,1)]
 byid[12022800]['ins']=ins
 # Original dual-gargoyle reinforcement scripts must never activate against bugs.
 removed_calls=[];constructor=byid[0]
 keep=[]
 for inst in constructor['ins']:
  if inst[:2]==(2000,0) and struct.unpack_from('<I',inst[2],4)[0] in [12022820,12022821,12022851]:removed_calls.append(struct.unpack_from('<I',inst[2],4)[0]);continue
  # Boss-grace activation only: change its first deficit flag, no unrelated bonfire.
  if inst[:2]==(2000,6) and len(inst[2])>=12 and struct.unpack_from('<II',inst[2],4)==(9005810,12020800):
   b=bytearray(inst[2]);struct.pack_into('<I',b,8,DEFEAT);inst=inst[0],inst[1],bytes(b),inst[3]
  keep.append(inst)
 constructor['ins']=keep
 constructor['ins'] += [I(2000,0,0,newids[rid],0) for rid in [39203721,39203722,39203723,39203740,39203741,39203742]]
 # Preserve native entrance fog and return side fog; one native music handler.
 fog=byid[12022849];fi=[];music=0
 for inst in fog['ins']:
  assert inst[:2]==(2000,6);b=bytearray(inst[2]);func=struct.unpack_from('<I',b,4)[0];assert struct.unpack_from('<I',b,8)[0]==12020800;struct.pack_into('<I',b,8,DEFEAT)
  if func==9005822:
   music+=1
   if music>1:continue
   for off in range(12,len(b),4):
    if struct.unpack_from('<I',b,off)[0]==12022820:struct.pack_into('<I',b,off,12020903)
  if func in [9005800,9005811]:
   for off in range(12,len(b),4):
    if struct.unpack_from('<I',b,off)[0]==12020801:struct.pack_into('<I',b,off,FIRST)
  fi.append((inst[0],inst[1],bytes(b),inst[3]))
 fog['ins']=fi;target.events+=newevents
 changed={0,12022800,12022810,12022849}
 for old in before:
  if old['id'] not in changed:assert byid[old['id']]==old
 blob=dcx_pack(target.write());assert Emevd(dcx_unpack(blob)).events==target.events;save('event/m12_02_00_00.emevd.dcx',blob)
 # Ensure all donor entity/flag/event dependencies were retargeted; no Makar writes.
 for e in newevents+[entrance]:
  for inst in e['ins']:
   for name,v in decode_args(inst):assert not(isinstance(v,int) and 39200000<=v<39210000),(e['id'],name,v)
 # Heart refresh: one new remembrance and suppress the old minor when new clear.
 common=Emevd(unpack((BASE/'ModEngine/mod/event/common.emevd.dcx').read_bytes()));old=copy.deepcopy(common.events);refresh=next(e for e in common.events if e['id']==20007902)
 reward=[I(2004,21,10000,PARENT),I(2004,21,10000,CHILD),I(1003,1,2,0,0,DEFEAT),I(2004,8,10000,PARENT),I(2004,8,10000,CHILD)]
 original=refresh['ins'];prefix=original[:72];body=copy.deepcopy(original[72:]);native_skip=I(1003,1,15,0,0,12020800);matches=[i for i,x in enumerate(body) if x==native_skip];assert len(matches)==1;pos=matches[0];body[pos:pos]=[I(1003,1,16,1,0,DEFEAT)];refresh['ins']=prefix+reward+body
 for a,b in zip(old,common.events):
  if a['id']!=20007902:assert a==b
 newcommon=dcx_pack(common.write());assert Emevd(dcx_unpack(newcommon)).events==common.events;save('event/common.emevd.dcx',newcommon)
 tests=[]
 for label,flags,n,new in [('none',set(),0,False),('old gargoyle',{12020800},1,False),('bugs only',{DEFEAT},0,True),('bugs native flags',{DEFEAT,12020800},0,True),('Caligo',{1054560804,1254560800},0,False),('both NR',{DEFEAT,12020800,1054560804,1254560800},0,True)]:
  count,fx=simulate_tail(reward+body,flags,I);assert count==n and (PARENT in fx)==new and (CHILD in fx)==new,(label,count,fx)
  assert (7400201 in fx)==(1054560804 in flags);tests.append(label)
 AUDIT['events']={'changed_native_ids':sorted(changed),'new_phase_ids':list(newids.values()),'removed_native_reinforcement_calls':removed_calls,'independent_defeat':DEFEAT,'first_encounter':FIRST,'native_passage_defeat':12020800,'original_trophy':9110,'CMI_global_music_events_not_imported':True,'native_arena_music':931000,'heart_refresh_prefix72_preserved':True,'single_remembrance_reward_effects':[PARENT,CHILD],'reward_tests':tests,'old_gargoyle_credit_suppressed_only_after_new_defeat':True,'original_Makar_map_event_untouched':True}

def shared_assets():
 # Only these runtime resource types; no donor regulation, map, message or globals overwrite.
 copied=[]
 for folder in ['chr','action','script','sfx','sd']:
  for p in (DONOR/folder).rglob('*'):
   if not p.is_file() or p.name=='aicommon.luabnd.dcx':continue
   rel=str(p.relative_to(DONOR))
   if not (MOD/rel).exists():save(rel,p.read_bytes())
   copied.append(rel)
 # Add the four GOAL definitions to current goal_list, not donor common scripts.
 path='script/aicommon.luabnd.dcx';raw=unpack((BASE/'ModEngine/mod'/path).read_bytes());e=bnd_entries(raw);goal=e['goal_list.lua'][1];lines=(DONOR/'[MERGE]/readme.txt').read_text().splitlines();assign=[l for l in lines if l.startswith('GOAL_')];assert len(assign)==4
 for line in assign:assert line.split('=')[0].strip().encode() not in goal
 newgoal=goal+b'\n'+('\n'.join(assign)+'\n').encode();LuaRuntime().compile(newgoal.decode());new=bnd_patch(raw,{'goal_list.lua':newgoal});saved=bnd_entries(new)
 for k,(h,b) in e.items():assert saved[k][1]==(newgoal if k=='goal_list.lua' else b)
 save(path,dcx_pack(new))
 for fn in ['752000_battle.lua','753000_battle.lua']:LuaRuntime().compile((TASK/'ai'/fn).read_text())
 # Five new moth materials only. Caligo's existing materials stay byte-for-byte.
 bm=(TASK/'base_material.bnd').read_bytes();dm=(TASK/'donor_material.bnd').read_bytes();B=bnd_entries(bm);D=bnd_entries(dm);newnames=D.keys()-B.keys();assert len(newnames)==5 and all('c7520' in k for k in newnames)
 files=[f for f in binder_files(dm) if f['name'].split('\\')[-1] in newnames];merged=binder_add(bm,files);M=bnd_entries(merged)
 for k,(h,b) in B.items():assert M[k][1]==b
 save('material/allmaterial.matbinbnd.dcx',dcx_pack(merged))
 # Only the two boss names. Original location/loot/heart descriptions stay.
 rel='msg/engus/item_dlc02.msgbnd.dcx';raw=unpack((BASE/'ModEngine/mod'/rel).read_bytes());members=bnd_entries(raw);fname=next(k for k in members if k.startswith('NpcName'))
 names=fmg_read(members[fname][1]);before=copy.deepcopy(names);names.update({904910001:'Faurtis Stoneshield',904910002:'Gnoster, The Sentient Pest'});new=bnd_repack(raw,{fname:fmg_write(names)});checked=fmg_read(bnd_entries(new)[fname][1]);assert checked==names
 for k,v in before.items():
  if k not in [904910001,904910002]:assert checked[k]==v
 for k,(h,b) in members.items():
  if k!=fname:assert bnd_entries(new)[k][1]==b
 save(rel,dcx_pack(new))
 AUDIT['assets']={'dedicated_paths':copied,'aicommon_changed_member_only':'goal_list.lua','new_goals':assign,'all_other_common_AI_members_preserved':True,'material_members_added':sorted(newnames),'all_existing_material_members_preserved':True,'names':{904910001:'Faurtis Stoneshield',904910002:'Gnoster, The Sentient Pest'},'skeleton_DLL_optional_not_loaded':'author optional size helper; current prototype uses native character size','donor_shared_aicommon_material_message_never_overwritten':True}

def package():
 doc=OUT/'Gnoster_Test';doc.mkdir(exist_ok=True)
 (doc/'audit.json').write_text(json.dumps(AUDIT,ensure_ascii=False,indent=2))
 (doc/'build_gnoster.py').write_bytes(Path(__file__).read_bytes());(doc/'event_inspect.py').write_bytes((TASK/'event_inspect.py').read_bytes())
 (doc/'verify_gnoster.py').write_bytes((TASK/'verify_gnoster.py').read_bytes())
 (doc/'CREDITS.txt').write_text('Gnoster/Faurtis: Lwingr, Gnoster - The Sentient Pest - Overhaul1.2.5, https://www.nexusmods.com/eldenring/mods/8406 . Author permissions allow credited modification and asset reuse. All original credits apply: Vawser, Ivi, Meowmaritus, Katalash, AinTunez, TechieW, Dasaav, Forsakensilver, WindShadowRuins, Shiki.\nCaligo: DDMMDD09 Nexus8583; HP clamp: NymicRazor/Named-Blade Nexus5732; six talismans: imCioco Nexus10481.\n')
 profile=(BASE/'ModEngine/evernight_v0116.me3').read_text().replace('evernight_v0116','evernight_gnoster_t1');(OUT/'ModEngine/evernight_gnoster_t1.me3').write_text(profile);(OUT/'ModEngine/evernight_v0116.me3').unlink(missing_ok=True)
 originalcheck=OUT/'ModEngine/check_v0116.ps1';originalcheck.unlink(missing_ok=True)
 hashes={str(p.relative_to(OUT/'ModEngine')).replace('/','\\'):sha(p.read_bytes()) for p in (OUT/'ModEngine').rglob('*') if runtime_file(p,OUT/'ModEngine') and p.suffix not in ['.ps1','.bat']}
 ps="$ErrorActionPreference='Stop'\n$checks=@{\n"+''.join(" '"+k+"'='"+h+"'\n" for k,h in sorted(hashes.items()))+"}\nforeach($rel in $checks.Keys){\n $p=Join-Path $PSScriptRoot $rel\n if(-not(Test-Path -LiteralPath $p -PathType Leaf)){throw \"Missing file: $rel\"}\n if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $checks[$rel]){throw \"File mismatch: $rel. Extract the complete Gnoster T1 package to a clean folder.\"}\n}\nWrite-Host 'Gnoster T1 complete runtime verified.'\n"
 (OUT/'ModEngine/check_gnoster_t1.ps1').write_text(ps,encoding='utf-8-sig')
 bat=(BASE/'ModEngine/launchmod_eldenring.bat').read_text().replace('check_v0116','check_gnoster_t1').replace('evernight_v0116.me3','evernight_gnoster_t1.me3').replace('v0.10.16','Gnoster T1');(OUT/'ModEngine/launchmod_eldenring.bat').write_bytes(bat.replace('\r\n','\n').replace('\n','\r\n').encode())
 guide='''Elden Ring: Evernight Reforged — Gnoster/Faurtis T1完整内测包

包含v0.10.16全部核心与Caligo，再新增地下希芙拉导水桥双石像鬼场地双虫。
完整解压到新目录，运行ModEngine/launchmod_eldenring.bat；单mod目录/单regulation/单入口，保留六护符与HP模块。HP日志仍须APPLIED/ALREADY_APPLIED。
双虫合计名义单周目750000，按原作者基础血量比例分配：Gnoster约292680、Faurtis约457320。周目/联机另外缩放。非火承伤×0.7、异常抗性阈值×1.3，火弱点保持；专属Atk×2+Caligo同一4x居民增益，名义8倍链；原有异常积累×2，无新异常/爆发伤害。
双虫四阶段原AI保留：Faurtis80%召唤Gnoster；实际作者事件55%开始爆头/准备骑乘；Faurtis10%终招退场；最后Gnoster单独战斗。并未改成Caligo的60%阶段。早杀Gnoster结束整场的作者设计保留。
独立击敗旗标不重置旧存档：已击败旧双石像鬼仍可在地图重新载入后挑战新双虫。新双虫已击败不会再生。旧已通棺材保持可用；新存档打赢双虫设原通路旗标，解锁深根棺材。
保留原双石像鬼地图资产/碰撞/棺材/区域和原奖励掉落引用；整场成长按一份追忆Boss档，在击败后手动使用Empowered Soul刷新：HP+5%、武器攻击+2.5%、法术祷告+2.5%，模板既有物理类型额外层保持。不会再叠旧双石像鬼小Boss成长。未制造新追忆兑换物。
英文游戏中名称已添加。原中文档案仍未取得；本版沿用当前英文文本工作方式。
声音使用作者c7520/c7530音效银行，战斗背景沿用该场地原配乐；未引入可选CMI。作者可选ERSkeletonMan缩放DLL不默认加载，Faurtis使用原尺寸，需测试相机。

检查：入场/死亡/赐福重试/旧已通关存档；两只满红与总HP/阶段衔接/骑乘碰撞/终招/Gnoster单独阶段；命中伤害/毒等异常/音效；提前击杀Gnoster；棺材通路；奖励与心脏重复刷新；Caligo与六护符回归。
静态回读/参数隔离/共享AI与材质逐成员保持/地图引用/奖励模拟/启动哈希通过，未运行Windows游戏。作者包自身存在47处参数引用缺口以及部分TAE控制效果缺口，主要涉及46000/46001/46004/46006等未提供的异常效果，另有攻击/弹丸/VFX缺行；现有20004/20005毒积累已私有克隆翻倍，但不能宣称所有毒攻击已有效。未凭空补造或静默删除缺行，具体在audit列出。此版是资源与数值内测候选，不是游戏验收。关闭光追沿用作者提示。
'''
 hp=AUDIT['params']['nominal_single_NG0_HP'];guide=guide.replace('292680',str(hp[75200000])).replace('457320',str(hp[75300000]));(OUT/'README.txt').write_text(guide,encoding='utf-8-sig')
 manifest={str(p.relative_to(OUT)):sha(p.read_bytes()) for p in OUT.rglob('*') if runtime_file(p,OUT) and p.name!='manifest.json'};(doc/'manifest.json').write_text(json.dumps(manifest,indent=2))
 output=TASK/'Evernight_Reforged_Gnoster_T1_Full_Test.zip'
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(OUT.rglob('*')):
   if runtime_file(p,OUT):z.write(p,'Evernight_Reforged_Gnoster_T1/'+str(p.relative_to(OUT)))
 with zipfile.ZipFile(output) as z:
  assert z.testzip() is None
  for k,h in manifest.items():assert sha(z.read('Evernight_Reforged_Gnoster_T1/'+k))==h
 before={str(p.relative_to(BASE)):sha(p.read_bytes()) for p in BASE.rglob('*') if runtime_file(p,BASE)};changed=[k for k,h in before.items() if k in manifest and manifest[k]!=h];unchanged=[k for k,h in before.items() if manifest.get(k)==h];summary={'zip':str(output),'size':output.stat().st_size,'sha256':sha(output.read_bytes()),'changed_existing_files':changed,'unchanged_existing_files':len(unchanged),'new_files':sorted(set(manifest)-set(before)),'game_test':'NOT RUN'};(TASK/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))

def main():
 assert sha((TASK/'baseline_v0116.zip').read_bytes())=='fa1454c9001a26028ef96f03d4a5c13f501da4684f880511722f4228bd180294'
 assert not OUT.exists();shutil.copytree(BASE,OUT)
 params();mapedit();events();shared_assets();package()
 subprocess.run([sys.executable,str(TASK/'verify_gnoster.py')],check=True)
if __name__=='__main__':main()
