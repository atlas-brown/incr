"""Serial bio diagnostics using deterministic subsets of the real BAM inputs.

Subsampling is fixture preparation, outside all timers. These are scaling
diagnostics, not historical full-input results. All seven original scripts and
the shared independent native-output validators run unchanged.
"""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'studies/paper-size-benchmarks/harness'))
from common import WORK, atomic_json, file_hash, remove_owned
from study import doctor, execute_sequence, freeze, lock, now, report, selected
from provenance import fingerprint, validate_arguments, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--fraction', type=float, required=True)
    parser.add_argument('--repetitions', type=int, default=1)
    args = parser.parse_args()
    validate_arguments(parser, args)
    if not 0 < args.fraction < 1:
        parser.error('Use a fraction between zero and one; full inputs use the paper harness')
    result = ROOT / 'studies/observe-performance-regression/results' / args.id
    result.mkdir(parents=True, exist_ok=False)
    fingerprint(ROOT, result, Path(__file__))
    parameters = SimpleNamespace(profile='scaled', only='bio', repetitions=args.repetitions,
        modes=('bash', 'original', 'observe'), annotations=False, reserve_gib=8,
        work_budget_gib=32, native_transform=True, assume_directory_access=True,
        content_validated_inputs=True)
    atomic_json(result / 'configuration.json', dict(vars(parameters), fraction=args.fraction,
        started=now(), scope='Deterministic real-BAM subsampling diagnostic; not full paper evaluation'))
    doctor()
    build = freeze(result)
    owned = Path(tempfile.mkdtemp(prefix='bio-scale-', dir=WORK))
    try:
        source = WORK / 'data/paper/bio/inputs/bio'
        target = owned / 'inputs/bio'
        target.mkdir(parents=True)
        shutil.copy2(source / 'input.txt', target / 'input.txt')
        inputs = []
        for bam in sorted(source.glob('*.bam')):
            initial = file_hash(bam)
            destination = target / bam.name
            subprocess.run(['samtools', 'view', '--subsample-seed', '42',
                '--subsample', str(args.fraction), '-b', '-o', str(destination), str(bam)],
                check=True, timeout=600)
            subprocess.run(['samtools', 'quickcheck', str(destination)], check=True, timeout=30)
            if file_hash(bam) != initial:
                raise RuntimeError('Source BAM changed during preparation')
            inputs.append(dict(source=str(bam), source_sha256=initial, name=bam.name,
                bytes=destination.stat().st_size, sha256=file_hash(destination)))
        if not inputs:
            raise RuntimeError('No prepared full BAM inputs')
        provenance = dict(input_bytes=sum(p.stat().st_size for p in target.iterdir()),
            models=[], inputs=inputs, seed=42, fraction=args.fraction,
            input_list_sha256=file_hash(target / 'input.txt'))
        atomic_json(owned / 'prepared.json', provenance)
        atomic_json(result / 'inputs/bio.json', provenance)
        task = dict(selected('bio')[0], timeout_scaled=600)
        references = {}
        for repetition in range(args.repetitions):
            modes = ['original', 'observe'] if repetition % 2 == 0 else ['observe', 'original']
            for mode in ['bash', *modes]:
                for item in inputs:
                    if file_hash(target / item['name']) != item['sha256']:
                        raise RuntimeError('Diagnostic input changed')
                row = execute_sequence(result, task, mode, repetition, parameters,
                    build, owned, references)
                report(result)
                if not row['valid']:
                    raise RuntimeError(f'Bio diagnostic failed: {mode}/{repetition}')
        summary = report(result)
        if not summary['complete']:
            raise RuntimeError('Incomplete bio scaling diagnostic')
        verify(ROOT, result, Path(__file__))
        atomic_json(result / 'status.json', dict(state='complete', updated=now(),
            valid_invocations=summary['valid_invocations']))
    except BaseException as error:
        atomic_json(result / 'status.json', dict(state='error', updated=now(), error=repr(error)))
        raise
    finally:
        remove_owned(owned)


if __name__ == '__main__':
    with lock():
        main()
