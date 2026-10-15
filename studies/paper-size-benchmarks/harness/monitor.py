"""Read-only periodic audit of saved evidence; never launches measurements."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil
import subprocess

from common import atomic_json


def check(run):
    now = datetime.now(timezone.utc)
    status = json.loads((run / 'status.json').read_text())
    config = json.loads((run / 'configuration.json').read_text())
    issues, failures, rows = [], [], []
    for sequence in sorted((run / 'sequences').glob('*')):
        if '.interrupted.' in sequence.name:
            continue
        for path in sorted(sequence.glob('[0-9][0-9].*.json')):
            row = json.loads(path.read_text())
            rows.append(row)
            label = f"{row['benchmark']}/{row['mode']}/{row['repetition']}/{row['script']}"
            if not row['valid']:
                failures.append({'sample': label, 'problems': row['problems'],
                                 'validator_stderr': row.get('validator_stderr')})
                continue
            elapsed = row.get('elapsed_sec')
            if not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed <= 0:
                issues.append(f'{label}: invalid elapsed time')
            if row.get('failure') or row.get('returncode') != 0 or row.get('remaining_descendants'):
                issues.append(f'{label}: valid flag contradicts execution evidence')
            resource = row.get('resources', {})
            for field in ('user_sec', 'system_sec', 'max_rss_kib', 'major_faults', 'minor_faults',
                          'voluntary_switches', 'involuntary_switches', 'filesystem_inputs', 'filesystem_outputs'):
                value = resource.get(field)
                if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    issues.append(f'{label}: invalid resource field {field}')
            validation = row.get('validation', {})
            if validation.get('problems') or not validation:
                issues.append(f'{label}: missing/failed validation marked valid')
            reference = run / 'references' / row['benchmark'] / f"{row['repetition']}.{row['script']}.json"
            if not reference.is_file():
                issues.append(f'{label}: missing Bash reference')
            else:
                expected = json.loads(reference.read_text())
                for field in ('returncode', 'stdout_sha256', 'normalized_stderr_sha256', 'outputs'):
                    if validation.get(field) != expected.get(field):
                        issues.append(f'{label}: saved {field} differs from Bash reference')
    state = status['state']
    if state in {'failed', 'error', 'interrupted'}:
        issues.append(f'Run terminated with state={state}')
    elif state not in {'running', 'complete'}:
        issues.append(f'Unknown run state={state}')
    if state == 'complete':
        summary_path = run / 'summary.json'
        if not summary_path.is_file():
            issues.append('Complete run has no summary')
        else:
            summary = json.loads(summary_path.read_text())
            expected = summary.get('expected_invocations')
            if (not summary.get('complete') or summary.get('failed_sequences')
                    or not isinstance(expected, int) or expected < 1
                    or expected != len(rows)
                    or summary.get('invocations') != len(rows)
                    or summary.get('valid_invocations') != sum(row['valid'] for row in rows)):
                issues.append('Complete status contradicts summary/sample counts')
    service = subprocess.run(['systemctl', '--user', 'is-active', 'incr-bench-study.service'],
                             capture_output=True, text=True, timeout=10).stdout.strip()
    heartbeat_age = (now - datetime.fromisoformat(status['updated'])).total_seconds()
    if status['state'] == 'running' and (service != 'active' or heartbeat_age > 120):
        issues.append(f'Run claims running but service={service}, heartbeat age={heartbeat_age:.1f}s')
    free = shutil.disk_usage(run).free
    if free < config['reserve_gib'] * 1024**3:
        issues.append('Free disk is below configured reserve')
    for sequence in (run / 'sequences').glob('*'):
        complete = sequence / 'complete.json'
        if complete.is_file() and not json.loads(complete.read_text()).get('valid'):
            issues.append(f'{sequence.name}: invalid completion marker')
    result = {'checked_at': now.isoformat(), 'run_state': status['state'], 'progress': status,
              'service': service, 'heartbeat_age_sec': heartbeat_age, 'recorded': len(rows),
              'valid': sum(row['valid'] for row in rows), 'failed_samples': failures,
              'monitor_issues': issues, 'free_bytes': free,
              'health': 'attention' if issues or failures else 'ok',
              'scope': 'Rechecks durable timing/output-comparison evidence. Live output decoding is performed by the measured-run validator.'}
    atomic_json(run / 'monitor.json', result)
    with (run / 'monitor-history.jsonl').open('a') as stream:
        stream.write(json.dumps(result) + '\n')
    print(json.dumps({key: result[key] for key in ('checked_at', 'run_state', 'recorded', 'valid', 'health', 'monitor_issues')}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    check(parser.parse_args().run.resolve())
