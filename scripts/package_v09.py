"""Create complete v0.9 package from the verified v0.8 installation."""
from pathlib import Path
import copy,hashlib,zipfile,zlib,struct
from build_v05_messages import parse_fmg
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'output/Ascended_Balance_v0.8_Test.zip'
REG=ROOT/'output/v09_regulation.bin'
DOC=ROOT/'docs/v0.9.md'
TEXT=ROOT/'output/v09_text'
OUT=ROOT/'output/Ascended_Balance_v0.9_Test.zip'
P='Elden_Ascended_Mod_Age of the Endless Mod/'
REGS={P+'regulation.bin',P+'ModEngine/mod/regulation.bin'}
MSGS={P+'ModEngine/mod/msg/engus/'+v+'.msgbnd.dcx':TEXT/(v+'.msgbnd.dcx') for v in ('item_dlc01','item_dlc02')}

def main():
 assert all(x.exists() for x in (BASE,REG,DOC,*MSGS.values()))
 with zipfile.ZipFile(BASE) as src,zipfile.ZipFile(OUT,'w') as dest:
  assert src.testzip() is None and REGS|MSGS.keys()<=set(src.namelist())
  for info in src.infolist():
   if info.filename.endswith('Ascended_v0.8_安装与测试说明.md'):continue
   data=REG.read_bytes() if info.filename in REGS else MSGS[info.filename].read_bytes() if info.filename in MSGS else src.read(info)
   dest.writestr(copy.copy(info),data)
  dest.write(DOC,P+'Ascended_v0.9_安装与测试说明.md')
  for filename in ('v0.9_talismans.csv','v0.9_description_changes.csv','v0.9_bow_audit.csv'):
   dest.write(ROOT/'changes'/filename,P+'审查清单/'+filename)
 with zipfile.ZipFile(OUT) as check:
  assert check.testzip() is None and len(check.namelist())==1216
  assert all(check.read(x)==REG.read_bytes() for x in REGS)
  assert all(check.read(dst)==src.read_bytes() for dst,src in MSGS.items())
 print(OUT,OUT.stat().st_size,hashlib.sha256(OUT.read_bytes()).hexdigest())
if __name__=='__main__':main()
