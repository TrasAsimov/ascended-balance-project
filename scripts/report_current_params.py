"""Reproducible, field-level comparisons for the integrated snapshot."""
from collections import Counter, defaultdict
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / 'work'))
from analyze_regulation import read_bnd
from field_diff import decode, defs, fields, names

SOURCES = {
    'vanilla': ROOT / 'work/vanilla_117.bnd',
    'v05': ROOT / 'work/v05_reconciled.bnd',
    'current': ROOT / 'work/pending_spell_boss_bonus.bnd',
}
LABELS = {
    'EquipParamWeapon':'武器／盾牌', 'SpEffectParam':'特殊效果',
    'NpcParam':'敌人与 NPC', 'AtkParam_Pc':'玩家攻击判定',
    'AtkParam_Npc':'敌人攻击判定', 'Magic':'魔法和祷告',
    'EquipParamAccessory':'护符', 'EquipParamGoods':'道具',
    'CalcCorrectGraph':'属性成长曲线', 'ThrowParam':'处决动作',
    'ItemLotParam_map':'地图奖励', 'MenuColorTableParam':'菜单色彩',
}

def value_rows(a, b, output):
    """Write every comparable changed field and count table-level row states."""
    stats=defaultdict(Counter)
    byfield=defaultdict(Counter)
    unknown=[]
    with output.open('w', newline='', encoding='utf-8-sig') as fh:
        writer=csv.writer(fh)
        writer.writerow(('参数表','中文类别','行ID','行名（参考）','字段','基线值','当前值'))
        ds=defs()
        for table in sorted(a):
            left,right=a[table],b[table]
            aa,bb=left['rows'],right['rows']
            cn=Counter(); stats[table]=cn
            cn['基线行']=len(aa);cn['当前行']=len(bb)
            cn['新增行']=len(bb.keys()-aa.keys())
            cn['缺失行']=len(aa.keys()-bb.keys())
            spec=ds.get(left['ptype'])
            ff,n=fields(spec) if spec else ([],0)
            valid=(left['row_size']==right['row_size']==n)
            if not valid and aa.keys()&bb.keys():
                unknown.append((table,left['row_size'],right['row_size'],n))
            nn=names(table)
            for rid in sorted(aa.keys()&bb.keys()):
                x,y=aa[rid]['data'],bb[rid]['data']
                if x==y:continue
                cn['改动共有行']+=1
                if not valid:continue
                for f in ff:
                    if x[f[2]:f[2]+f[3]]==y[f[2]:f[2]+f[3]]:continue
                    va,vb=decode(x,f),decode(y,f)
                    if va==vb:continue
                    writer.writerow((table,LABELS.get(table,''),rid,nn.get(rid,''),f[0],va,vb))
                    cn['字段改动']+=1;byfield[table][f[0]]+=1
            cn['相同行']=len(aa.keys()&bb.keys())-cn['改动共有行']
    return stats,byfield,unknown

def main():
    parsed={k:read_bnd(p) for k,p in SOURCES.items()}
    for k,(version,tables) in parsed.items():
        assert version=='11711000' and len(tables)==194,(k,version,len(tables))
    for k,title in [('vanilla','官方原版 1.17.1'),('v05','v0.5')]:
        csvpath=ROOT/'changes'/f'{k}_to_current_fields.csv'
        stats,byfield,unknown=value_rows(parsed[k][1],parsed['current'][1],csvpath)
        out=ROOT/'docs'/f'{k}_to_current_summary.generated.md'
        total=Counter()
        for v in stats.values():total.update(v)
        with out.open('w',encoding='utf-8') as f:
            f.write(f'# {title} → 当前 v0.10 集成测试参数\n\n')
            f.write('基线及当前均是内部版本 `11711000` 的 194 张参数表。仅比较 `regulation.bin` 参数行；'+
                    '事件、文本、地图及角色动画另行记录。相同共有行不会列入 CSV。\n\n')
            f.write('逐字段全量明细（gzip 压缩的 CSV，下载后解压）：[`../changes/'+csvpath.name+'.gz`](../changes/'+csvpath.name+'.gz)。'+
                    '独有行只有行级数量，不在字段 CSV 中假定原值。\n\n')
            f.write('| 指标 | 数量 |\n|---|---:|\n')
            for field in ('基线行','当前行','新增行','缺失行','改动共有行','字段改动','相同行'):
                f.write(f'| {field} | {total[field]:,} |\n')
            f.write('\n| 参数表 | 中文类别 | 基线行 | 当前行 | 新增 | 缺失 | 改动共有行 | 逐字段变化 |\n')
            f.write('|---|---|---:|---:|---:|---:|---:|---:|\n')
            for table,c in sorted(stats.items(),key=lambda x:(-x[1]['字段改动'],-x[1]['改动共有行'],x[0])):
                if any(c[n] for n in ('新增行','缺失行','改动共有行')):
                    f.write(f'| `{table}` | {LABELS.get(table,"")} | {c["基线行"]} | {c["当前行"]} | {c["新增行"]} | {c["缺失行"]} | {c["改动共有行"]} | {c["字段改动"]} |\n')
            f.write('\n## 差异最多的字段\n\n| 参数表 | 字段 | 变化行数 |\n|---|---|---:|\n')
            for table,c in sorted(byfield.items()):
                for field,count in c.most_common(8):
                    f.write(f'| `{table}` | `{field}` | {count} |\n')
            if unknown:
                f.write('\n## 无法逐字段解析的表\n\n')
                for row in unknown:f.write(f'- `{row[0]}`: 行字节数 {row[1]} → {row[2]}；定义 {row[3]}。\n')
        print(k,dict(total),'CSV bytes',csvpath.stat().st_size,'unparsed',unknown)

if __name__=='__main__':main()
