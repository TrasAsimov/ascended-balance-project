"""Add matching single-piece Effect blocks without changing native/tier text."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'systems/armor/scripts'))
from formats import bnd_entries,bnd_patch,dcx_pack,dcx_unpack
from fmg import fmg_read,fmg_write
CONFIG=json.loads((ROOT/'systems/armor/config/tarnished_piece_bonuses.json').read_text())


def caption(rid,text,language):
    target=CONFIG['armors'].get(str(rid))
    if not target or not text:return text
    blocks=text.split('\n\n');label='效果: ' if language=='zh' else 'Effect: '
    position=next((i for i,b in enumerate(blocks) if ('件效果:' in b or '-Piece Effect:' in b)),len(blocks))
    new=[label+CONFIG['effects'][str(eid)][language] for eid in target['add_effect_ids']]
    new=[b for b in new if b not in blocks]
    return '\n\n'.join(blocks[:position]+new+blocks[position:])


def archive(blob):
    raw=dcx_unpack(blob);parts=bnd_entries(raw);updates={};changed=[]
    for name,(_,body) in parts.items():
        if not name.startswith('ProtectorCaption'):continue
        entries=fmg_read(body);after={rid:caption(rid,text,'en') for rid,text in entries.items()}
        ids=[rid for rid in entries if after[rid]!=entries[rid]]
        if ids:updates[name]=fmg_write(after);changed.extend(ids)
    if not updates:return blob,changed
    result=dcx_pack(bnd_patch(raw,updates));check=bnd_entries(dcx_unpack(result))
    for name,(_,body) in parts.items():
        if name not in updates:assert check[name][1]==body
        else:assert fmg_read(check[name][1])=={rid:caption(rid,text,'en') for rid,text in fmg_read(body).items()}
    return result,changed


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--language',choices=['en','zh'],default='en');a=p.parse_args()
    if a.input.suffix=='.json':
        original=json.loads(a.input.read_text());after={rid:caption(rid,text,a.language) for rid,text in original.items()}
        changed=[rid for rid in original if after[rid]!=original[rid]]
        assert {rid:caption(rid,text,a.language) for rid,text in after.items()}==after
        blob=(json.dumps(after,ensure_ascii=False,indent=2)+'\n').encode()
    else:
        blob,changed=archive(a.input.read_bytes());assert archive(blob)==(blob,[])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(blob)
    print(json.dumps({'output':str(a.output),'changed':len(changed),'idempotent':True},ensure_ascii=False))


if __name__=='__main__':main()
