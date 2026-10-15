"""Repeated salted encryption must always decrypt to the original input."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'studies/paper-size-benchmarks/harness'))
from common import WORK,atomic_json,file_hash,remove_owned,supervise


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--id',required=True)
    p.add_argument('--mib',type=int,default=8)
    p.add_argument('--runs',type=int,default=8)
    a=p.parse_args()
    from provenance import validate_arguments
    validate_arguments(p, a)
    result=ROOT/'studies/observe-performance-regression/results'/a.id
    result.mkdir(parents=True,exist_ok=False)
    from provenance import fingerprint
    fingerprint(ROOT, result, Path(__file__))
    owned=Path(tempfile.mkdtemp(prefix='crypto-repro-',dir=WORK));fixture=owned/'fixture';fixture.mkdir()
    (fixture/'input').write_bytes((b'0123456789abcdef'*65536)*a.mib)
    expected=file_hash(fixture/'input')
    (fixture/'invoke').write_text('exec "$@" < input\n')
    rows=[]
    try:
        for mode,top in [('original',ROOT.parent/'incr-main-qualification'),('observe',ROOT)]:
            cache=owned/'cache'
            if cache.exists():remove_owned(cache)
            cache.mkdir()
            env={k:os.environ[k] for k in ['HOME','USER','LOGNAME','PATH'] if k in os.environ}
            env.update(LC_ALL='C',INCR_EFFECT_POLICY='final')
            for iteration in range(a.runs):
                capture=owned/'capture'
                if capture.exists():remove_owned(capture)
                argv=[str(top/'target/release/incr'),'--try',str(top/'src/scripts/try.sh'),'--cache',str(cache)]
                if mode=='observe':argv+=['--observe',str(ROOT.parent/'observe/target/release/observe')]
                argv+=['--','openssl','enc','-aes-256-cbc','-pbkdf2','-iter','20000','-k','key']
                row=supervise(['bash',str(fixture/'invoke'),*argv],cwd=fixture,env=env,capture=capture,timeout=15,reserve=8*1024**3,budget=32*1024**3)
                decoded=owned/'decoded'
                with decoded.open('wb') as out:
                    proc=subprocess.run(['openssl','enc','-d','-aes-256-cbc','-pbkdf2','-iter','20000','-k','key','-in',str(capture/'stdout')],stdout=out,stderr=subprocess.PIPE,timeout=10)
                row.update(mode=mode,iteration=iteration,decode_status=proc.returncode,decode_error=proc.stderr.decode(errors='replace'),
                           valid=not row['failure'] and row['returncode']==0 and proc.returncode==0 and file_hash(decoded)==expected)
                rows.append(row);atomic_json(result/'measurements.json',rows)
                print(mode,iteration,row['valid'],row['decode_status'],flush=True)
        atomic_json(result/'summary.json',{'valid':all(r['valid'] for r in rows),'samples':len(rows)})
    finally:
        try:
            from provenance import verify
            verify(ROOT, result, Path(__file__))
        finally:
            remove_owned(owned)


if __name__=='__main__':
    from study import lock
    with lock():
        main()
