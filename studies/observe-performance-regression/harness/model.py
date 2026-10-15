"""One real SAM image: native reference, then cold/warm Observe validation.

Uses the study's frozen programs, model fixtures and isolated artifact layout.
Does not run the entire DPT development sequence or download data.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'studies/paper-size-benchmarks/harness'))
from common import WORK,SCRATCH,atomic_json,remove_owned,supervise,file_hash
from study import doctor,freeze,fixture,environment,lock
from provenance import fingerprint,verify,validate_arguments
from cache_metadata import directory_summary


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--id',required=True)
    parser.add_argument('--repetitions',type=int,default=2)
    args=parser.parse_args();validate_arguments(parser,args)
    result=ROOT/'studies/observe-performance-regression/results'/args.id
    result.mkdir(parents=True,exist_ok=False)
    fingerprint(ROOT,result,Path(__file__))
    doctor()
    build=freeze(result)
    data=WORK/'data/min/dpt'
    app=fixture('dpt',data,build,'min')
    env=environment('dpt','min',app,build)
    cache=SCRATCH/'cache'
    remove_owned(cache);cache.mkdir()
    image=next(iter(sorted((app/'inputs/dpt.ref').glob('*.jpg'))))
    env['IN_IMAGE']=str(image)
    timing=SCRATCH/'model-timing.json';timing.write_text('{}')
    invoke=SCRATCH/'model-invoke.sh';invoke.write_text('cat "$IN_IMAGE" | "$@"\n')
    atomic_json(result/'input.json',{'image':str(image),'sha256':file_hash(image),
        'prepared':json.loads((data/'prepared.json').read_text())})
    worker=('import json,resource,subprocess,sys,time;start=time.perf_counter();'
            'p=subprocess.Popen(sys.argv[2:],close_fds=True);status=p.wait();elapsed=time.perf_counter()-start;'
            'r=resource.getrusage(resource.RUSAGE_CHILDREN);'
            'open(sys.argv[1],"w").write(json.dumps({"elapsed_sec":elapsed,"user_sec":r.ru_utime,"system_sec":r.ru_stime,"max_rss_kib":r.ru_maxrss}));sys.exit(status)')
    rows=[];oracle=None
    try:
        for mode,count in [('bash',1),('observe',args.repetitions)]:
            remove_owned(cache);cache.mkdir()
            for repetition in range(count):
                capture=SCRATCH/'capture';remove_owned(capture)
                command=['python3','scripts/segment.py']
                if mode=='observe':
                    command=[str(build/'candidate/target/release/incr'),'--effect-policy','final',
                        '--observe',str(build/'observe/target/release/observe'),
                        '--try',str(build/'candidate/src/scripts/try.sh'),'--cache',str(cache),'--',*command]
                row=supervise([sys.executable,'-c',worker,str(timing),'bash',str(invoke),*command],cwd=app,env=env,
                    capture=capture,timeout=180,reserve=8*1024**3,budget=32*1024**3)
                actual=[row['returncode'],row['stdout_sha256'],row['stderr_sha256']]
                if mode=='bash':oracle=actual
                resources=json.loads(timing.read_text()) if timing.exists() else {}
                row.update(mode=mode,repetition=repetition,command_resources=resources,
                    valid=not row['failure'] and row['returncode']==0 and actual==oracle)
                row['metadata']=[directory_summary(path) for path in cache.glob('batch_*/data.incr')]
                if not row['valid']:row['stderr_sample']=(capture/'stderr').read_text(errors='replace')[:4096]
                rows.append(row);atomic_json(result/'measurements.json',rows)
                print(mode,repetition,resources,row['valid'],len(row['metadata']),flush=True)
                if not row['valid']:raise RuntimeError('Model output/status mismatch')
        atomic_json(result/'summary.json',{'valid':all(row['valid'] for row in rows),'samples':len(rows)})
    finally:
        try:verify(ROOT,result,Path(__file__))
        finally:
            if list(cache.glob('*.recovery')):raise RuntimeError('Recovery retained; inspect fixture/cache')
            for path in (cache,app,SCRATCH/'capture',timing,invoke):remove_owned(path)


if __name__=='__main__':
    with lock():main()
