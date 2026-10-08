#!/usr/bin/env python3
"""Show matrix progress and optionally append changed milestones to the work log."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--log', action='store_true')
args = parser.parse_args()
status = {}
for name, expected in [('final-ordinary', 2064), ('final-dpt', 80)]:
    path = ROOT / 'qualification/results/2026-10-07' / name / 'summary.json'
    if not path.exists():
        continue
    try:
        records = json.loads(path.read_text())
    except json.JSONDecodeError:
        print(name + ': summary is being updated; read again on next poll')
        continue
    counts = Counter(r['mode'] for r in records if not r['valid'])
    status[name] = dict(completed=len(records), expected=expected, invalid=dict(counts),
                        latest={k: records[-1][k] for k in ['benchmark', 'script', 'mode', 'phase']} if records else None,
                        candidate_failures=[{k: r[k] for k in ['benchmark', 'script', 'mode', 'phase', 'repetition']}
                            for r in records if not r['valid'] and r['mode'] != 'main'])
print(json.dumps(status, separators=(',', ':')))
if args.log:
    previous = ROOT / 'qualification/.work/progress.json'
    previous.parent.mkdir(exist_ok=True)
    old = json.loads(previous.read_text()) if previous.exists() else {}
    changed = {k: v for k, v in status.items() if v != old.get(k)}
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
