"""Real framework imports: diagnose cross-process temporary-directory invalidation."""
import argparse
import hashlib
import shutil
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'studies/paper-size-benchmarks/harness'))
from common import WORK,atomic_json,remove_owned,supervise,file_hash
from study import lock
from provenance import fingerprint,verify,validate_arguments
from cache_metadata import directory_summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id',required=True)
    parser.add_argument('--trace-tensorflow',action='store_true',
                        help='Also trace the interfering TensorFlow import; suitable for diagnostic CPU profiling')
    parser.add_argument('--only-explicit',action='store_true',help='Test only the isolated compiler-cache layout')
    parser.add_argument('--observer',type=Path,default=ROOT.parent/'observe/target/release/observe')
    parser.add_argument('--blas-threads',type=int,help='Explicit OpenBLAS worker count for all probe stages')
    args=parser.parse_args();validate_arguments(parser,args)
    if not args.observer.is_file():parser.error('Observe binary must exist')
    if args.blas_threads is not None and not 1 <= args.blas_threads <= 64:parser.error('Use 1--64 OpenBLAS workers')
    result=ROOT/'studies/observe-performance-regression/results'/args.id
    result.mkdir(parents=True,exist_ok=False);fingerprint(ROOT,result,Path(__file__))
    observer=result/'observe-binary'
    shutil.copy2(args.observer,observer)
    if file_hash(observer)!=file_hash(args.observer):raise RuntimeError('Observe binary changed while copying')
    atomic_json(result/'configuration.json',{'observer_source':str(args.observer.resolve()),
        'observer_sha256':file_hash(observer),'trace_tensorflow':args.trace_tensorflow,
        'blas_threads':args.blas_threads,'only_explicit':args.only_explicit})
    owned=Path(tempfile.mkdtemp(prefix='temp-interference-',dir=WORK))
    rows=[]
    try:
        for variant in (('explicit-torch-cache',) if args.only_explicit else ('default','explicit-torch-cache')):
            base=owned/variant;app=base/'fixture';app.mkdir(parents=True)
            scratch=base/'runner';scratch.mkdir()
            for name in ('tmp','config/matplotlib','config/torch'):(app/name).mkdir(parents=True,exist_ok=True)
            script=app/'probe.py'
            script.write_text("import os,tempfile\nimport segment_anything\nos.path.realpath(__file__)\ntempfile.gettempdir()\nprint('sam-import-ok')\n")
            env={key:os.environ[key] for key in ('HOME','USER','LOGNAME') if key in os.environ}
            env.update(PATH=str(ROOT/'qualification/.venv/bin')+':/usr/local/bin:/usr/bin:/bin',
                LC_ALL='C',LANG='C',PYTHONDONTWRITEBYTECODE='1',PYTHONHASHSEED='42',
                OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',TF_NUM_INTRAOP_THREADS='2',TF_NUM_INTEROP_THREADS='2',
                MPLBACKEND='Agg',MPLCONFIGDIR=str(app/'config/matplotlib'),TMPDIR=str(app/'tmp'))
            if variant=='explicit-torch-cache':env['TORCHINDUCTOR_CACHE_DIR']=str(app/'config/torch')
            if args.blas_threads is not None:env['OPENBLAS_NUM_THREADS']=str(args.blas_threads)
            cache=scratch/'cache';cache.mkdir();env['INCR_CACHE_DIR']=str(cache)
            atomic_json(result/f'{variant}-environment.json',env)
            oracle=None
            for stage in ('native','cold','tensorflow','warm'):
                capture=scratch/'capture';remove_owned(capture)
                command=['python3',str(script)]
                if stage=='tensorflow':
                    command=['python3','-c',"import tensorflow,tempfile;tempfile.gettempdir();print('tensorflow-import-ok')"]
                if stage in ('cold','warm') or (stage=='tensorflow' and args.trace_tensorflow):
                    command=[str(ROOT/'target/release/incr'),'--effect-policy','final',
                        '--observe',str(observer),
                        '--try',str(ROOT/'src/scripts/try.sh'),'--cache',str(cache),'--',*command]
                row=supervise(command,cwd=app,env=env,capture=capture,timeout=60,
                              reserve=8*1024**3,budget=32*1024**3)
                actual=[row['returncode'],row['stdout_sha256'],row['stderr_sha256']]
                if stage=='native':oracle=actual
                row.update(variant=variant,stage=stage,
                    valid=not row['failure'] and row['returncode']==0 and (
                        (row['stdout_sha256']==hashlib.sha256(b'tensorflow-import-ok\n').hexdigest())
                        if stage=='tensorflow' else actual==oracle),
                    metadata=[directory_summary(path) for path in cache.glob('batch_*/data.incr')])
                if not row['valid']:row['stderr_sample']=(capture/'stderr').read_text(errors='replace')[:4096]
                rows.append(row);atomic_json(result/'measurements.json',rows)
                print(variant,stage,round(row['elapsed_sec'],4),row['valid'],flush=True)
                if not row['valid']:raise RuntimeError('Framework import/status mismatch')
        if file_hash(observer)!=file_hash(args.observer):raise RuntimeError('Observe source/copy binary changed during probe')
        atomic_json(result/'summary.json',{'valid':all(row['valid'] for row in rows),'samples':len(rows)})
    finally:
        try:verify(ROOT,result,Path(__file__))
        finally:
            if list(owned.glob('*/runner/cache/*.recovery')):raise RuntimeError('Recovery retained; inspect probe state')
            remove_owned(owned)


if __name__=='__main__':
    with lock():main()
