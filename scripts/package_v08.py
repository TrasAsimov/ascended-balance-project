"""Make a full v0.8 package with official animations for two affected models."""
from pathlib import Path
import copy,hashlib,zipfile
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'output/Ascended_Balance_v0.7_Test.zip'
VAN=ROOT.parent/'vanilla_chr/Ascended_vanilla_chr_01.zip'
REG=ROOT/'output/v08_regulation.bin'
NOTES=ROOT/'docs/v0.8.md'
OUT=ROOT/'output/Ascended_Balance_v0.8_Test.zip'
P='Elden_Ascended_Mod_Age of the Endless Mod/'
REGS={P+'regulation.bin',P+'ModEngine/mod/regulation.bin'}
ANIMS={P+'ModEngine/mod/chr/'+model+'.anibnd.dcx':'chr/'+model+'.anibnd.dcx' for model in ('c3010','c4820')}

def main():
 assert all(x.exists() for x in (BASE,VAN,REG,NOTES))
 with zipfile.ZipFile(BASE) as src,zipfile.ZipFile(VAN) as official,zipfile.ZipFile(OUT,'w') as dest:
  assert src.testzip() is None and official.testzip() is None
  assert REGS|ANIMS.keys()<=set(src.namelist())
  for info in src.infolist():
   if info.filename.endswith('Ascended_v0.7_安装与测试说明.md'):continue
   data=REG.read_bytes() if info.filename in REGS else official.read(ANIMS[info.filename]) if info.filename in ANIMS else src.read(info)
   dest.writestr(copy.copy(info),data)
  dest.write(NOTES,P+'Ascended_v0.8_安装与测试说明.md')
  for name in ('v0.8_enemy_audit.csv','v0.8_changes.csv'):
   dest.write(ROOT/'changes'/name,P+'审查清单/'+name)
 with zipfile.ZipFile(OUT) as check,zipfile.ZipFile(VAN) as official:
  assert check.testzip() is None
  assert all(check.read(x)==REG.read_bytes() for x in REGS)
  assert all(check.read(dst)==official.read(src) for dst,src in ANIMS.items())
  assert len(check.namelist())==1213
 print(OUT,OUT.stat().st_size,hashlib.sha256(OUT.read_bytes()).hexdigest())
if __name__=='__main__':main()
