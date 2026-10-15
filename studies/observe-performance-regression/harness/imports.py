"""Small real-SAM-import probe: negative lookups and artifact layout isolation."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'studies/paper-size-benchmarks/harness'))
from common import WORK,atomic_json,file_hash,remove_owned,supervise
from provenance import fingerprint,verify,validate_arguments
from cache_metadata import directory_summary
from study import lock


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--id',required=True)
    parser.add_argument('--repetitions',type=int,default=3)
    parser.add_argument('--reference-build',type=Path,required=True)
    args=parser.parse_args();validate_arguments(parser,args)
    reference=args.reference_build.resolve()
    sources={'incr':reference/'candidate/target/release/incr','observe':reference/'observe/target/release/observe'}
    if not all(path.is_file() for path in sources.values()):parser.error('Reference frozen build is missing')
    result=ROOT/'studies/observe-performance-regression/results'/args.id
    result.mkdir(parents=True,exist_ok=False);fingerprint(ROOT,result,Path(__file__))
    old=result/'reference';old.mkdir()
    for name,source in sources.items():shutil.copy2(source,old/name)
    old_hashes={name:file_hash(old/name) for name in sources}
    atomic_json(result/'reference.json',{'build':str(reference),'sha256':old_hashes})
    rows=[]
    worker=('import json,resource,subprocess,sys,time;start=time.perf_counter();'
            'p=subprocess.Popen(sys.argv[2:],close_fds=True);status=p.wait();elapsed=time.perf_counter()-start;'
            'r=resource.getrusage(resource.RUSAGE_CHILDREN);'
            'open(sys.argv[1],"w").write(json.dumps({"elapsed_sec":elapsed,"user_sec":r.ru_utime,"system_sec":r.ru_stime,"max_rss_kib":r.ru_maxrss}));sys.exit(status)')
    owned=Path(tempfile.mkdtemp(prefix='imports-',dir=WORK))
    try:
        for layout in ('siblings','isolated'):
            base=owned/layout;base.mkdir()
            scratch=base if layout=='siblings' else base/'scratch';scratch.mkdir(exist_ok=True)
            app=base/'fixture';app.mkdir()
            captures=scratch/'captures';captures.mkdir()
            temporary=app/'tmp' if layout=='siblings' else scratch/'tmp';temporary.mkdir()
            (app/'config/matplotlib').mkdir(parents=True)
            timing=scratch/'timing.json';timing.write_text('{}')
            script=app/'probe.py'
            script.write_text("import os,tempfile\nimport segment_anything\nos.path.realpath(__file__)\ntempfile.gettempdir()\nprint('import-ok')\n")
            env={key:os.environ[key] for key in ('HOME','USER','LOGNAME') if key in os.environ}
            env.update(PATH=str(ROOT/'qualification/.venv/bin')+':/usr/local/bin:/usr/bin:/bin',LC_ALL='C',LANG='C',
                       PYTHONDONTWRITEBYTECODE='1',PYTHONHASHSEED='42',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',
                       MPLBACKEND='Agg',MPLCONFIGDIR=str(app/'config/matplotlib'),TMPDIR=str(temporary))
            oracle=None
            for mode in ('bash','before','after'):
                cache=scratch/'cache'
                if cache.exists():remove_owned(cache)
                cache.mkdir()
                env['INCR_CACHE_DIR']=str(cache)
                for repetition in range(args.repetitions):
                    capture=base/'capture' if layout=='siblings' else captures/'capture'
                    if capture.exists():remove_owned(capture)
                    command=['python3',str(script)]
                    if mode!='bash':
                        binary=old/'incr' if mode=='before' else ROOT/'target/release/incr'
                        observer=old/'observe' if mode=='before' else ROOT.parent/'observe/target/release/observe'
                        command=[str(binary),'--effect-policy','final','--cache',str(cache),'--try',str(ROOT/'src/scripts/try.sh'),'--observe',str(observer),'--',*command]
                    row=supervise([sys.executable,'-c',worker,str(timing),*command],cwd=app,env=env,capture=capture,
                                  timeout=40,reserve=8*1024**3,budget=32*1024**3)
                    resources=json.loads(timing.read_text()) if timing.exists() else {}
                    actual=[row['returncode'],row['stdout_sha256'],row['stderr_sha256']]
                    if mode=='bash' and oracle is None:oracle=actual
                    row.update(layout=layout,mode=mode,repetition=repetition,command_resources=resources,
                               valid=not row['failure'] and actual==oracle and row['returncode']==0)
                    metadata=list(cache.glob('batch_*/data.incr'))
                    row['cache_entries']=len(metadata)
                    if mode=='after':
                        row['metadata']=[directory_summary(path) for path in metadata]
                    if not row['valid']:row['stderr_sample']=(capture/'stderr').read_text(errors='replace')[:4096]
                    rows.append(row);atomic_json(result/'measurements.json',rows)
                    print(layout,mode,repetition,round(resources.get('elapsed_sec',row['elapsed_sec']),4),row['valid'],len(metadata),flush=True)
        if any(file_hash(old/name)!=digest for name,digest in old_hashes.items()):raise RuntimeError('Reference binary changed')
        atomic_json(result/'summary.json',{'valid':all(row['valid'] for row in rows),'samples':len(rows)})
    finally:
        try:verify(ROOT,result,Path(__file__))
        finally:remove_owned(owned)


if __name__=='__main__':
    with lock():main()
