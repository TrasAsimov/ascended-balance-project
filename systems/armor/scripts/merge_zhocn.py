"""Append armor descriptions to matching owned zhocn BND4 text archives."""
from pathlib import Path
import argparse,json,struct,ctypes,re
from formats import bnd_entries,bnd_patch,dcx_pack,dcx_unpack
from fmg import fmg_read,fmg_write
MARK='【护甲单件与套装效果】'
def unpack(blob,oodle):
    if blob[:4]!=b'DCX\0' or blob[40:44]==b'DFLT':return dcx_unpack(blob)
    if blob[40:44]!=b'KRAK':raise ValueError('Unsupported DCX compression')
    if not oodle:raise ValueError('KRAK 输入需提供自己游戏的 Oodle DLL，或先用自己的解包工具解压为 BND4')
    size,n=struct.unpack_from('>II',blob,28);src=ctypes.create_string_buffer(blob[76:76+n]);dst=ctypes.create_string_buffer(size)
    dll=ctypes.CDLL(str(oodle));f=dll.OodleLZ_Decompress
    f.restype=ctypes.c_ssize_t
    f.argtypes=[ctypes.c_void_p,ctypes.c_ssize_t,ctypes.c_void_p,ctypes.c_ssize_t,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_void_p,ctypes.c_ssize_t,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ssize_t,ctypes.c_int]
    if f(src,n,dst,size,1,0,0,None,0,None,None,None,0,3)!=size:raise ValueError('Oodle 解压失败')
    return dst.raw

def patch(raw,texts):
    parts=bnd_entries(raw);updates={};seen=set()
    for name,(_,body) in parts.items():
        if not name.startswith('ProtectorCaption'):continue
        ids=fmg_read(parts['ProtectorName'+name[len('ProtectorCaption'):]][1]);entries=fmg_read(body)
        for rid in ids:
            if str(rid) not in texts:continue
            entries[rid]=texts[str(rid)];seen.add(rid)
        updates[name]=fmg_write(entries)
    result=bnd_patch(raw,updates);check=bnd_entries(result)
    assert all(check[n][1]==v[1] for n,v in parts.items() if n not in updates)
    return dcx_pack(result),seen

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True,help='原文包所在目录（item_dlc01/02.msgbnd.dcx 或 .msgbnd）')
    p.add_argument('--output',type=Path,required=True,help='新目录；不能覆盖输入')
    p.add_argument('--oodle',type=Path,help='64 位 Windows 游戏目录内的 oo2core_*_win64.dll')
    p.add_argument('--descriptions',type=Path,default=Path(__file__).resolve().parent.parent/'data/description_zh.json')
    a=p.parse_args();texts=json.loads(a.descriptions.read_text(encoding='utf-8'))
    if a.input.resolve()==a.output.resolve():p.error('输出必须与输入分开')
    staged=[];allseen=set()
    for name in ['item_dlc01','item_dlc02']:
        source=a.input/(name+'.msgbnd.dcx')
        if not source.exists():source=a.input/(name+'.msgbnd')
        packed,seen=patch(unpack(source.read_bytes(),a.oodle),texts);staged.append((name,packed));allseen|=seen
    missing=set(map(int,texts))-allseen
    if missing:raise ValueError(f'原文包版本不匹配，缺少 {len(missing)} 件护甲名称；未输出文件')
    a.output.mkdir(parents=True,exist_ok=True)
    for name,data in staged:
        dest=a.output/(name+'.msgbnd.dcx')
        if dest.exists():raise ValueError(f'输出文件已存在：{dest}，请选择新目录')
    for name,data in staged:(a.output/(name+'.msgbnd.dcx')).write_bytes(data)
    print(f'已生成 {len(allseen)} 件护甲的简中说明；把两个输出文件复制至 ModEngine/mod/msg/zhocn/')
if __name__=='__main__':main()
