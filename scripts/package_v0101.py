"""Package only the starter heart and English name correction on top of v0.10."""
from pathlib import Path
import copy
import hashlib
import zipfile

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'output/Ascended_Balance_v0.10_Integrated_Test.zip'
OUT=ROOT/'output/Ascended_Balance_v0.10.1_Starter_Heart_Test.zip'
P='Elden_Ascended_Mod_Age of the Endless Mod/'
REG=ROOT/'output/v0101_starter_heart_regulation.bin'
TEXT=ROOT/'output/pending_remembrance_text'
REPLACE={P+'regulation.bin':REG,P+'ModEngine/mod/regulation.bin':REG}
for s in ('item_dlc01','item_dlc02'):
 REPLACE[P+f'ModEngine/mod/msg/engus/{s}.msgbnd.dcx']=TEXT/(s+'.msgbnd.dcx')
DOC=P+'Ascended_v0.10.1_开局心脏测试说明.md'
CSV=P+'审查清单/v0.10.1_starter_heart.csv'

def main():
 with zipfile.ZipFile(BASE) as before,zipfile.ZipFile(OUT,'w') as after:
  assert before.testzip() is None
  assert set(REPLACE)<=set(before.namelist())
  for item in before.infolist():
   after.writestr(copy.copy(item),REPLACE[item.filename].read_bytes()
                  if item.filename in REPLACE else before.read(item))
  after.write(ROOT/'docs/v0.10.1.md',DOC)
  after.write(ROOT/'changes/v0.10.1_starter_heart.csv',CSV)
 with zipfile.ZipFile(OUT) as check,zipfile.ZipFile(BASE) as before:
  assert check.testzip() is None
  assert set(check.namelist())==set(before.namelist())|{DOC,CSV}
  for name,path in REPLACE.items():assert check.read(name)==path.read_bytes()
  for name in before.namelist():
   if name not in REPLACE:assert check.read(name)==before.read(name),name
 print(OUT,OUT.stat().st_size,hashlib.sha256(OUT.read_bytes()).hexdigest())

if __name__=='__main__':main()
