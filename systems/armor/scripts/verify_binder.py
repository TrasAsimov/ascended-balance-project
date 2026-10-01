"""Audit packed BND4 layout; optional failed candidate proves isolation.

This checks external container metadata and every opaque PARAM payload,
without inferring row sizes or changing the approved armor design.
"""
from pathlib import Path
import argparse, hashlib, json, struct
from formats import bnd_entries, bnd_repack

ROOT=Path(__file__).resolve().parent.parent

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--previous-bnd',type=Path)
    args=parser.parse_args()
    base=(ROOT/'inputs/pending_v0105/adjusted.bnd').read_bytes()
    final=(ROOT/'data/result.bnd').read_bytes()
    base_parts=bnd_entries(base);parts=bnd_entries(final)
    assert parts.keys()==base_parts.keys() and len(parts)==194
    first=struct.unpack_from('<Q',base,0x28)[0]
    assert final[:64]==base[:64]
    metadata=bytearray(final[:first]);end=first;payload=0;padding=0
    for name,(h,body) in parts.items():
        size,usize,off=struct.unpack_from('<QQI',final,h+8)
        assert size==usize==len(body)
        aligned=(end+15)//16*16
        assert off==aligned and final[end:off]==bytes(off-end),(name,end,off)
        padding+=off-end;payload+=len(body);end=off+size
        assert end<=len(final)
        metadata[h+8:h+28]=base[h+8:h+28]
    assert end==len(final), 'Unexpected trailing unreferenced data'
    assert metadata==base[:first], 'Names, IDs, flags, hash table or opaque metadata changed'
    assert len(final)==first+payload+padding
    assert bnd_repack(base,{})==base, 'No-op repack must reproduce the tested native binder exactly'
    assert bnd_repack(final,{})==final, 'Repacking must be idempotent'
    # The only legitimate size increase is changed member sizes plus the
    # bounded alignment adjustment. Do not invent an engine memory limit.
    growth=sum(len(parts[n][1])-len(base_parts[n][1]) for n in parts)
    assert abs((len(final)-len(base))-growth)<=15*len(parts)
    previous=None
    if args.previous_bnd:
        old=args.previous_bnd.read_bytes();prior=bnd_entries(old)
        assert prior.keys()==parts.keys()
        assert all(prior[n][1]==parts[n][1] for n in parts), 'A parameter payload changed in the container-only test'
        assert bnd_repack(old,{})==final
        previous={'bytes':len(old),'sha256':hashlib.sha256(old).hexdigest(),'identical_table_payloads':194,'removed_unreferenced_bytes':len(old)-len(final)}
    result={'status':'static container audit passed; game test not run','native_base_bytes':len(base),'candidate_bytes':len(final),'candidate_sha256':hashlib.sha256(final).hexdigest(),'member_count':len(parts),'member_payload_bytes':payload,'metadata_bytes':first,'alignment_bytes':padding,'unreferenced_data_bytes':0,'baseline_noop_byte_identity':True,'idempotent':True,'metadata_changes':'member sizes and offsets only','legitimate_payload_growth':growth,'previous_candidate':previous,'game_validation':{'startup':'not run','load':'not run','save_and_reload':'not run','armor_and_set_effects':'not run'}}
    (ROOT/'data/binder_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
