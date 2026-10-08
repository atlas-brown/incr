#!/usr/bin/env python3
"""Compare Observe report-write overhead on a small, shared read fixture."""
import json
from pathlib import Path
import sys
import tempfile

from bounded import run

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'qualification/.work/builds/bad83b650932aabad3a9/observe/target/release/observe'
CANDIDATE = ROOT.parent / 'observe/target/release/observe'
RESULT = ROOT / 'qualification/results/effect-replay/report-probe.json'


def main():
    records = []
    with tempfile.TemporaryDirectory(prefix='report-probe-', dir=ROOT / 'qualification/.work') as temporary:
        fixture = Path(temporary)
        inputs = fixture / 'inputs'
        inputs.mkdir()
        for index in range(200):
            (inputs / str(index)).write_text('data')
        expected = None
        for name, binary in [('baseline', BASELINE), ('candidate', CANDIDATE)]:
            report = fixture / f'{name}.json'
            statistics = fixture / f'{name}.strace'
            command = ['strace', '-c', '-e', 'write', '-o', str(statistics), str(binary),
                       '--dependencies', '--no-filter', '--output', str(report), '--',
                       sys.executable, '-c',
                       'import pathlib,sys; [path.read_bytes() for path in pathlib.Path(sys.argv[1]).iterdir()]',
                       str(inputs)]
            result = run(command, cwd=inputs, timeout=10)
            assert result['returncode'] == 0 and not result['timeout'], result
            assert not result['leaked_descendants'] and not result['remaining_descendants'], result
            observed = json.loads(report.read_text())
            access = (observed['reads'], observed['writes'])
            if expected is None:
                expected = access
            assert access == expected, 'reported access sets differ'
            result.update(mode=name, report_bytes=report.stat().st_size,
                          read_count=len(observed['reads']), write_statistics=statistics.read_text())
            records.append(result)
    RESULT.write_text(json.dumps(records, indent=2) + '\n')
    for result in records:
        print(result['mode'], f"{result['elapsed_sec']:.3f}s", result['report_bytes'], 'report bytes')
        print(result['write_statistics'])


if __name__ == '__main__':
    main()
