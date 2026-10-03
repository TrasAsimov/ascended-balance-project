from pathlib import Path
import sys,struct,json
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'repo/systems/armor/scripts'),str(R/'bridge_hotfix'),str(R/'work')]
from formats import Emevd
from inspect_maps import unpack
DOC=json.load(open(R/'ds/DarkScript3/Resources/er-common.emedf.json'));SPEC={(b['index'],i['index']):i for b in DOC['main_classes'] for i in b['instrs']};FMT={0:'B',1:'H',2:'I',3:'b',4:'h',5:'i',6:'f',8:'I'}
def decode_args(ins):
 b,i,a,l=ins;p=0;v=[]
 for f in SPEC[b,i]['args']:
  fmt=FMT[f['type']];size=struct.calcsize(fmt);p+=-p%size
  v.append((f['name'],struct.unpack_from('<'+fmt,a,p)[0]));p+=size
 return v
if __name__=='__main__':
 base=R/'gnoster/baseline/Ascended_Balance_v0.10.16/ModEngine/mod'
 e=Emevd(unpack((base/'event/m12_02_00_00.emevd.dcx').read_bytes()))
 for v in e.events:
  if 12022800<=v['id']<=12022899 or v['id'] in [12022710,12022711]:
   print('EVENT',v['id'],'params',v['params'])
   for ins in v['ins']:print(SPEC[ins[:2]]['name'],decode_args(ins))
