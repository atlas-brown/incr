"""Small serial cold/warm probes; Bash output is the correctness reference."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'studies/paper-size-benchmarks/harness'))
from common import supervise, atomic_json, remove_owned, WORK


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--include-old', action='store_true')
    parser.add_argument('--only')
    parser.add_argument('--mib', type=int, default=2)
    parser.add_argument('--profile', action='store_true', help='Diagnostic phase profiling; not headline timing evidence')
    parser.add_argument('--modes', help='Comma-separated modes; Bash must be first')
    args = parser.parse_args()
    from provenance import validate_arguments
    validate_arguments(parser, args)
    if args.only and not set(args.only.split(',')) <= {'stream', 'sort-stdin', 'file-read', 'sort-file', 'write-file'}:
        parser.error('Unknown probe case')
    result = ROOT / 'studies/observe-performance-regression/results' / args.id
    result.mkdir(parents=True, exist_ok=False)
    from provenance import fingerprint
    old = ROOT / 'studies/observe-performance-regression/.work'
    fingerprint(ROOT, result, Path(__file__), [old/'incr-before-audit', old/'observe-before-audit'] if args.include_old else [])
    owned = Path(tempfile.mkdtemp(prefix='perf-probe-', dir=WORK))
    fixture = owned / 'fixture'
    fixture.mkdir()
    (fixture / 'tmp').mkdir()
    profiles = owned / 'profiles'
    profiles.mkdir()
    original = ROOT.parent / 'incr-main-qualification'
    modes = {'bash': None, 'original': original, 'current-try': ROOT, 'observe': ROOT}
    if args.include_old:
        modes['old-observe'] = ROOT / 'studies/observe-performance-regression/.work/incr-before-audit'
    modes['observe-batch'] = ROOT
    modes['observe-directory-access'] = ROOT
    if args.modes:
        requested = args.modes.split(',')
        if requested[0] != 'bash' or len(requested) != len(set(requested)) or not set(requested) <= modes.keys():
            parser.error('Use unique available modes with Bash first; old-observe needs --include-old')
        modes = {name: modes[name] for name in requested}
    cases = {'stream': ['tr', 'a-z', 'A-Z'], 'sort-stdin': ['sort'], 'file-read': ['wc', '-l', str(fixture / 'input')],
             'sort-file': ['sort', str(fixture / 'input')],
             'write-file': ['sh', '-c', 'tr a-z A-Z < input > output']}
    env = {k: os.environ[k] for k in ('HOME', 'USER', 'LOGNAME', 'PATH') if k in os.environ}
    env.update(LC_ALL='C', INCR_EFFECT_POLICY='final', TMPDIR=str(fixture / 'tmp'))
    if args.profile:
        env['INCR_PROFILE_DIR'] = str(profiles)
    records = []
    try:
        # About 2 MiB: enough stream traffic to expose buffering overhead, no download.
        line = b'one two three four five six seven eight nine ten\n'
        (fixture / 'input').write_bytes(line * (args.mib*1024**2//len(line)+1))
        script = fixture / 'invoke'
        script.write_text('exec "$@" < input\n')
        for case, command in cases.items():
            if args.only and case not in args.only.split(','):
                continue
            if case == 'sort-stdin':
                line = b'one\ntwo\nthree\nfour\nfive\nsix\nseven\neight\nnine\nten\n'
                (fixture / 'input').write_bytes(line * (args.mib*1024**2//len(line)+1))
            script.write_text('exec "$@" < input\n' if case in ('stream', 'sort-stdin') else 'exec "$@" < /dev/null\n')
            references = {}
            for mode, top in modes.items():
                cache = owned / 'cache'
                if cache.exists(): remove_owned(cache)
                cache.mkdir()
                (fixture / 'output').unlink(missing_ok=True)
                argv = command if top is None else [str(top / 'target/release/incr'), '--cache', str(cache),
                       '--try', str(top / 'src/scripts/try.sh')]
                if mode in ('observe', 'observe-batch', 'observe-directory-access', 'old-observe'):
                    observer = (ROOT / 'studies/observe-performance-regression/.work/observe-before-audit/target/release/observe'
                                if mode == 'old-observe' else ROOT.parent / 'observe/target/release/observe')
                    argv += ['--observe', str(observer)]
                if mode == 'observe-batch': argv += ['-b']
                if mode == 'observe-directory-access': argv += ['--assume-directory-access']
                if top is not None: argv += ['--', *command]
                for phase in ('cold', 'warm'):
                    if case == 'write-file':
                        (fixture / 'output').unlink(missing_ok=True)
                    before = set(profiles.iterdir())
                    capture = owned / 'capture'
                    if capture.exists(): remove_owned(capture)
                    timing = owned / 'timing.json'
                    worker = ('import json,resource,subprocess,sys,time;start=time.perf_counter();'
                              'p=subprocess.Popen(sys.argv[2:],close_fds=True);status=p.wait();'
                              'elapsed=time.perf_counter()-start;r=resource.getrusage(resource.RUSAGE_CHILDREN);'
                              'open(sys.argv[1],"w").write(json.dumps({"elapsed_sec":elapsed,"user_sec":r.ru_utime,"system_sec":r.ru_stime,"output_blocks":r.ru_oublock,"voluntary_switches":r.ru_nvcsw,"involuntary_switches":r.ru_nivcsw}));sys.exit(status)')
                    row = supervise([sys.executable, '-c', worker, str(timing), 'bash', str(script), *argv], cwd=fixture, env=env, capture=capture,
                                    timeout=20, reserve=8*1024**3, budget=32*1024**3)
                    row['command_resources'] = json.loads(timing.read_text()) if timing.is_file() else {}
                    row['command_elapsed_sec'] = row['command_resources'].get('elapsed_sec')
                    from common import file_hash
                    outputs = file_hash(fixture / 'output') if (fixture / 'output').exists() else None
                    observed = [row['returncode'], row['stdout_sha256'], outputs]
                    if mode == 'bash': references[phase] = observed
                    row.update(case=case, mode=mode, phase=phase,
                               valid=not row['failure'] and observed == references[phase], output_sha256=outputs)
                    row['input_bytes'] = (fixture / 'input').stat().st_size
                    if top == ROOT:
                        # Preserve metadata before cache cleanup so missed reuse
                        # can be investigated without rerunning the workload.
                        from cache_metadata import decode, directory_summary
                        metadata = {}
                        for path in cache.glob('batch_*/data.incr'):
                            try:
                                metadata[path.parent.name] = decode(path)
                                metadata[path.parent.name]['directory_checks'] = directory_summary(path)
                            except (OSError, ValueError) as error:
                                metadata[path.parent.name] = {'diagnostic_error': str(error)}
                        atomic_json(result / f'{case}-{mode}-{phase}-cache.json', metadata)
                    if not row['valid']:
                        row['stderr_sample'] = (capture/'stderr').read_text(errors='replace')[:4096]
                    records.append(row)
                    destination = result / f'{case}-{mode}-{phase}-profiles'
                    if args.profile:
                        destination.mkdir()
                        for path in set(profiles.iterdir())-before:
                            shutil.copy2(path, destination/path.name)
                    atomic_json(result / 'measurements.json', records)
                    print(case, mode, phase, round(row['command_elapsed_sec'] or row['elapsed_sec'], 5), row['valid'], flush=True)
        atomic_json(result / 'summary.json', {'valid': all(r['valid'] for r in records),
            'samples': len(records), 'mib': args.mib, 'profiling': args.profile})
    finally:
        try:
            from provenance import verify
            verify(ROOT, result, Path(__file__))
        finally:
            remove_owned(owned)


if __name__ == '__main__':
    from study import lock
    with lock():
        main()
