"""Serial attribution of stdin transport versus tracing; no command substitutions.

The external program is always the installed GNU sort with identical flags.
Input is either a regular descriptor or an anonymous pipe containing the same
bytes. These diagnostic timings are not a benchmark-family performance claim.
"""
import argparse
import json
import os
from pathlib import Path
import random
import statistics
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'studies/paper-size-benchmarks/harness'))
from common import WORK, atomic_json, file_hash, remove_owned, supervise
from provenance import fingerprint, verify, validate_arguments
from study import lock

WORKER = '''import json,pathlib,resource,subprocess,sys,time
transport,source,timing=sys.argv[1:4]
data=pathlib.Path(source).read_bytes() if transport=='pipe' else None
with open(source,'rb') as input_file:
 start=time.perf_counter()
 child=subprocess.Popen(sys.argv[4:],stdin=subprocess.PIPE if transport=='pipe' else input_file,close_fds=True)
 if transport=='pipe': child.communicate(data)
 else: child.wait()
 elapsed=time.perf_counter()-start
 usage=resource.getrusage(resource.RUSAGE_CHILDREN)
 pathlib.Path(timing).write_text(json.dumps(dict(elapsed_sec=elapsed,user_sec=usage.ru_utime,system_sec=usage.ru_stime,max_rss_kib=usage.ru_maxrss,output_blocks=usage.ru_oublock,voluntary_switches=usage.ru_nvcsw,involuntary_switches=usage.ru_nivcsw)))
 sys.exit(child.returncode)
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id',required=True)
    parser.add_argument('--mib',type=int,default=8)
    parser.add_argument('--repetitions',type=int,default=3)
    args=parser.parse_args();validate_arguments(parser,args)
    result=ROOT/'studies/observe-performance-regression/results'/args.id
    result.mkdir(parents=True,exist_ok=False)
    old=ROOT/'studies/observe-performance-regression/.work/observe-before-audit'
    fingerprint(ROOT,result,Path(__file__),[old])
    owned=Path(tempfile.mkdtemp(prefix='fd-transport-',dir=WORK))
    (owned/'tmp').mkdir()
    source=owned/'input'
    line=b'one\ntwo\nthree\nfour\nfive\nsix\nseven\neight\nnine\nten\n'
    source.write_bytes(line*(args.mib*1024**2//len(line)+1))
    source_hash=file_hash(source)
    atomic_json(result/'input.json',dict(bytes=source.stat().st_size,sha256=source_hash,recipe='Repeated complete token records; synthetic diagnostic'))
    env={k:os.environ[k] for k in ('HOME','USER','LOGNAME','PATH') if k in os.environ}
    env.update(LC_ALL='C',LANG='C',TMPDIR=str(owned/'tmp'))
    variants=[(mode,transport) for mode in ('native','observe','observe-dependencies','old-observe') for transport in ('file','pipe')]
    rows=[];reference=None
    try:
        for repetition in range(args.repetitions):
            ordered=list(variants);random.Random(repetition).shuffle(ordered)
            if repetition==0:
                ordered.remove(('native','file'));ordered.insert(0,('native','file'))
            for mode,transport in ordered:
                report=owned/'report.json';report.unlink(missing_ok=True)
                command=['sort']
                if mode!='native':
                    observer=old/'target/release/observe' if mode=='old-observe' else ROOT.parent/'observe/target/release/observe'
                    command=[str(observer),'--json','--hash','--output',str(report),*(['--dependencies'] if mode=='observe-dependencies' else []),'--',*command]
                capture=owned/'capture';remove_owned(capture)
                timing=owned/'timing.json';timing.unlink(missing_ok=True)
                row=supervise([sys.executable,'-c',WORKER,transport,str(source),str(timing),*command],cwd=owned,env=env,capture=capture,timeout=120,reserve=8*1024**3,budget=32*1024**3)
                observed=[row['returncode'],row['stdout_sha256'],row['stderr_sha256']]
                if reference is None:reference=observed
                resources=json.loads(timing.read_text()) if timing.exists() else {}
                row.update(mode=mode,transport=transport,repetition=repetition,command_resources=resources,valid=not row['failure'] and row['returncode']==0 and observed==reference and bool(resources))
                if mode!='native':
                    data=json.loads(report.read_text()) if report.is_file() else {}
                    row['valid']=row['valid'] and bool(data.get('reads'))
                    atomic_json(result/f'{mode}-{transport}-{repetition}-report.json',data)
                rows.append(row);atomic_json(result/'measurements.json',rows)
                print(mode,transport,repetition,round(resources.get('elapsed_sec',0),5),row['valid'],flush=True)
                if not row['valid']:raise RuntimeError('Transport diagnostic failed correctness')
        if file_hash(source)!=source_hash:raise RuntimeError('Input changed')
        stats=[]
        for mode,transport in variants:
            samples=[r['command_resources']['elapsed_sec'] for r in rows if r['mode']==mode and r['transport']==transport]
            stats.append(dict(mode=mode,transport=transport,samples=len(samples),mean_sec=statistics.mean(samples),median_sec=statistics.median(samples),stdev_sec=statistics.stdev(samples) if len(samples)>1 else None))
        atomic_json(result/'summary.json',dict(valid=all(r['valid'] for r in rows) and len(rows)==len(variants)*args.repetitions,samples=len(rows),statistics=stats,scope='Synthetic transport/tracer diagnostic; not benchmark-family evidence'))
    finally:
        try:verify(ROOT,result,Path(__file__))
        finally:remove_owned(owned)


if __name__=='__main__':
    with lock():main()
