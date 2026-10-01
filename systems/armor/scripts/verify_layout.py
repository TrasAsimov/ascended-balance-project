"""Audit offset preservation without using read_param's inferred row size.

Use after build.py. Optional --previous-bnd verifies that the fix changes
layout only, and --excel checks the original approved workbook, read-only.
This is a binary audit, not an Elden Ring startup/save test.
"""
from pathlib import Path
import argparse, hashlib, json, struct, sys, zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parents[1]/'scripts'))
from field_diff import defs, fields
from formats import bnd_entries

def directory(blob,size):
    assert blob[0x2c]==0 and blob[0x2d]&0x84==0x84
    assert blob[4:6]==bytes(2) and blob[12:16]==bytes(4)
    assert blob[0x18:0x2c]==bytes(20) and blob[0x38:0x40]==bytes(8)
    count=struct.unpack_from('<H',blob,10)[0];end=64+24*count
    assert end<=len(blob)
    entries={}
    for i in range(count):
        rid,pad,off,name=struct.unpack_from('<iIQQ',blob,64+24*i)
        assert rid not in entries and end<=off<=len(blob)-size
        if name:
            assert end<=name<len(blob)
            step=2 if blob[0x2e]&1 else 1
            stop=name
            while stop+step<=len(blob) and blob[stop:stop+step]!=bytes(step):stop+=step
            assert stop+step<=len(blob),('unterminated row name',rid)
        entries[rid]=(pad,off,name,blob[off:off+size])
    spans=sorted((r[1],r[1]+size) for r in entries.values())
    assert all(a[1]<=b[0] for a,b in zip(spans,spans[1:]))
    return entries,end

def workbook_notes(path):
    ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(path) as z:
        shared=[''.join(t.itertext()) for t in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)]
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        rels={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        result=[]
        for s in wb.findall('m:sheets/m:sheet',ns):
            target=rels[s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            for row in ET.fromstring(z.read(target)).findall('m:sheetData/m:row',ns):
                if int(row.attrib['r'])<8:continue
                cells={}
                for c in row:
                    v=c.find('m:v',ns);value=v.text if v is not None else ''
                    if c.get('t')=='s':value=shared[int(value)]
                    elif c.get('t')=='inlineStr':value=''.join(c.find('m:is',ns).itertext())
                    if value:cells[c.attrib['r'].rstrip('0123456789')]=value
                if s.attrib['name']=='套装增益':
                    assert not any(cells.get(k) for k in ['H','J','L']), 'Unprocessed set-specific workbook edit'
                elif s.attrib['name']=='单件调整':
                    assert not any(cells.get(k) for k in ['I','J']), 'Unprocessed armor membership/remark edit'
                    if cells.get('H'):result.append(('armor',cells['D'],8,cells['H']))
                elif s.attrib['name']=='草案对照' and cells.get('I'):
                    result.append(('drafts',cells['C'],9,cells['I']))
        return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--previous-bnd',type=Path);parser.add_argument('--excel',type=Path)
    args=parser.parse_args()
    base=bnd_entries((ROOT/'inputs/pending_v0105/adjusted.bnd').read_bytes())
    out=bnd_entries((ROOT/'data/result.bnd').read_bytes())
    assert base.keys()==out.keys() and len(out)==194
    definitions=defs();report={};previous=bnd_entries(args.previous_bnd.read_bytes()) if args.previous_bnd else None
    expected_changed={'EquipParamProtector.param','SpEffectParam.param','BehaviorParam_PC.param','Bullet.param'}
    for name,(_,blob) in base.items():
        final=out[name][1]
        if name not in expected_changed:
            assert final==blob,('unrelated table bytes changed',name)
            if previous:assert final==previous[name][1]
            continue
        typeoff=struct.unpack_from('<Q',blob,0x10)[0]
        ptype=blob[typeoff:blob.index(b'\0',typeoff)].decode('ascii')
        _,size=fields(definitions[ptype])
        before,end=directory(blob,size);after,newend=directory(final,size)
        added=after.keys()-before.keys();assert before.keys()<=after.keys()
        delta=24*len(added);assert newend==end+delta
        header=bytearray(blob[:64]);struct.pack_into('<H',header,10,len(after))
        if added:
            for pos,fmt in [(0,'I'),(0x10,'Q'),(0x30,'Q')]:
                ptr=struct.unpack_from('<'+fmt,header,pos)[0]
                if ptr:struct.pack_into('<'+fmt,header,pos,ptr+delta)
        assert final[:64]==header,('header metadata changed',name)
        restored=bytearray(blob[end:]);changed=0
        for rid,(pad,off,nptr,body) in before.items():
            apad,aoff,anptr,abody=after[rid]
            assert (apad,aoff,anptr)==(pad,off+delta,nptr+delta if nptr else 0),(name,rid)
            restored[off-end:off-end+size]=abody
            changed+=body!=abody
        assert final[end+delta:len(blob)+delta]==restored,('opaque data/name/tail bytes changed',name)
        if not added:assert len(final)==len(blob)
        if previous:
            prior,_=directory(previous[name][1],size)
            assert prior.keys()==after.keys()
            for rid in prior:assert prior[rid][3]==after[rid][3],('effect design changed',name,rid)
        report[name]={'row_size_from_definition':size,'existing_rows':len(before),'added_rows':len(added),'changed_rows':changed,'existing_offsets_shift_only':delta}
    approval=json.loads((ROOT/'config/approved_edits.json').read_text())
    if args.excel:
        assert hashlib.sha256(args.excel.read_bytes()).hexdigest()==approval['excel_sha256']
        actual=workbook_notes(args.excel)
        expected=[(r['sheet'],r['id'],c['column'],c['after']) for r in approval['changes'] for c in r['changes']]
        assert sorted(actual)==sorted(expected), 'Workbook decisions differ from approved configuration'
    result={'table_audit':report,'untouched_table_bodies':190,'matches_previous_design':bool(previous),'approved_workbook_checked':bool(args.excel),'startup':'not run','load':'not run','save_and_reload':'not run','runtime_set_and_piece_effects':'not run'}
    (ROOT/'data/layout_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
