"""Modular paper-sized study: doctor, prepare, run, report, status, launch.

No automatic min-to-paper transition. Background launch is an explicit command.
All mutating/measurement commands share one nonblocking exclusive study lock.
"""
import argparse
import csv
import fcntl
import hashlib
import http.server
import json
import math
import os
from pathlib import Path
import platform
import shutil
import signal
import socketserver
import statistics
import subprocess
import sys
import tarfile
import threading
import time
from datetime import datetime, timezone

from common import (GIB, ROOT, STUDY, WORK, SCRATCH, allocated_bytes, atomic_json, file_hash,
                    mounts_under, remove_owned, supervise)
from prepare import SOURCE, prepare, check_space
from validate import compare

MODES = ('bash', 'original', 'observe')
HARNESS = Path(__file__).resolve().parent
MANIFEST = json.loads((STUDY / 'manifest.json').read_text())
PYTHON = ROOT / 'qualification/.venv/bin/python'
ORIGINAL = ROOT.parent / 'incr-main-qualification'


def revision(path):
    return subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()


def now():
    return datetime.now(timezone.utc).isoformat()


def lock():
    WORK.mkdir(exist_ok=True)
    stream = (WORK / 'study.lock').open('a+')
    try:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        stream.close()
        raise RuntimeError('Another study command is active; measurements never overlap')
    return stream


def selected(names):
    requested = set(names.split(',')) if names else {b['name'] for b in MANIFEST['benchmarks']}
    known = {b['name'] for b in MANIFEST['benchmarks']}
    if not requested <= known:
        raise ValueError(f'Unknown benchmarks: {requested - known}')
    return [b for b in MANIFEST['benchmarks'] if b['name'] in requested]


def doctor(build=False):
    required = ['bash', 'git', 'strace', 'mergerfs', 'ffmpeg', 'openssl', 'samtools',
                'gnuplot', 'col', 'mogrify', 'wget', 'unzip', 'tar', 'cc', '/usr/bin/time']
    missing = [tool for tool in required if not shutil.which(tool)]
    if missing:
        raise RuntimeError(f'Missing dependencies: {missing}')
    if not Path('/dev/fuse').exists():
        raise RuntimeError('FUSE device missing')
    subprocess.run(['sudo', '-n', 'true'], check=True, timeout=5)
    if revision(ORIGINAL) != MANIFEST['original_revision']:
        raise RuntimeError('Original checkout is not the pinned revision')
    original_patch = subprocess.check_output(['git', '-C', str(ORIGINAL), 'diff', 'HEAD', '--',
                                              'src', 'Cargo.toml', 'Cargo.lock'], timeout=15)
    expected_patch = (STUDY / 'reference/original-minimal-fixes.patch').read_bytes()
    if original_patch != expected_patch:
        raise RuntimeError('Original runtime differs from the reviewed minimal baseline patch')
    subprocess.run([str(PYTHON), '-c',
                    'import libdash,libbash,shasta,numpy,torch,tensorflow,cv2,matplotlib,segment_anything'],
                   check=True, timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not Path('/usr/share/dict/words').is_file():
        raise RuntimeError('Spelling dictionary missing')
    fonts = WORK / 'font-cache'
    fonts.mkdir(exist_ok=True)
    subprocess.run([str(PYTHON), '-c', 'import matplotlib.font_manager'],
                   env=dict(os.environ, MPLCONFIGDIR=str(fonts), MPLBACKEND='Agg'),
                   check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if build:
        for repo in (ORIGINAL, ROOT.parent / 'observe', ROOT):
            subprocess.run(['cargo', 'build', '--release', '--locked'], cwd=repo,
                           check=True, timeout=900)
    result = {'time': now(), 'platform': platform.platform(), 'cpu': Path('/proc/cpuinfo').read_text(),
              'meminfo': Path('/proc/meminfo').read_text(), 'free_bytes': shutil.disk_usage(WORK).free,
              'repositories': {str(repo): revision(repo) for repo in (ORIGINAL, ROOT, ROOT.parent / 'observe')},
              'original_baseline_patch': original_patch.decode(),
              'source_fingerprints': {str(repo): inventory(repo / 'src') for repo in (ORIGINAL, ROOT, ROOT.parent / 'observe')},
              'dictionary_sha256': file_hash('/usr/share/dict/words'),
              'packages': subprocess.check_output([str(PYTHON), '-m', 'pip', 'freeze'], text=True, timeout=60),
              'tool_versions': {}}
    for tool, args in {'bash': ['--version'], 'strace': ['--version'], 'mergerfs': ['--version'],
                       'samtools': ['--version'], 'ffmpeg': ['-version'], 'gnuplot': ['--version'],
                       'openssl': ['version'], 'cargo': ['--version'], 'sort': ['--version']}.items():
        proc = subprocess.run([tool, *args], capture_output=True, text=True, timeout=15, errors='replace')
        result['tool_versions'][tool] = (proc.stdout + proc.stderr)[:8192]
    atomic_json(WORK / 'doctor.json', result)
    return result


def archive_sources(source, destination):
    """Preserve new files too: git diff alone cannot reproduce a dirty build."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    def keep(member):
        path = Path(member.name)
        return None if '__pycache__' in path.parts or path.suffix == '.pyc' else member
    with tarfile.open(destination, 'w:gz', dereference=False) as archive:
        paths = [source/name for name in ('src', 'Cargo.toml', 'Cargo.lock', 'build.rs')]
        paths.extend(sorted(source.glob('*.sh')))
        for path in paths:
            if path.exists():
                archive.add(path, arcname=path.name, filter=keep)


def freeze(run):
    build = WORK / 'builds' / run.name
    build.mkdir(parents=True, exist_ok=False)
    sources = {}
    for source, name in ((ROOT, 'candidate'), (ORIGINAL, 'original'), (ROOT.parent/'observe', 'observe')):
        before = inventory(source/'src')
        archive = run/'sources'/f'{name}.tar.gz'
        archive_sources(source, archive)
        if before != inventory(source/'src'):
            raise RuntimeError(f'Source changed while archiving {source}')
        sources[name] = {'repository':str(source), 'revision':revision(source),
                         'archive':str(archive.relative_to(run)), 'sha256':file_hash(archive)}
    paths = []
    for source, name in ((ROOT, 'candidate'), (ORIGINAL, 'original')):
        dest = build / name
        shutil.copytree(source / 'src/scripts', dest / 'src/scripts',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        binary = dest / 'target/release/incr'
        binary.parent.mkdir(parents=True)
        shutil.copy2(source / 'target/release/incr', binary)
        wrapper = source / ('incr.sh' if name == 'candidate' else 'src/incr.sh')
        shutil.copy2(wrapper, dest / 'incr.sh')
        paths.append(dest)
    observer = build / 'observe/target/release/observe'
    observer.parent.mkdir(parents=True)
    shutil.copy2(ROOT.parent / 'observe/target/release/observe', observer)
    snapshots = build / 'benchmarks'
    snapshots.mkdir()
    for b in MANIFEST['benchmarks']:
        source = SOURCE / b['name'] / 'scripts'
        shutil.copytree(source, snapshots / b['name'],
                        ignore=shutil.ignore_patterns('node_modules', '__pycache__', '*.pyc', '*.incr_orig', 'incr_script_*'))
    shutil.copytree(HARNESS, build / 'harness', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    subprocess.run(['cc', '-O2', '-Wall', '-Wextra', '-Werror', str(build / 'harness/fdguard.c'),
                    '-o', str(build / 'fdguard')], check=True, timeout=30)
    hashes = {str(p.relative_to(build)): file_hash(p) for p in sorted(build.rglob('*')) if p.is_file()}
    atomic_json(run / 'frozen-build.json', {'directory': str(build), 'sha256': hashes, 'source_archives': sources,
                                          'revisions': {str(p): revision(p) for p in (ROOT, ORIGINAL, ROOT.parent / 'observe')}})
    return build


def inventory(directory):
    return {str(p.relative_to(directory)): file_hash(p) for p in sorted(directory.rglob('*'))
            if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def cache_inventory():
    # Entry metadata is directly below each cache entry. Never recurse through
    # sandbox mounts left by a cancelled original-Incr child.
    result = {}
    root = SCRATCH/'cache'
    if not root.is_dir(): return result
    for directory in root.iterdir():
        if directory.is_symlink() or not directory.is_dir(): continue
        for name in ('data','data.incr'):
            path = directory/name
            if path.is_file() and not path.is_symlink():
                metadata = path.stat()
                result[str(path.relative_to(root))] = [metadata.st_mtime_ns,metadata.st_size]
    return result


def fixture(name, data, build, profile):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    target = WORK / 'fixture'
    remove_owned(target)
    target.mkdir()
    shutil.copytree(build / 'benchmarks' / name, target / 'scripts')
    shutil.copytree(data / 'inputs', target / 'inputs')
    (target / 'outputs/statistics').mkdir(parents=True)
    (target / 'tmp').mkdir()
    if name == 'bio':
        shutil.copy2(SOURCE / 'bio/Gene_locs.txt', target / 'Gene_locs.txt')
        shutil.copy2(SOURCE / 'bio/Gene_locs.txt', target / 'scripts/Gene_locs.txt')
    if name == 'dpt':
        (target / 'inputs/models').symlink_to(SOURCE / 'dpt/inputs/models', target_is_directory=True)
        (target / 'inputs/dpt').mkdir()
        (target / 'config/torch').mkdir(parents=True)
    # A fixed font cache is setup state, not a changing per-process dependency.
    if name in ('bio', 'dpt'):
        shutil.copytree(WORK / 'font-cache', target / 'config/matplotlib')
    return target


def environment(name, profile, fixture, build):
    # Explicit environment prevents unrelated UI/session changes entering keys.
    env = {key: os.environ[key] for key in ('HOME', 'USER', 'LOGNAME') if key in os.environ}
    env.update(PATH=str(PYTHON.parent) + ':/usr/local/bin:/usr/bin:/bin', LC_ALL='C', LANG='C',
               PYTHONDONTWRITEBYTECODE='1', PYTHONHASHSEED='42', MPLBACKEND='Agg',
               MPLCONFIGDIR=str(fixture / 'config/matplotlib'),
               OMP_NUM_THREADS='8' if name == 'dpt' else '2', MKL_NUM_THREADS='8' if name == 'dpt' else '2',
               TF_NUM_INTRAOP_THREADS='2', TF_NUM_INTEROP_THREADS='2',
               TMPDIR=str(fixture / 'tmp'), RUN_SIZE='min' if profile == 'min' else 'paper',
               mode='study', MODE='study', BENCHMARK_DIR=str(fixture), OUTPUT_DIR=str(fixture / 'outputs'),
               OUT=str(fixture / 'outputs'), INCR_CACHE_DIR=str(SCRATCH / 'cache'),
               INCR_PYTHON=str(PYTHON), INCR_EFFECT_POLICY='final')
    inp = fixture / 'inputs'
    if name == 'file-mod': env['IN'] = str(inp / 'songs')
    if name == 'word-freq': env['INPUT'] = str(inp / 'text.txt')
    if name in ('nlp-ngrams', 'nlp-uppercase', 'poet', 'spell'):
        env['IN'] = str(inp / 'books')
        env['ENTRIES'] = '1' if profile == 'min' or name in ('nlp-ngrams', 'nlp-uppercase') else '115916'
    if name == 'covid': env['INPUT'] = str(inp / 'covid.csv')
    if name == 'weather':
        env.update(INPUT=str(inp / 'temperatures.txt'), input_file=str(inp / 'temperatures.txt'),
                   statistics_dir=str(fixture / 'outputs/statistics'))
    if name == 'nginx-analysis': env['INPUT'] = str(inp / 'logs')
    if name == 'beginner': env['IN'] = str(inp / 'logs/log0')
    if name == 'unixfun': env['INPUT'] = str(inp / 'chess.txt')
    if name == 'bio':
        env['IN'] = str(inp / 'bio')
        env['IN_NAME'] = str(inp / 'bio' / ('input_min.txt' if profile == 'min' else 'input.txt'))
    if name == 'dpt':
        env['IMG_DIR'] = str(inp)
        # Framework cache state must not share tempfile's mutable namespace.
        # Applied identically to all modes and recreated for every sequence.
        env['TORCHINDUCTOR_CACHE_DIR'] = str(fixture / 'config/torch')
    return env


def resources(path):
    if not path.exists():
        return {}
    for row in path.read_text(errors='replace').splitlines():
        if row.startswith('{'):
            try:
                return json.loads(row)
            except ValueError:
                pass
    return {'parse_error': path.read_text(errors='replace')[:8192]}


class Mirror:
    def __init__(self, data):
        self.data = data
        self.server = self.thread = None

    def __enter__(self):
        directory = str(self.data / 'inputs')
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)
            def log_message(self, *args):
                pass
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Quiet)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return f'http://127.0.0.1:{self.server.server_port}/images.zip'

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def record_event(run, event):
    event['time'] = now()
    with (run / 'events.jsonl').open('a') as stream:
        stream.write(json.dumps(event) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def execute_sequence(run, b, mode, repetition, args, build, data, references, mirror_url=None):
    name = b['name']
    sequence = run / 'sequences' / f'{name}.{mode}.{repetition}'
    if (sequence / 'complete.json').is_file():
        return json.loads((sequence / 'complete.json').read_text())
    # An interrupted sequence is rerun from empty state, preserving old evidence.
    if sequence.exists():
        sequence.rename(sequence.with_name(sequence.name + '.interrupted.' + str(time.time_ns())))
    sequence.mkdir(parents=True)
    remove_owned(SCRATCH / 'cache')
    active = fixture(name, data, build, args.profile)
    if mirror_url:
        for path in (active / 'scripts').glob('dpt_*.sh'):
            path.write_text(path.read_text().replace('https://atlas-group.cs.brown.edu/data/dpt/dpt.zip', mirror_url))
    initial_inputs = inventory(active / 'inputs')
    initial_sources = inventory(active / 'scripts')
    env = environment(name, args.profile, active, build)
    if getattr(args, 'native_transform', False):
        env['INCR_NATIVE_TRANSFORM'] = '1'
    env['INCR_TOP'] = str(build / ('original' if mode == 'original' else 'candidate'))
    env['INCR_SYS_PATH'] = str(Path(env['INCR_TOP']) / 'target/release/incr')
    env['INCR_TRY_PATH'] = str(Path(env['INCR_TOP']) / 'src/scripts/try.sh')
    env['INCR_OBSERVE_PATH'] = str(build / 'observe/target/release/observe')
    env['INCR_OBSERVE'] = '1' if mode == 'observe' else '0'
    atomic_json(sequence / 'setup.json', {'environment': env, 'input_inventory': initial_inputs,
                                        'script_inventory': initial_sources, 'mirror_url': mirror_url,
                                        'frozen_build': str(build)})
    all_records = []
    try:
        for index, script in enumerate(b['scripts']):
            capture = SCRATCH / 'capture'
            remove_owned(capture)
            capture.mkdir()
            command = (['bash', str(active / 'scripts' / script)] if mode == 'bash' else
                       ['bash', str(Path(env['INCR_TOP']) / 'incr.sh'), str(active / 'scripts' / script)])
            timed = ['/usr/bin/time', '-f',
                '{"user_sec":%U,"system_sec":%S,"max_rss_kib":%M,"major_faults":%F,"minor_faults":%R,"voluntary_switches":%w,"involuntary_switches":%c,"filesystem_inputs":%I,"filesystem_outputs":%O,"exit_status":%x}',
                '-o', str(capture / 'resources.json'), '--', str(build / 'fdguard'), *command]
            status = {'state': 'running', 'run': run.name, 'profile': args.profile, 'benchmark': name,
                      'mode': mode, 'repetition': repetition, 'script': script, 'index': index,
                      'total': len(b['scripts']), 'updated': now(), 'pid': os.getpid()}
            def heartbeat(extra):
                atomic_json(run / 'status.json', dict(status, **extra, updated=now()))
            heartbeat({})
            print(f'{now()} RUN {name} {mode} repetition={repetition} {script}', flush=True)
            cache_before = cache_inventory()
            record = supervise(timed, cwd=active, env=env, capture=capture,
                               timeout=b[f'timeout_{args.profile}'], reserve=args.reserve_gib * GIB,
                               budget=args.work_budget_gib * GIB, heartbeat=heartbeat)
            cache_after = cache_inventory()
            record.update(benchmark=name, mode=mode, repetition=repetition, script=script, index=index,
                          profile=args.profile, resources=resources(capture / 'resources.json'),
                          cache_bytes=allocated_bytes(SCRATCH / 'cache'),
                          private_tmp_bytes=allocated_bytes(active / 'tmp'),
                          cache_entries_before=len(cache_before), cache_entries_after=len(cache_after),
                          cache_entries_retained=sum(cache_before.get(p) == v for p, v in cache_after.items()),
                          cache_entries_changed=sum(cache_before.get(p) != v for p, v in cache_after.items()))
            if 'user_sec' not in record['resources']:
                record['failure'] = record['failure'] or 'missing-resource-measurements'
                atomic_json(capture / 'supervisor.json', record)
            validation_file = capture / 'validation.json'
            checked = supervise([str(PYTHON), str(build / 'harness/validation_worker.py'),
                                 str(active), str(capture), name, script, str(validation_file)],
                                cwd=STUDY, env=dict(os.environ, INCR_BENCH_STUDY=str(STUDY)), capture=SCRATCH / 'validation-capture',
                                timeout=600, reserve=args.reserve_gib * GIB, budget=args.work_budget_gib * GIB)
            if checked['failure'] or checked['returncode'] != 0 or not validation_file.is_file():
                record['valid'] = False
                record['problems'] = ['validator failed', checked]
                record['validator_stderr'] = (SCRATCH / 'validation-capture/stderr').read_bytes()[:65536].decode(errors='replace')
            else:
                validated = json.loads(validation_file.read_text())
                problems = validated['problems']
                key = (name, repetition, script)
                if mode == 'bash':
                    references[key] = validated
                    atomic_json(run / 'references' / name / f'{repetition}.{script}.json', validated)
                else:
                    if key not in references:
                        ref_path = run / 'references' / name / f'{repetition}.{script}.json'
                        references[key] = json.loads(ref_path.read_text())
                    problems += compare(references[key], validated)
                record.update(valid=not problems, problems=problems, validation=validated)
            # Freeze complete invocation evidence before deleting large captures.
            atomic_json(sequence / f'{index:02d}.{script}.json', record)
            record_event(run, {'event': 'invocation', 'benchmark': name, 'mode': mode,
                              'repetition': repetition, 'script': script, 'valid': record['valid'],
                              'elapsed_sec': record['elapsed_sec'], 'problems': record['problems']})
            all_records.append(record)
            print(f'{"PASS" if record["valid"] else "FAIL"} {record["elapsed_sec"]:.3f}s {record["problems"]}', flush=True)
            if not record['valid']:
                diagnostics = sequence / 'failure-capture'
                diagnostics.mkdir()
                if record.get('validator_stderr'):
                    (diagnostics / 'validator-stderr.txt').write_text(record['validator_stderr'])
                atomic_json(diagnostics / 'output-inventory.json', {str(p.relative_to(active)): {'bytes': p.stat().st_size, 'sha256': file_hash(p)}
                    for p in active.rglob('*') if p.is_file() and not p.is_symlink() and 'inputs' not in p.relative_to(active).parts})
                for filename in ('stdout', 'stderr'):
                    with (capture / filename).open('rb') as inp, (diagnostics / filename).open('wb') as out:
                        out.write(inp.read(1024 * 1024))
                break
            remove_owned(capture)
            remove_owned(SCRATCH / 'validation-capture')
        if inventory(active / 'inputs') != initial_inputs:
            # DPT's working image directory is a documented mutable output.
            current = inventory(active / 'inputs')
            current = {k: v for k, v in current.items() if not k.startswith('dpt/')}
            initial = {k: v for k, v in initial_inputs.items() if not k.startswith('dpt/')}
            if current != initial:
                raise RuntimeError('Benchmark mutated immutable inputs')
        if inventory(active / 'scripts') != initial_sources:
            raise RuntimeError('Wrapper did not restore script sources')
        complete = len(all_records) == len(b['scripts']) and all(r['valid'] for r in all_records)
        result = {'valid': complete, 'benchmark': name, 'mode': mode, 'repetition': repetition,
                  'records': len(all_records), 'elapsed_sec': sum(r['elapsed_sec'] for r in all_records),
                  'cache_bytes': allocated_bytes(SCRATCH / 'cache')}
        if mode == 'observe' and complete and all(r['cache_entries_after'] == 0 for r in all_records):
            result.update(valid=False, instrumentation_failure='No Observe cache entries: acceleration was bypassed')
            complete = False
        atomic_json(sequence / ('complete.json' if complete else 'failed.json'), result)
        return result
    finally:
        record_event(run, {'event': 'cleanup-start', 'benchmark': name, 'mode': mode,
                           'repetition': repetition, 'cache_bytes': allocated_bytes(SCRATCH / 'cache')})
        recovery = list((SCRATCH / 'cache').glob('*.recovery'))
        if recovery:
            record_event(run, {'event': 'recovery-retained', 'paths': list(map(str, recovery))})
            raise RuntimeError(f'Recovery requires inspection; preserving fixture/cache: {recovery}')
        for path in (SCRATCH / 'cache', WORK / 'fixture', SCRATCH / 'capture', SCRATCH / 'validation-capture'):
            remove_owned(path)
        record_event(run, {'event': 'cleanup-complete', 'benchmark': name, 'mode': mode,
                           'repetition': repetition, 'free_bytes': shutil.disk_usage(WORK).free})


def report(run):
    rows = []
    for sequence in sorted((run / 'sequences').glob('*')):
        if '.interrupted.' in sequence.name:
            continue
        for path in sorted(sequence.glob('[0-9][0-9].*.json')):
            rows.append(json.loads(path.read_text()))
    config = json.loads((run / 'configuration.json').read_text())
    if 'modes' not in config:
        raise ValueError('Preparation has status/input provenance, not timing results; use status')
    expected = sum(len(b['scripts']) for b in selected(config['only'])) * len(config['modes']) * config['repetitions']
    groups = {}
    for row in rows:
        groups.setdefault((row['benchmark'], row['script'], row['mode']), []).append(row)
    stats = []
    for (name, script, mode), samples in sorted(groups.items()):
        valid = [r['elapsed_sec'] for r in samples if r['valid']]
        stats.append({'benchmark': name, 'script': script, 'mode': mode,
                      'samples': len(samples), 'valid_samples': len(valid),
                      'mean_sec': statistics.mean(valid) if valid else None,
                      'median_sec': statistics.median(valid) if valid else None,
                      'stdev_sec': statistics.stdev(valid) if len(valid) > 1 else None,
                      'min_sec': min(valid) if valid else None, 'max_sec': max(valid) if valid else None})
    lookup = {(r['benchmark'], r['script'], r['mode']): r for r in stats}
    ratios = []
    frozen_hashes = json.loads((run / 'frozen-build.json').read_text())['sha256']
    for b in selected(config['only']):
        for index, script in enumerate(b['scripts']):
            obs = lookup.get((b['name'], script, 'observe'))
            for reference in ('bash', 'original'):
                ref = lookup.get((b['name'], script, reference))
                if obs and ref and obs['valid_samples'] == ref['valid_samples'] == config['repetitions']:
                    ratios.append({'benchmark': b['name'], 'script': script, 'cold': index == 0,
                                   'unchanged_source': index > 0 and frozen_hashes.get(f'benchmarks/{b["name"]}/{script}') ==
                                       frozen_hashes.get(f'benchmarks/{b["name"]}/{b["scripts"][index-1]}'),
                                   'reference': reference, 'speedup': ref['mean_sec'] / obs['mean_sec']})
    failed_sequences = list((run / 'sequences').glob('*/failed.json'))
    family_totals = []
    cold_overheads = []
    for b in selected(config['only']):
        complete_modes = {}
        for mode in config['modes']:
            entries = [lookup.get((b['name'], script, mode)) for script in b['scripts']]
            if all(e and e['valid_samples'] == config['repetitions'] for e in entries):
                complete_modes[mode] = sum(e['mean_sec'] for e in entries)
        if 'bash' in complete_modes:
            for mode in ('original', 'observe'):
                if mode in complete_modes:
                    first = b['scripts'][0]
                    cold_overheads.append({'benchmark': b['name'], 'mode': mode,
                        'bash_sec': lookup[(b['name'], first, 'bash')]['mean_sec'],
                        'mode_sec': lookup[(b['name'], first, mode)]['mean_sec'],
                        'time_ratio': lookup[(b['name'], first, mode)]['mean_sec'] /
                                      lookup[(b['name'], first, 'bash')]['mean_sec']})
        peaks = {mode: max((r['peak_cache_bytes'] for r in rows if r['benchmark'] == b['name']
                          and r['mode'] == mode), default=0) for mode in config['modes']}
        provenance_path = run / 'inputs' / f'{b["name"]}.json'
        provenance = json.loads(provenance_path.read_text()) if provenance_path.is_file() else {}
        input_bytes = provenance.get('input_bytes', 0) + sum(m['bytes'] for m in provenance.get('models', []))
        family_totals.append({'benchmark': b['name'], 'complete_mode_totals_sec': complete_modes,
                              'peak_cache_bytes': peaks, 'input_bytes': input_bytes,
                              'paper_nominal_bytes': b['paper_nominal_bytes'],
                              'size_ratio_to_paper_nominal': input_bytes / b['paper_nominal_bytes'] if input_bytes else None})
    summed_comparisons = []
    for reference in ('bash', 'original'):
        families = [f for f in family_totals if reference in f['complete_mode_totals_sec']
                    and 'observe' in f['complete_mode_totals_sec']]
        if families:
            reference_sum = sum(f['complete_mode_totals_sec'][reference] for f in families)
            observe_sum = sum(f['complete_mode_totals_sec']['observe'] for f in families)
            summed_comparisons.append({'reference': reference, 'matched_families': len(families),
                                      'reference_sum_sec': reference_sum, 'observe_sum_sec': observe_sum,
                                      'summed_time_speedup': reference_sum / observe_sum})
    historical = {}
    with (STUDY / 'reference/historical-timings.csv').open() as stream:
        for old in csv.DictReader(stream):
            historical.setdefault((old['benchmark'], old['script'], old['mode']), []).append(float(old['elapsed_sec']))
    historical_comparisons = []
    if config['profile'] == 'paper':
        for current in stats:
            historical_mode = {'bash': 'bash', 'original': 'incr'}.get(current['mode'])
            previous = historical.get((current['benchmark'], current['script'], historical_mode))
            if previous and current['mean_sec'] is not None:
                historical_mean = statistics.mean(previous)
                factor = current['mean_sec'] / historical_mean
                historical_comparisons.append({
                    'benchmark': current['benchmark'], 'script': current['script'], 'mode': current['mode'],
                    'historical_mean_sec': historical_mean, 'current_mean_sec': current['mean_sec'],
                    'current_over_historical': factor,
                    'review_large_difference': factor < 0.5 or factor > 2})
    summary = {'run': run.name, 'profile': config['profile'], 'expected_invocations': expected,
               'invocations': len(rows), 'valid_invocations': sum(r['valid'] for r in rows),
               'complete': len(rows) == expected and all(r['valid'] for r in rows) and not failed_sequences,
               'failed_sequences': [str(p.relative_to(run)) for p in failed_sequences],
               'statistics': stats, 'ratios': ratios, 'family_totals': family_totals,
               'cold_overheads': cold_overheads, 'summed_comparisons': summed_comparisons,
               'historical_comparisons': historical_comparisons}
    if (run / 'superseded.json').is_file():
        summary.update(complete=False, superseded=json.loads((run / 'superseded.json').read_text()), ratios=[])
        ratios = []
    atomic_json(run / 'summary.json', summary)
    fields = ['benchmark', 'script', 'mode', 'repetition', 'profile', 'index', 'elapsed_sec', 'returncode',
              'valid', 'cache_bytes', 'peak_cache_bytes', 'peak_work_bytes', 'private_tmp_bytes',
              'stdout_bytes', 'stderr_bytes', 'stdout_sha256', 'stderr_sha256']
    resource_fields = ['user_sec', 'system_sec', 'max_rss_kib', 'major_faults', 'minor_faults',
                       'voluntary_switches', 'involuntary_switches', 'filesystem_inputs', 'filesystem_outputs']
    fields += resource_fields + ['cache_entries_before', 'cache_entries_after', 'cache_entries_retained', 'cache_entries_changed']
    with (run / 'timings.csv.pending').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(dict(r, **r.get('resources', {})) for r in rows)
    (run / 'timings.csv.pending').replace(run / 'timings.csv')
    lines = [f'# Study {run.name}', '', f'Profile: {config["profile"]}.',
             'Native shell transformation: ' + ('enabled, with Python fallback.' if config.get('native_transform') else 'disabled.'), '',
             f'{len(rows)}/{expected} invocations; {summary["valid_invocations"]} valid. Complete: {summary["complete"]}.', '',
             '| Reference | Valid paired edits | Arithmetic mean | Geometric mean | Maximum |',
             '|---|---:|---:|---:|---:|']
    for ref in ('bash', 'original'):
        values = [r['speedup'] for r in ratios if r['reference'] == ref and not r['cold'] and not r['unchanged_source']]
        if values:
            lines.append(f'| {ref} | {len(values)} | {statistics.mean(values):.3f}× | '
                         f'{math.exp(statistics.mean(math.log(v) for v in values)):.3f}× | {max(values):.3f}× |')
    lines += ['', 'See timings.csv and invocation JSON for resources, hashes, output manifests, diagnostics, and cleanup evidence.',
              'Identical successive source versions are retained as warm-repeat measurements and excluded from edit aggregates.',
              'An incomplete study or failed sequence is never presented as a complete benchmark comparison.', '']
    (run / 'report.md').write_text('\n'.join(lines))
    return summary


def run(args):
    benchmarks = selected(args.only)
    if args.resume:
        destination = args.resume.resolve()
        args._run_destination = destination
        if not destination.is_relative_to(STUDY / 'results'):
            raise ValueError('Resume target must be in study results')
        config = json.loads((destination / 'configuration.json').read_text())
        if config['manifest_sha256'] != file_hash(STUDY / 'manifest.json') or config['harness_sha256'] != inventory(HARNESS):
            raise ValueError('Cannot resume with changed harness/manifest; create a new run')
        for key in ('profile', 'only', 'repetitions', 'modes', 'reserve_gib', 'work_budget_gib', 'native_transform'):
            actual = list(args.modes) if key == 'modes' else getattr(args, key)
            if config.get(key, False) != actual:
                raise ValueError(f'Resume configuration mismatch: {key}')
        build = Path(json.loads((destination / 'frozen-build.json').read_text())['directory'])
        for p, digest in json.loads((destination / 'frozen-build.json').read_text())['sha256'].items():
            if file_hash(build / p) != digest:
                raise ValueError('Frozen build changed')
        args._owns_run = True
    else:
        run_id = args.run_id or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + f'-{os.getpid()}'
        if not run_id or '/' in run_id or run_id in ('.', '..'):
            raise ValueError('Invalid run ID')
        destination = STUDY / 'results' / run_id
        destination.mkdir(parents=True, exist_ok=False)
        args._run_destination = destination
        args._owns_run = True
        config = {'profile': args.profile, 'only': args.only, 'repetitions': args.repetitions,
                  'modes': list(args.modes), 'native_transform': getattr(args, 'native_transform', False), 'reserve_gib': args.reserve_gib,
                  'work_budget_gib': args.work_budget_gib, 'started': now(),
                  'manifest_sha256': file_hash(STUDY / 'manifest.json'), 'harness_sha256': inventory(HARNESS)}
        atomic_json(destination / 'configuration.json', config)
        # Dependency/source evidence belongs to this run, not an earlier build.
        doctor()
        shutil.copy2(WORK / 'doctor.json', destination / 'environment.json')
        build = freeze(destination)
    references = {}
    interrupted = False
    try:
        for b in benchmarks:
            if all((destination / 'sequences' / f'{b["name"]}.{mode}.{rep}' / 'complete.json').is_file()
                   for rep in range(args.repetitions) for mode in args.modes):
                continue  # Released inputs are unnecessary for fully completed families.
            data = WORK / 'data' / args.profile / b['name']
            if not (data / 'prepared.json').is_file():
                raise RuntimeError(f'Inputs not prepared: run prepare --profile {args.profile} --only {b["name"]}')
            provenance = json.loads((data / 'prepared.json').read_text())
            atomic_json(destination / 'inputs' / f'{b["name"]}.json', provenance)
            for entry in provenance['files']:
                if file_hash(data / entry['path']) != entry['sha256']:
                    raise RuntimeError('Prepared input fingerprint changed')
            for model in provenance.get('models', []):
                if file_hash(Path(model['path'])) != model['sha256']:
                    raise RuntimeError('External model fingerprint changed')
            if b['name'] == 'dpt' and args.profile == 'paper':
                mirror_context = Mirror(data)
            else:
                from contextlib import nullcontext
                mirror_context = nullcontext(None)
            with mirror_context as mirror:
                for repetition in range(args.repetitions):
                    # Bash always produces that repetition's reference first.
                    measured = [m for m in args.modes if m != 'bash']
                    if repetition % 2:
                        measured.reverse()
                    for mode in (['bash'] if 'bash' in args.modes else []) + measured:
                        result = execute_sequence(destination, b, mode, repetition, args, build, data, references, mirror)
                        report(destination)
                        if not result['valid']:
                            print(f'FAILED sequence {b["name"]}/{mode}; inspect {destination}', flush=True)
                            if not args.continue_on_failure:
                                atomic_json(destination / 'status.json', {'state': 'failed', 'updated': now(), 'sequence': result})
                                return 1
            completed_paths = [destination / 'sequences' / f'{b["name"]}.{mode}.{rep}' / 'complete.json'
                               for rep in range(args.repetitions) for mode in args.modes]
            if args.release_inputs and all(path.is_file() for path in completed_paths):
                remove_owned(data)
    except BaseException as error:
        interrupted = True
        atomic_json(destination / 'status.json', {'state': 'interrupted' if isinstance(error, KeyboardInterrupt) else 'error',
                    'updated': now(), 'error': repr(error)})
        record_event(destination, {'event': 'error', 'error': repr(error)})
        raise
    finally:
        summary = report(destination)
        if not interrupted:
            atomic_json(destination / 'status.json', {'state': 'complete' if summary['complete'] else 'failed',
                        'updated': now(), 'run': destination.name,
                        'valid_invocations': summary['valid_invocations'], 'expected_invocations': summary['expected_invocations']})
    return 0 if summary['complete'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    doc = sub.add_parser('doctor')
    doc.add_argument('--build', action='store_true')
    pre = sub.add_parser('prepare')
    pre.add_argument('--profile', choices=('min', 'paper'), required=True)
    pre.add_argument('--only', default='')
    pre.add_argument('--reserve-gib', type=int, default=8)
    pre.add_argument('--result', type=Path, help='Optional durable preparation progress directory')
    execute = sub.add_parser('run')
    execute.add_argument('--profile', choices=('min', 'paper'), required=True)
    execute.add_argument('--only', default='')
    execute.add_argument('--repetitions', type=int, default=3)
    execute.add_argument('--native-transform', action='store_true', help='Opt into the native pipeline compiler, with Python fallback')
    execute.add_argument('--modes', type=lambda s: tuple(s.split(',')), default=MODES)
    execute.add_argument('--run-id')
    execute.add_argument('--resume', type=Path)
    execute.add_argument('--reserve-gib', type=int, default=8)
    execute.add_argument('--work-budget-gib', type=int, default=32)
    execute.add_argument('--continue-on-failure', action='store_true')
    execute.add_argument('--release-inputs', action='store_true')
    for command in ('report', 'status'):
        p = sub.add_parser(command)
        p.add_argument('run', type=Path)
    args = parser.parse_args()
    if args.command == 'status':
        print((args.run / 'status.json').read_text())
        return 0
    if args.command == 'report':
        print(json.dumps(report(args.run), indent=2))
        return 0
    with lock():
        if args.command == 'doctor':
            print(json.dumps({k: v for k, v in doctor(args.build).items() if k in ('platform', 'repositories', 'free_bytes')}, indent=2))
            return 0
        if args.reserve_gib < 1:
            parser.error('Disk reserve must be positive')
        if args.command == 'prepare':
            result = args.result
            if result is not None:
                result = result.resolve()
                if not result.is_relative_to((STUDY / 'results').resolve()):
                    parser.error('Preparation evidence must live under study results')
                result.mkdir(parents=True, exist_ok=False)
                atomic_json(result / 'configuration.json', {'stage': 'prepare', 'profile': args.profile,
                    'only': args.only, 'started': now(), 'harness_sha256': inventory(HARNESS)})
            try:
                for b in selected(args.only):
                    print(f'PREPARE {args.profile} {b["name"]}', flush=True)
                    if result:
                        atomic_json(result / 'status.json', {'state': 'preparing', 'profile': args.profile,
                            'benchmark': b['name'], 'updated': now(), 'pid': os.getpid()})
                    directory = prepare(b['name'], args.profile, args.reserve_gib * GIB)
                    print(f'PREPARED {directory}', flush=True)
                    if result:
                        shutil.copy2(directory / 'prepared.json', result / f'{b["name"]}.json')
                if result:
                    atomic_json(result / 'status.json', {'state': 'complete', 'updated': now()})
            except BaseException as error:
                if result:
                    atomic_json(result / 'status.json', {'state': 'error', 'error': repr(error), 'updated': now()})
                raise
            return 0
        if args.reserve_gib < 1 or args.work_budget_gib < 1:
            parser.error('Disk limits must be positive')
        if args.repetitions < 1 or len(args.modes) != len(set(args.modes)) or not set(args.modes) <= set(MODES):
            parser.error('Use positive repetitions and unique known modes')
        if 'bash' not in args.modes:
            parser.error('Bash reference mode is required')
        check_space(args.reserve_gib * GIB)
        try:
            return run(args)
        except BaseException as error:
            # Failed validation of an existing ID/resume does not own its
            # evidence and must never change an earlier run's saved status.
            destination = getattr(args, '_run_destination', None)
            if getattr(args, '_owns_run', False) and destination and destination.resolve().is_relative_to((STUDY / 'results').resolve()) and (destination / 'configuration.json').is_file():
                atomic_json(destination / 'status.json', {'state': 'interrupted' if isinstance(error, KeyboardInterrupt) else 'error',
                    'updated': now(), 'error': repr(error)})
            raise


if __name__ == '__main__':
    def stop(_signal, _frame):
        raise KeyboardInterrupt('Study termination requested')
    signal.signal(signal.SIGTERM, stop)
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
