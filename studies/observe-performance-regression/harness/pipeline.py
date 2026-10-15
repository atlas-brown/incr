"""Small actual word-frequency development sequence, with opt-in runtime phases."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'studies/paper-size-benchmarks/harness'))
from common import WORK,atomic_json,remove_owned,supervise,file_hash
from provenance import fingerprint


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--id',required=True)
    p.add_argument('--mib',type=int,default=2)
    p.add_argument('--repetitions',type=int,default=1)
    p.add_argument('--profile',action='store_true')
    p.add_argument('--input',type=Path,help='Optional frozen local text input, up to 1 GiB')
    p.add_argument('--reference-binary',type=Path,help='Optional previous candidate, using the same helpers and Observe')
    a=p.parse_args()
    from provenance import validate_arguments
    validate_arguments(p, a)
    if a.reference_binary is not None and not a.reference_binary.is_file():
        p.error('Reference binary must exist')
    if a.input is not None and (not a.input.is_file() or a.input.stat().st_size>1024**3):
        p.error('Input must exist and be no larger than 1 GiB')
    result=ROOT/'studies/observe-performance-regression/results'/a.id
    result.mkdir(parents=True,exist_ok=False);fingerprint(ROOT,result,Path(__file__))
    reference_binary=None
    reference_hash=None
    if a.reference_binary is not None:
        reference_binary=result/'reference-incr'
        shutil.copy2(a.reference_binary,reference_binary)
        reference_hash=file_hash(reference_binary)
        atomic_json(result/'reference-binary.json',{'source':str(a.reference_binary.resolve()),'sha256':reference_hash})
    owned=Path(tempfile.mkdtemp(prefix='pipeline-probe-',dir=WORK));fixture=owned/'fixture';fixture.mkdir()
    profiles=owned/'profiles';profiles.mkdir()
    shutil.copytree(ROOT/'evaluation/benchmarks/word-freq/scripts',fixture/'scripts')
    line=b'one two three four five six seven eight nine ten\n'
    if a.input is None:
        (fixture/'input').write_bytes((line*(a.mib*1024**2//len(line)+1))[:a.mib*1024**2])
    else:
        shutil.copyfile(a.input,fixture/'input')
    input_hash=file_hash(fixture/'input')
    atomic_json(result/'input.json',{'source':str(a.input.resolve()) if a.input else 'generated text','bytes':(fixture/'input').stat().st_size,'sha256':input_hash})
    env={key:os.environ[key] for key in ('HOME','USER','LOGNAME') if key in os.environ}
    env.update(PATH=str(ROOT/'qualification/.venv/bin')+':/usr/local/bin:/usr/bin:/bin',LC_ALL='C',LANG='C',
               INPUT=str(fixture/'input'),INCR_EFFECT_POLICY='final',
               INCR_PYTHON=str(ROOT/'qualification/.venv/bin/python'),PYTHONDONTWRITEBYTECODE='1')
    if a.profile: env['INCR_PROFILE_DIR']=str(profiles)
    rows=[];refs={}
    worker=('import json,resource,subprocess,sys,time;start=time.perf_counter();'
            'p=subprocess.Popen(sys.argv[2:],close_fds=True);status=p.wait();'
            'elapsed=time.perf_counter()-start;r=resource.getrusage(resource.RUSAGE_CHILDREN);'
            'open(sys.argv[1],"w").write(json.dumps({"elapsed_sec":elapsed,"user_sec":r.ru_utime,"system_sec":r.ru_stime,"max_rss_kib":r.ru_maxrss,"voluntary_switches":r.ru_nvcsw,"involuntary_switches":r.ru_nivcsw,"output_blocks":r.ru_oublock}));sys.exit(status)')
    try:
        for repetition in range(a.repetitions):
            modes=['original','observe'] + (['observe-reference'] if reference_binary else [])
            if repetition % 2: modes.reverse()
            for mode in ['bash',*modes]:
                cache=owned/'cache'
                if cache.exists():remove_owned(cache)
                cache.mkdir();env['INCR_CACHE_DIR']=str(cache)
                top=ROOT.parent/'incr-main-qualification' if mode=='original' else ROOT
                env.update(INCR_TOP=str(top),INCR_SYS_PATH=str(top/'target/release/incr'),
                           INCR_TRY_PATH=str(top/'src/scripts/try.sh'),INCR_OBSERVE='1' if mode.startswith('observe') else '0',
                           INCR_OBSERVE_PATH=str(ROOT.parent/'observe/target/release/observe'))
                if mode=='observe-reference':env['INCR_SYS_PATH']=str(reference_binary)
                for script in ('wf.sh','top-n.sh'):
                    before=set(profiles.iterdir())
                    source=fixture/'scripts'/script
                    argv=['bash',str(source)] if mode=='bash' else ['bash',str(top/('src/incr.sh' if mode=='original' else 'incr.sh')),str(source)]
                    capture=owned/'capture'
                    if capture.exists():remove_owned(capture)
                    timing=owned/'timing.json'
                    row=supervise([sys.executable,'-c',worker,str(timing),*argv],cwd=fixture,env=env,capture=capture,
                                  timeout=30,reserve=8*1024**3,budget=32*1024**3)
                    resources=json.loads(timing.read_text()) if timing.is_file() else {}
                    row.update(mode=mode,script=script,repetition=repetition,command_resources=resources,command_elapsed_sec=resources.get('elapsed_sec'))
                    actual=[row['returncode'],row['stdout_sha256'],row['stderr_sha256']]
                    if mode=='bash':refs[script]=actual
                    row['valid']=not row['failure'] and actual==refs[script]
                    destination=result/f'{mode}-{script}-{repetition}-profiles';destination.mkdir()
                    for profile in set(profiles.iterdir())-before:shutil.copy2(profile,destination/profile.name)
                    rows.append(row);atomic_json(result/'measurements.json',rows)
                    print(mode,script,round(row['command_elapsed_sec'],5),row['valid'],flush=True)
        if file_hash(fixture/'input')!=input_hash:
            raise RuntimeError('Input changed during measurement')
        atomic_json(result/'summary.json',{'valid':all(row['valid'] for row in rows),'samples':len(rows),'mib':a.mib,'profiling':a.profile,'repetitions':a.repetitions})
    finally:
        try:
            from provenance import verify
            verify(ROOT, result, Path(__file__))
            if reference_binary is not None and file_hash(reference_binary)!=reference_hash:
                atomic_json(result/'summary.json',{'valid':False,'error':'Reference binary changed during measurement'})
                raise RuntimeError('Reference binary changed during measurement')
        finally:
            remove_owned(owned)


if __name__=='__main__':
    from study import lock
    with lock():
        main()
