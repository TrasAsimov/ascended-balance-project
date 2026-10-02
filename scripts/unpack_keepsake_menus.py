"""Extract current English menus for update_starting_keepsakes.py.

Requires unoodle from oozextract, validated revision
5ff5dc14be82160ab2c605dd844a46ba46e52d43. The runtime uses independently
restarted 256 KiB Kraken blocks; decode each at history offset zero.
Do not distribute the temporary extracted game archives in source Git.
"""
import argparse,struct,sys,zipfile,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from formats import bnd_entries,dcx_unpack
from fmg import fmg_read

def unpack_menu(blob,unoodle):
 if blob[:4]==b'BND4':return blob
 if blob[40:44]==b'DFLT':return dcx_unpack(blob)
 assert blob[:4]==b'DCX\0' and blob[40:44]==b'KRAK'
 size,compressed=struct.unpack_from('>II',blob,28);source=blob[76:76+compressed];pos=0;out=bytearray()
 while len(out)<size:
  assert source[pos:pos+2]==b'\x8c\x06','Expected independently restarted Kraken block without checksum'
  quantum=int.from_bytes(source[pos+2:pos+5],'big');assert quantum&0x3ffff!=0x3ffff
  end=pos+5+(quantum&0x3ffff)+1;assert end<=len(source)
  with tempfile.TemporaryDirectory() as folder:
   src=Path(folder)/'block.kraken';dst=Path(folder)/'block.raw';src.write_bytes(source[pos:end])
   count=min(0x40000,size-len(out))
   subprocess.run([str(unoodle.resolve()),str(src),'--length',str(count),'--output',str(dst)],check=True,capture_output=True)
   decoded=dst.read_bytes();assert len(decoded)==count;out.extend(decoded)
  pos=end
 assert pos==compressed and len(out)==size
 raw=bytes(out)
 for _,body in bnd_entries(raw).values():fmg_read(body)
 return raw

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-zip',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--unoodle',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=True,parents=True)
 with zipfile.ZipFile(a.base_zip) as z:
  for name in ['menu','menu_dlc01','menu_dlc02']:
   path=next(n for n in z.namelist() if n.endswith('/msg/engus/'+name+'.msgbnd.dcx'))
   raw=unpack_menu(z.read(path),a.unoodle);(a.output/(name+'.msgbnd.dcx.bnd')).write_bytes(raw);print(name,len(raw))
if __name__=='__main__':main()
