#!/usr/bin/env python3
"""Show matrix progress and optionally append changed milestones to the work log."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--log', action='store_true')
parser.add_argument('--results', type=Path, required=True)
args = parser.parse_args()
status = {}
for name, expected in [('final-ordinary', 2064), ('final-dpt', 80)]:
    path = args.results / name / 'summary.json'
    if not path.exists():
        continue
    try:
        records = json.loads(path.read_text())
    except json.JSONDecodeError:
        print(name + ': summary is being updated; read again on next poll')
        continue
    counts = Counter(record['mode'] for record in records if not record['valid'])
    status[name] = dict(completed=len(records), expected=expected, invalid=dict(counts),
                        latest={key: records[-1][key] for key in ['benchmark', 'script', 'mode', 'phase']} if records else None,
                        candidate_failures=[{key: record[key] for key in ['benchmark', 'script', 'mode', 'phase', 'repetition']}
                            for record in records if not record['valid'] and record['mode'] != 'main'])
print(json.dumps(status, separators=(',', ':')))
if args.log:
    results_key = hashlib.sha256(str(args.results.resolve()).encode()).hexdigest()[:12]
    previous = ROOT / 'qualification/.work' / ('progress-' + results_key + '.json')
    previous.parent.mkdir(parents=True, exist_ok=True)
    old = json.loads(previous.read_text()) if previous.exists() else {}
    changed = {key: value for key, value in status.items() if value != old.get(key)}
    if changed:
        with (ROOT / 'QUALIFICATION_LOG.md').open('a') as stream:
            stream.write('\n### ' + datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC') + '\n\n')
            for name, value in changed.items():
                latest = value['latest']
                stream.write(f"{name}: {value['completed']}/{value['expected']} measurements complete. "
                             f"Latest: `{latest['benchmark']}/{latest['script']}`, {latest['mode']} {latest['phase']}. "
                             f"Invalid measurements by mode: `{value['invalid']}`. "
                             f"Bash/updated-backend failures: {len(value['candidate_failures'])}.\n")
        previous.write_text(json.dumps(status))
