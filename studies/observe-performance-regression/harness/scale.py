"""Serial diagnostic scaling of minimum fixtures; never paper-size measurements.

Reuses the full study's frozen runtimes, per-version native oracle, filesystem
validators, resource collection and cleanup. Repetition of tiny source fixtures
retains their limited vocabulary/distribution and cannot establish paper speedups.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'studies/paper-size-benchmarks/harness'))
from common import WORK,STUDY,GIB,atomic_json,file_hash,remove_owned
from study import doctor,freeze,execute_sequence,report,selected,lock,now
from provenance import fingerprint,verify,validate_arguments


def replicate(source,target,requested):
    content=source.read_bytes()
    if not content:raise ValueError('Empty minimum fixture')
    source_hash=hashlib.sha256(content).hexdigest()
    if not content.endswith(b'\n'):content+=b'\n'
    copies=(requested+len(content)-1)//len(content)
    block=content*max(1,min(copies,1024**2//len(content)))
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('wb') as output:
        remaining=copies
        per_block=len(block)//len(content)
        while remaining:
            count=min(remaining,per_block)
            output.write(block[:count*len(content)])
            remaining-=count
    if file_hash(source)!=source_hash:raise RuntimeError('Minimum source changed during replication')
    return {'recipe':'Replicate complete minimum-fixture records; append final newline if absent',
            'source':str(source),'source_sha256':source_hash,'copies':copies,
            'bytes':target.stat().st_size,'sha256':file_hash(target)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id',required=True)
    parser.add_argument('--only',default='poet,covid,weather')
    parser.add_argument('--mib',type=int,default=8)
    parser.add_argument('--repetitions',type=int,default=1)
    parser.add_argument('--native-transform',action='store_true')
    parser.add_argument('--assume-directory-access',action='store_true')
    args=parser.parse_args();validate_arguments(parser,args)
    if not set(args.only.split(',')) <= {'poet','covid','weather','word-freq'}:
        parser.error('Scaling supports poet, COVID, temperature-weather and word frequency')
    if args.mib>256:parser.error('Diagnostic scaling is bounded to 256 MiB per family')
    result=ROOT/'studies/observe-performance-regression/results'/args.id
    result.mkdir(parents=True,exist_ok=False);fingerprint(ROOT,result,Path(__file__))
    parameters=SimpleNamespace(profile='scaled',only=args.only,repetitions=args.repetitions,
        modes=('bash','original','observe'),annotations=False,reserve_gib=8,work_budget_gib=32,native_transform=args.native_transform,
        assume_directory_access=args.assume_directory_access)
    atomic_json(result/'configuration.json',dict(vars(parameters),started=now(),mib=args.mib,
        scope='Synthetic scaling diagnostic from repeated minimum fixtures; not historical-size evaluation'))
    doctor();build=freeze(result)
    owned=Path(tempfile.mkdtemp(prefix='scale-',dir=WORK));references={}
    try:
        for benchmark in selected(args.only):
            name=benchmark['name'];relative={'poet':'books/sample.txt','covid':'covid.csv','weather':'temperatures.txt',
                'word-freq':'text.txt'}[name]
            data=owned/name
            recipe=replicate(WORK/'data/min'/name/'inputs'/relative,data/'inputs'/relative,args.mib*1024**2)
            atomic_json(result/'inputs'/f'{name}.json',dict(recipe,input_bytes=recipe['bytes'],models=[]))
            task=dict(benchmark,timeout_scaled=300)
            for repetition in range(args.repetitions):
                modes=['original','observe'] if repetition%2==0 else ['observe','original']
                for mode in ['bash',*modes]:
                    if file_hash(data/'inputs'/relative)!=recipe['sha256']:raise RuntimeError('Scaling input changed before measurement')
                    row=execute_sequence(result,task,mode,repetition,parameters,build,data,references)
                    if file_hash(data/'inputs'/relative)!=recipe['sha256']:raise RuntimeError('Scaling input changed during measurement')
                    report(result)
                    if not row['valid']:raise RuntimeError(f'Scaled validation failed: {name}/{mode}/{repetition}')
            remove_owned(data)
        summary=report(result)
        if not summary['complete']:raise RuntimeError('Incomplete scaling study')
        atomic_json(result/'status.json',{'state':'complete','updated':now(),'valid_invocations':summary['valid_invocations']})
    except BaseException as error:
        atomic_json(result/'sequences/probe-integrity/failed.json',{'valid':False,'error':repr(error)})
        report(result)
        atomic_json(result/'status.json',{'state':'error','updated':now(),'error':repr(error)})
        raise
    finally:
        try:verify(ROOT,result,Path(__file__))
        finally:remove_owned(owned)


if __name__=='__main__':
    with lock():main()
