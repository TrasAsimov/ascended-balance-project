"""Verify effect-only captions, including the Chinese merger in memory."""
from pathlib import Path
import json,sys,statistics
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parents[1]/'scripts'))
from build_zhocn_patch import fmg_read
from formats import bnd_entries,dcx_unpack
from merge_zhocn import patch

def main():
    zh=json.loads((ROOT/'data/description_zh.json').read_text())
    en=json.loads((ROOT/'data/description_en.json').read_text())
    assert zh.keys()==en.keys() and len(zh)==741
    for rid,text in zh.items():
        assert text.startswith('套装：') and len(text.splitlines())<=4
        assert not any(s in text for s in ['原版','保留 Mod','游戏帧','按实际穿戴','数值不相加','【护甲','单件效果仍'])
        for line in text.splitlines():assert line.startswith(('套装：','单件：','2件：','满套：'))
    for rid,text in en.items():
        assert text.startswith('Set: ') and len(text.splitlines())<=4
        assert not any(s in text for s in ['Original piece','Retained Mod','game frames','count by equipped','[Armor effects'])
    masks=json.loads((ROOT/'data/sets.json').read_text())
    for g in masks.values():
        for reward in g['rewards']:
            if reward['tier']>2 and any(r['exclusive'] for r in g['rewards']):
                for ids in g['pieces'].values():
                    for rid in ids:
                        assert '替换2件' in zh[str(rid)] and 'replaces 2 pieces' in en[str(rid)]
    core={2090:'x5.00',2120:'x3.50',2130:'x3.00',2140:'x2.20',2150:'x2.00',2180:'x2.00',2200:'x4.00',4100:'x0.50'}
    captions=0;fixture=0
    for name in ['item_dlc01','item_dlc02']:
        raw=dcx_unpack((ROOT/f'ModEngine/mod/msg/engus/{name}.msgbnd.dcx').read_bytes())
        parts=bnd_entries(raw)
        for key,(_,body) in parts.items():
            if key.startswith('AccessoryCaption'):
                entries=fmg_read(body)
                for rid,rate in core.items():
                    if rid in entries:
                        assert rate in entries[rid] and len(entries[rid].splitlines())==1
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
    result={'armor_descriptions':741,'max_logical_lines':4,'zh_character_median':statistics.median(map(len,zh.values())),'zh_character_max':max(map(len,zh.values())),'en_character_max':max(map(len,en.values())),'compact_talisman_captions_checked':captions,'chinese_merge_structural_fixture_captions':fixture,'actual_chinese_archive':'not generated; matching owned zhocn inputs unavailable','in_game_layout':'not tested'}
    (ROOT/'data/short_text_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
