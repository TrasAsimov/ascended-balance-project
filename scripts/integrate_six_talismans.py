"""Stage the authorized Expanded Talisman Slots DLL with exactly two extra slots.

Reads an existing release and the original author archive; produces three
runtime overlay files and an audit only. Never builds a package or edits PARAM,
events, actions, or saves. Supply the newest release to avoid rolling back work.
"""
import argparse, configparser, hashlib, json, re, struct, tomllib, zipfile
from pathlib import Path

AUTHOR_ARCHIVE_SHA='bc917f070f41b1f0387d2c4ad465398ad6fa76292c1533d8323dab3bc364ea85'
DLL='ExpandedTalismanSlots.dll'
INI='ExpandedTalismanSlots.ini'

def sha(blob):return hashlib.sha256(blob).hexdigest()

def configure_ini(blob):
    text=blob.decode('utf-8-sig');config=configparser.ConfigParser()
    config.read_string(text)
    assert config.has_section('talisman_slots')
    assert config.getint('talisman_slots','enabled') in (0,1)
    assert 1<=config.getint('talisman_slots','slots')<=19
    for key,value in [('enabled',1),('slots',2)]:
        pattern=rf'(?m)^([ \t]*{key}[ \t]*=[ \t]*)\d+([ \t]*(?:[;#][^\r\n]*)?\r?)$'
        text,n=re.subn(pattern,lambda m:m[1]+str(value)+m[2],text)
        assert n==1,('ambiguous config option',key)
    after=configparser.ConfigParser();after.read_string(text)
    assert after.getint('talisman_slots','enabled')==1
    assert after.getint('talisman_slots','slots')==2
    old={s:dict(config[s]) for s in config.sections()}
    expected={s:dict(after[s]) for s in after.sections()}
    old['talisman_slots'].update(enabled='1',slots='2')
    assert old==expected
    return text.encode('utf-8')

def configure_loader(blob):
    text=blob.decode('utf-8-sig');before=tomllib.loads(text)
    dlls=before['modengine'].get('external_dlls',[])
    assert isinstance(dlls,list) and all(isinstance(d,str) for d in dlls)
    if any(Path(d.replace('\\','/')).name.casefold()==DLL.casefold() for d in dlls):
        assert dlls.count(DLL)==1,'Existing DLL path requires explicit reconciliation'
        return blob
    replacement=json.dumps(dlls+[DLL])
    match=re.search(r'(?m)^\[modengine\][ \t]*(?:#[^\r\n]*)?(?:\r?\n|$)',text)
    assert match,'missing modengine section'
    end=re.search(r'(?m)^\[',text[match.end():]);stop=match.end()+end.start() if end else len(text)
    section=text[match.end():stop]
    if 'external_dlls' in before['modengine']:
        section,n=re.subn(r'(?ms)^([ \t]*external_dlls[ \t]*=[ \t]*)\[.*?\]',
                         lambda m:m[1]+replacement,section)
        assert n==1,'Unrecognized DLL list format'
        result=text[:match.end()]+section+text[stop:]
    else:
        newline='\r\n' if '\r\n' in text else '\n'
        result=text[:match.end()]+'external_dlls = '+replacement+newline+text[match.end():]
    expected=json.loads(json.dumps(before));expected['modengine']['external_dlls']=dlls+[DLL]
    assert tomllib.loads(result)==expected,'Unrelated loader setting changed'
    return result.encode('utf-8')

def integrate(files,archive):
    assert sha(archive)==AUTHOR_ARCHIVE_SHA,'Use the inspected author v1.1.6 archive'
    import io
    with zipfile.ZipFile(io.BytesIO(archive)) as source:
        assert source.testzip() is None
        assert len(source.namelist())==len(set(source.namelist()))==2
        assert set(source.namelist())=={DLL,INI}
        dll=source.read(DLL);ini=configure_ini(source.read(INI))
    assert dll[:2]==b'MZ'
    pe=struct.unpack_from('<I',dll,60)[0]
    assert dll[pe:pe+4]==b'PE\0\0' and struct.unpack_from('<H',dll,pe+4)[0]==0x8664
    assert struct.unpack_from('<H',dll,pe+22)[0]&0x2000,'Not a DLL'
    config_path='ModEngine/config_eldenring.toml'
    updates={config_path:configure_loader(files[config_path]),
             'ModEngine/'+DLL:dll,'ModEngine/'+INI:ini}
    for name in ('ModEngine/'+DLL,'ModEngine/'+INI):
        if name in files:assert files[name]==updates[name],'Conflicting existing native module'
    merged=dict(files,**updates)
    assert all(merged[n]==b for n,b in files.items() if n not in updates)
    assert configure_ini(ini)==ini and configure_loader(updates[config_path])==updates[config_path]
    assert [n for n in merged if n.endswith('regulation.bin')]==['ModEngine/mod/regulation.bin']
    return updates,{'native_slots':4,'extra_slots':2,'total_slots':6,
        'upstream_archive_sha256':sha(archive),'upstream_version':'1.1.6',
        'dll_x64_pe_verified':True,'original_dll_unchanged':True,
        'ini_filename_verified':INI,'idempotent':True,
        'existing_non_target_files_byte_identical':sum(n not in updates for n in files),
        'regulation_sha256_unchanged':sha(files['ModEngine/mod/regulation.bin']),
        'runtime_paths':{n:{'bytes':len(b),'sha256':sha(b)} for n,b in updates.items()},
        'game_validation':'not run','package_generated':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base_zip','upstream_zip','output'):
        p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    a=p.parse_args()
    with zipfile.ZipFile(a.base_zip) as source:
        names=[n for n in source.namelist() if not n.endswith('/')]
        assert len(names)==len(set(names))
        prefix=names[0].split('/')[0]+'/'
        assert all(n.startswith(prefix) for n in names)
        files={n[len(prefix):]:source.read(n) for n in names}
    updates,report=integrate(files,a.upstream_zip.read_bytes())
    assert integrate(dict(files,**updates),a.upstream_zip.read_bytes())[0]==updates
    for name,body in updates.items():
        path=a.output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body)
    report.update(base_zip_name=a.base_zip.name,base_zip_sha256=sha(a.base_zip.read_bytes()),
                  upstream_author='imCioco',upstream_url='https://www.nexusmods.com/eldenring/mods/10481')
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'six_talisman_integration_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
