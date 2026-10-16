"""Queue the opt-in live API study behind synthetic timings; keep secrets external."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

STUDY = Path(__file__).resolve().parent
ROOT = STUDY.parents[1]
WORK = STUDY / '.work'


def status(state, **extra):
    pending = STUDY / 'status.pending'
    pending.write_text(json.dumps(dict(state=state, updated_unix=time.time(), **extra), indent=2)+'\n')
    pending.replace(STUDY / 'status.json')


def command(argv, **kwargs):
    subprocess.run([str(x) for x in argv], check=True, **kwargs)


def main():
    os.environ['PATH'] = str(Path.home()/'.cargo/bin') + ':' + os.environ.get('PATH', '/usr/bin:/bin')
    credentials = Path(os.environ['LLM_USER_PATH'])
    lock = None
    minimum_run = os.environ.get('INCR_IMAGE_MIN_RUN', 'minimum-01')
    try:
        status('queued', wait_for='incr-strengths-microbench-final.service')
        while subprocess.run(['systemctl','--user','is-active','--quiet',
                              'incr-strengths-microbench-final.service']).returncode == 0:
            time.sleep(30)
        # Hold the synthetic study lock too, preventing a new timed run overlapping.
        lock_path = ROOT/'studies/observe-strengths-microbench/.work/lock'
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock = lock_path.open('a+')
        fcntl.flock(lock, fcntl.LOCK_EX)
        status('setup')
        WORK.mkdir(exist_ok=True)
        client = WORK/'client'
        command([sys.executable,'-m','venv',client])
        command([client/'bin/python','-m','pip','install','--disable-pip-version-check','llm==0.36'])
        with (STUDY/'client-packages.txt').open('w') as output:
            command([client/'bin/python','-m','pip','freeze'], stdout=output)
        # Freeze the maintained runner at queue time, not after a later edit.
        harness = WORK/'queued-harness'
        command([ROOT/'qualification/.venv/bin/python','-m','unittest','test_image_annotation'], cwd=harness)
        env = dict(os.environ, INCR_BENCH_STUDY=str(STUDY), INCR_IMAGE_CLIENT_BIN=str(client/'bin'))
        python = ROOT/'qualification/.venv/bin/python'
        command([python,harness/'study.py','prepare','--profile','min','--only','image-annotation'],env=env)
        status('minimum-validation', results=f'results/{minimum_run}/status.json')
        command([python,harness/'study.py','run','--profile','min','--only','image-annotation',
                 '--repetitions','1','--run-id',minimum_run,'--native-transform',
                 '--assume-directory-access'],env=env)
        command([python,harness/'study.py','prepare','--profile','paper','--only','image-annotation'],env=env)
        status('running', results='results/paper-01/status.json')
        command([python,harness/'study.py','run','--profile','paper','--only','image-annotation',
                 '--repetitions','3','--run-id','paper-01','--native-transform',
                 '--assume-directory-access'],env=env)
        status('complete', results='results/paper-01/summary.json')
    except BaseException as error:
        status('failed', error_type=type(error).__name__,
               detail='Inspect console.log and per-run status; no automatic retry or promotion of failed samples.')
        raise
    finally:
        # This directory was supplied by the launcher and contains only this key.
        if credentials.parent == Path('/tmp') and credentials.name.startswith('incr-image-api-'):
            shutil.rmtree(credentials, ignore_errors=True)
        if lock is not None:
            lock.close()


if __name__ == '__main__':
    main()
