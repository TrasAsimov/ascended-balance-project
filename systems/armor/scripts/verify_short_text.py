"""Verify effect-only captions, including the Chinese merger in memory."""
from pathlib import Path
import json,sys,statistics,re
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parents[1]/'scripts'))
from build_zhocn_patch import fmg_read
from formats import bnd_entries,dcx_unpack
from merge_zhocn import patch

def main():
    zh=json.loads((ROOT/'data/description_zh.json').read_text())
    en=json.loads((ROOT/'data/description_en.json').read_text())
    assert zh.keys()==en.keys() and len(zh)==741
    masks=json.loads((ROOT/'data/sets.json').read_text())
    armors=json.loads((ROOT/'data/armor_index.json').read_text())
    for rid in zh:
        g=masks[armors[rid]['key']]
        assert zh[rid].splitlines()[0].endswith(f"（{g['full']}件）")
        assert en[rid].splitlines()[0]==g['english_name']+f" ({g['full']} {'piece' if g['full']==1 else 'pieces'})"
        for language, descriptions in [('zh',zh),('en',en)]:
            text=descriptions[rid]
            assert not re.search(r'[×x]\d',text), (rid,text)
            assert not any(s in text for s in ['原版','Original piece','Retained Mod','independent','独立倍率','[Armor effects'])
            if len(text.splitlines())>1:
                assert text.splitlines()[1]==''
            for line in text.splitlines()[2:]:
                assert not line.strip() or line.startswith('    ') or re.match(r'(单件|[234]件|Piece|[234] pcs) · ',line), (rid,line)
            for tier in {r['tier'] for r in g['rewards'] if r['tier']>1}:
                label=f'{tier}件 · ' if language=='zh' else f'{tier} pcs · '
                assert label in text
        if any(r['tier']>2 and r['exclusive'] for r in g['rewards']):
            assert '替换2件' in zh[rid] and 'replaces 2 pcs' in en[rid]
    core={2090:'+400%',2120:'+250%',2130:'+200%',2140:'+120%',2150:'+100%',2180:'+100%',2200:'+300%',4100:'-50%'}
    captions=0;fixture=0
    for name in ['item_dlc01','item_dlc02']:
        raw=dcx_unpack((ROOT/f'ModEngine/mod/msg/engus/{name}.msgbnd.dcx').read_bytes())
        parts=bnd_entries(raw)
        for key,(_,body) in parts.items():
            if key.startswith('AccessoryCaption'):
                entries=fmg_read(body)
                for rid,rate in core.items():
                    if rid in entries:
                        assert rate in entries[rid] and len(entries[rid].splitlines())==1 and not re.search(r'[×x]\d',entries[rid])
                        captions+=1
        # English container is a structural fixture only. Do not output or
        # present this in-memory mixed-language result as a Chinese archive.
        packed,seen=patch(raw,zh)
        assert seen==set(map(int,zh))
        for key,(_,body) in bnd_entries(dcx_unpack(packed)).items():
            if key.startswith('ProtectorCaption'):
                for rid,text in fmg_read(body).items():
                    if str(rid) in zh:assert text==zh[str(rid)];fixture+=1
    assert captions==16
    result={'armor_descriptions':741,'max_logical_lines':max(len(t.splitlines()) for t in en.values()),'set_piece_counts':'all 741 verified against unique equipped slots','format':'percentage only; one effect per line; explicit tier counts','zh_character_median':statistics.median(map(len,zh.values())),'zh_character_max':max(map(len,zh.values())),'en_character_max':max(map(len,en.values())),'compact_talisman_captions_checked':captions,'chinese_merge_structural_fixture_captions':fixture,'actual_chinese_archive':'not generated; matching owned zhocn inputs unavailable','in_game_layout':'not tested'}
    (ROOT/'data/short_text_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
