#!/usr/bin/env python3
"""Serial policy/optimization qualification with bounded subprocess trees."""
import argparse
import json
import os
from pathlib import Path
import sys

from bounded import run

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    arguments = parser.parse_args()
    arguments.results.mkdir(parents=True, exist_ok=True)
    cases = []
    variants = {
        'stream': [], 'compressed': ['--compress'], 'full': ['--full'],
        'annotations': ['--annotations'], 'batch': ['--batch'],
        'batch-compressed': ['--batch', '--compress'],
        'full-compressed': ['--full', '--compress'],
        'annotations-compressed': ['--annotations', '--compress'],
    }
    for policy in ['live', 'final']:
        for name, flags in variants.items():
            cases.append((policy + '-' + name, 45,
                          [sys.executable, 'qualification/regressions.py', '--effect-policy', policy, *flags, '-q']))
    for name, script in [('chunks', 'chunk_tests.py'), ('shell-ast', 'shell_ast_tests.py'),
                         ('strace', 'trace_tests.py'), ('try', 'try_tests.py'),
                         ('benchmark-components', 'benchmark_tests.py')]:
        cases.append((name, 60, [sys.executable, 'qualification/' + script, '-q']))
    cases.extend([
        ('readonly-descriptor-limit', 20, ['prlimit', '--nofile=64:64', 'cargo', 'test', 'readonly', '--quiet']),
        ('foreign-owner-replay', 20, ['cargo', 'test', 'replay_preserves_group_writable_file_ownership',
                                     '--', '--ignored', '--nocapture']),
        ('observe', 60, ['bash', '../observe/tests/run_tests.sh']),
        ('speculative-restore', 20, [sys.executable, 'qualification/speculative_restore_test.py']),
        ('speculative-byte-restore', 20, [sys.executable, 'qualification/speculative_restore_test.py',
                                        '--byte-path', '--results', str(arguments.results / 'speculative-byte-cases.json')]),
        ('speculative-parent-restore', 20, [sys.executable, 'qualification/speculative_restore_test.py',
                                          '--parent-link', '--byte-path', '--results',
                                          str(arguments.results / 'speculative-parent-cases.json')]),
        ('effect-replay', 30, [sys.executable, 'qualification/effect_replay_probe.py', '--policy', 'final',
                               '--expect-hit', '--results', str(arguments.results / 'effect-replay-cases.json')]),
    ])
    summary = []
    for name, timeout, command in cases:
        print('RUN', name, flush=True)
        result = run(command, cwd=ROOT, timeout=timeout,
                     env=dict(os.environ, INCR_QUALIFICATION_RESULTS=str(arguments.results.resolve())))
        (arguments.results / (name + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        valid = result['returncode'] == 0 and not result['timeout'] and not result['leaked_descendants'] and not result['remaining_descendants']
        summary.append(dict(case=name, valid=valid, elapsed_sec=result['elapsed_sec']))
        (arguments.results / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        print('PASS' if valid else 'FAIL', round(result['elapsed_sec'], 3), flush=True)
        if not valid:
            print(result['stdout'][-2000:], result['stderr'][-4000:], flush=True)
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
