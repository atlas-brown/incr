"""Explicit serial live campaign using the maintained measurement supervisors.

Create fresh study scaffolds with init; smoke is bounded and independent of run.
run never overwrites/resumes attempts and publishes only after complete audits.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time

from common import ROOT, atomic_json, measurement_lock, mounts_under

SOURCE = ROOT / 'studies/paper-size-benchmarks'
MICRO = ROOT / 'studies/observe-strengths-microbench'
IMAGE = ROOT / 'studies/image-annotation-api-2026-10-16'
PYTHON = ROOT / 'qualification/.venv/bin/python'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths(name):
    if not re.fullmatch(r'live-[A-Za-z0-9_-]+', name):
        raise ValueError('Use a simple live- campaign name')
    return [ROOT/'studies'/name, ROOT/'studies'/(name+'-micro'), ROOT/'studies'/(name+'-image')]


def init(name):
    roots = paths(name)
    if any(p.exists() for p in roots):
        raise FileExistsError('Campaign already exists')
    for target, source in zip(roots, (SOURCE, MICRO, SOURCE)):
        target.mkdir()
        shutil.copytree(source/'harness', target/'harness', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        if source == MICRO:
            shutil.copytree(source/'scenarios', target/'scenarios')
            shutil.copy2(source/'PLAN.md', target/'PLAN.md')
        else:
            shutil.copy2(source/'manifest.json', target/'manifest.json')
            shutil.copytree(source/'reference', target/'reference')
        (target/'.gitignore').write_text('.work/\nresults/\nmeasurements/\n')
    shutil.copy2(IMAGE/'manifest.json', roots[2]/'manifest.json')
    for target in (roots[0], roots[2]):
        manifest=json.loads((target/'manifest.json').read_text())
        manifest['effect_policy']='live'
        atomic_json(target/'manifest.json',manifest)
    config = {'name': name, 'policy': 'live', 'created': time.time(),
              'expected': {'application':828, 'synthetic':2754, 'image':63},
              'service': name+'.service', 'supplemental':False,
              'head': subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
              'branch':subprocess.check_output(['git','-C',str(ROOT),'branch','--show-current'],text=True).strip(),
              'binaries':{str(p):digest(p) for p in (
                  ROOT/'target/release/incr', ROOT.parent/'observe/target/release/observe',
                  ROOT.parent/'incr-main-qualification/target/release/incr')}}
    changes=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only'],text=True).splitlines()
    changes += ['studies/LIVE_EVALUATION_PLAN.md',
                'studies/paper-size-benchmarks/harness/campaign.py',
                'studies/paper-size-benchmarks/harness/test_live.py']
    config['implementation_files']={p:digest(ROOT/p) for p in sorted(set(changes))}
    atomic_json(roots[0]/'campaign.json', config)
    print(roots[0])


class Campaign:
    def __init__(self, name, stage):
        self.app, self.micro, self.image = paths(name)
        self.config = json.loads((self.app/'campaign.json').read_text())
        self.stage = stage
        self.evidence = self.app/'results'/('controller-'+stage)
        self.evidence.mkdir(parents=True, exist_ok=False)
        self.lock = measurement_lock()
        self.env = dict(os.environ, INCR_BENCH_LOCK_FD=str(self.lock.fileno()),
                        INCR_BENCH_SERVICE=self.config['service'], PYTHONDONTWRITEBYTECODE='1',
                        PATH=str(PYTHON.parent)+':'+str(Path.home()/'.cargo/bin')+':/usr/local/bin:/usr/bin:/bin',
                        INCR_REPO_ROOT=str(ROOT))
        self.completed = []
        self.verify_binaries()

    def verify_binaries(self):
        if any(digest(Path(p)) != h for p,h in self.config['binaries'].items()):
            raise RuntimeError('Campaign binary fingerprint changed')

    def status(self, state, **extra):
        atomic_json(self.evidence/'status.json', dict(state=state, updated=time.time(),
                    completed=self.completed, **extra))

    def command(self, label, argv, env=None, timeout=86400):
        if shutil.disk_usage(self.app).free < 8*1024**3:
            raise RuntimeError('Campaign disk reserve exhausted')
        self.verify_binaries()
        self.status('running', step=label)
        logfile = self.evidence/(label+'.log')
        started = time.monotonic()
        with logfile.open('xb') as out:
            proc = subprocess.Popen(list(map(str,argv)), cwd=ROOT, env=env or self.env,
                                    stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                    pass_fds=(self.lock.fileno(),), start_new_session=True)
            try:
                while proc.poll() is None:
                    if time.monotonic()-started > timeout:
                        raise TimeoutError(label)
                    if shutil.disk_usage(self.app).free < 8*1024**3:
                        raise RuntimeError('Campaign disk reserve exhausted')
                    self.status('running', step=label, pid=proc.pid,
                                elapsed_sec=time.monotonic()-started,
                                free_bytes=shutil.disk_usage(self.app).free)
                    time.sleep(2)
                if proc.returncode:
                    raise RuntimeError(f'{label} exited {proc.returncode}; inspect {logfile}')
            finally:
                if proc.poll() is None:
                    os.killpg(proc.pid, signal.SIGTERM)
                    try:
                        proc.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait(timeout=10)
        self.completed.append(label)
        self.status('running', step=label, step_complete=True)

    def app_run(self, root, family, profile, repetitions, run_id, content=True):
        env = dict(self.env, INCR_BENCH_STUDY=str(root))
        if root == self.image:
            env['INCR_IMAGE_CLIENT_BIN'] = str(PYTHON.parent)
            if not (Path(env.get('LLM_USER_PATH','/nonexistent'))/'keys.json').is_file():
                raise RuntimeError('Private image credentials missing')
        runner = root/'harness/study.py'
        self.command(run_id+'-prepare', [PYTHON,runner,'prepare','--profile',profile,'--only',family],env)
        argv = [PYTHON,runner,'run','--profile',profile,'--only',family,'--repetitions',repetitions,
                '--run-id',run_id,'--effect-policy','live','--native-transform',
                '--assume-directory-access','--release-inputs']
        if content:
            argv.append('--content-validated-inputs')
        self.command(run_id,argv,env)
        run = root/'results'/run_id
        self.command(run_id+'-audit',[PYTHON,root/'harness/monitor.py',run],env,timeout=600)
        audit=json.loads((run/'monitor.json').read_text())
        if audit['health'] != 'ok' or audit['run_state'] != 'complete':
            raise RuntimeError('Terminal application audit failed')
        if repetitions == 3:
            self.command(run_id+'-report',[PYTHON,root/'harness/cohort_report.py',run,
                                         '--output',run/'paired-report.json'],env,timeout=600)
        self.command(run_id+'-cleanup',[PYTHON,root/'harness/cleanup.py','--apply','--build',run_id],env,timeout=600)
        return run

    def micro_run(self, run_id, diagnostic=False):
        env = dict(self.env, INCR_MICRO_STUDY=str(self.micro))
        argv=[PYTHON,self.micro/'harness/study.py','--run-id',run_id,'--effect-policy','live']
        if diagnostic:
            argv += ['--diagnostic','--scales','small','--repetitions','1','--counts','1,24,128','--rows','1,128,1024']
        self.command(run_id,argv,env)
        run=self.micro/'measurements'/run_id
        if diagnostic:
            self.command(run_id+'-backend-audit',[PYTHON,self.micro/'harness/audit_profiles.py',run],env,600)
        else:
            self.command(run_id+'-audit',[PYTHON,self.micro/'harness/audit.py','--require-full',
                          '--backend-pilot',self.micro/'measurements/smoke-live',run],env,600)
        return run

    def smoke(self):
        self.app_run(self.app,'word-freq','min',1,'smoke-word-freq')
        self.micro_run('smoke-live', diagnostic=True)
        self.app_run(self.image,'image-annotation','min',1,'smoke-image',content=False)
        self.status('complete', scope='Minimal independent smoke; not full measurement evidence')

    def run(self):
        smoke=json.loads((self.app/'results/controller-smoke/status.json').read_text())
        if smoke['state'] != 'complete':
            raise RuntimeError('Smoke gate incomplete')
        manifest=json.loads((self.app/'manifest.json').read_text())
        runs=[]
        for family in manifest['benchmarks']:
            name=family['name']
            runs.append(self.app_run(self.app,name,'paper',3,'paper-'+name))
        micro=self.micro_run('full-live')
        image=self.app_run(self.image,'image-annotation','paper',3,'paper-image',content=False)
        runs.append(image)
        expected=sum(json.loads((p/'summary.json').read_text())['valid_invocations'] for p in runs)
        if expected != 891:
            raise RuntimeError('Application matrix coverage mismatch')
        self.export(runs,micro)
        self.cleanup()
        self.status('complete', application_invocations=891, synthetic_invocations=2754)
        self.publish()

    def cleanup(self):
        receipt=[]
        for root in (self.app,self.micro,self.image):
            work=root/'.work'
            if mounts_under(work) or list(work.rglob('*.recovery')):
                raise RuntimeError('Mounted/recovery state requires inspection')
            # Whole campaign workspace is newly owned; result evidence is outside it.
            if work.is_symlink():
                raise RuntimeError('Unexpected workspace link')
            if work.exists():
                shutil.rmtree(work)
                receipt.append(str(work))
        atomic_json(self.app/'completed-evidence/cleanup.json',
                    {'removed_owned_workspaces':receipt,'free_bytes':shutil.disk_usage(self.app).free})

    def publish(self):
        """Publish only this completed campaign and its unchanged implementation."""
        def git(*args):
            return subprocess.check_output(['git','-C',str(ROOT),*args],text=True,timeout=180).strip()
        if git('rev-parse','HEAD') != self.config['head'] or git('branch','--show-current') != self.config['branch']:
            raise RuntimeError('Repository moved during measurements; results retained, publication stopped')
        if git('diff','--cached','--name-only'):
            raise RuntimeError('Unrelated staged changes; results retained, publication stopped')
        for name,h in self.config['implementation_files'].items():
            if digest(ROOT/name) != h:
                raise RuntimeError('Implementation changed; publication stopped: '+name)
        owned=list(self.config['implementation_files'])
        owned += [str(p.relative_to(ROOT)) for root in (self.app,self.micro,self.image)
                  for p in root.rglob('*') if p.is_file() and not p.is_symlink()
                  and not {'results','measurements','.work','__pycache__'}.intersection(p.relative_to(root).parts)]
        pattern=re.compile(rb'sk-(?:proj-)?[A-Za-z0-9_-]{30,}')
        for name in owned:
            file=ROOT/name
            if file.stat().st_size > 90*1024**2:
                raise RuntimeError('Artifact too large for Git; publication stopped: '+name)
            if pattern.search(file.read_bytes()):
                raise RuntimeError('Possible credential in artifact; publication stopped')
        for root in (self.app,self.micro,self.image):
            for file in root.rglob('*'):
                if file.is_file() and file.suffix not in ('.gz',) and '.work' not in file.parts:
                    if pattern.search(file.read_bytes()):
                        raise RuntimeError('Possible credential in raw evidence; publication stopped')
        git('add','--',*sorted(set(owned)))
        git('diff','--cached','--check')
        git('commit','-m','Record isolated live-policy evaluations and serial background orchestration')
        commit=git('rev-parse','HEAD')
        git('push','origin','HEAD:refs/heads/'+self.config['branch'])
        remote=git('ls-remote','origin','refs/heads/'+self.config['branch']).split()[0]
        if remote != commit:
            raise RuntimeError('Remote verification failed')
        atomic_json(self.evidence/'publication.json',{'commit':commit,'remote_verified':True})

    def export(self, runs, micro):
        destination=self.app/'completed-evidence'
        destination.mkdir(exist_ok=False)
        rows=[]
        for run in runs:
            value=json.loads((run/'paired-report.json').read_text())
            rows += value['families']
        atomic_json(destination/'application-statistics.json',rows)
        for filename in ('summary.json','audit.json','timings.csv','REPORT.md'):
            shutil.copy2(micro/filename,destination/('synthetic-'+filename))
        (destination/'README.md').write_text(
            '# Live effect-policy measurements\n\n891 application and 2,754 synthetic invocations. '
            'Three paired repetitions; Bash/original/Observe-live. Image API remains a separate '
            'payload-validated cohort. Cold means an empty Incr cache. Raw evidence includes '
            'all smoke runs, separately labelled; they are not pooled into final timings.\n')
        catalogs={}
        for label,root,subdir in [('applications',self.app,'results'),('images',self.image,'results'),
                                  ('synthetics',self.micro,'measurements')]:
            members={}
            archive=destination/(label+'.tar.gz')
            with tarfile.open(archive,'w:gz') as out:
                for file in sorted((root/subdir).rglob('*')):
                    if file.is_symlink():
                        raise RuntimeError('Unexpected evidence link')
                    if file.is_file() and 'controller-run' not in file.parts:
                        member=str(file.relative_to(root))
                        members[member]=digest(file)
                        out.add(file,arcname=member,recursive=False)
            with tarfile.open(archive) as source:
                restored={m.name:hashlib.sha256(source.extractfile(m).read()).hexdigest() for m in source}
            if restored != members:
                raise RuntimeError('Archive round-trip mismatch')
            catalogs[label]={'sha256':digest(archive),'members':members}
        atomic_json(destination/'catalog.json',catalogs)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=('init','smoke','run'))
    p.add_argument('--name',required=True)
    args=p.parse_args()
    if args.stage == 'init':
        return init(args.name)
    campaign=Campaign(args.name,args.stage)
    try:
        getattr(campaign,args.stage)()
    except BaseException as error:
        campaign.status('failed', error=str(error))
        raise
    finally:
        campaign.lock.close()


if __name__ == '__main__':
    def stop(*_):
        raise KeyboardInterrupt('Campaign stop requested')
    signal.signal(signal.SIGTERM,stop)
    main()
