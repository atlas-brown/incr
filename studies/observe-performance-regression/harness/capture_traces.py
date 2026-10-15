"""Bounded read-only inotify capture of short-lived DPT Observe reports.

Saves one report per model program before normal runtime cleanup removes it.
Does not change cache files, tracing flags, measured programs or reuse decisions.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import select
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'studies/paper-size-benchmarks/harness'))
from common import STUDY, WORK, atomic_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run',type=Path)
    parser.add_argument('--seconds',type=int,default=180)
    args = parser.parse_args()
    run = args.run.resolve()
    if not run.is_relative_to((STUDY/'results').resolve()) or not 1 <= args.seconds <= 300:
        parser.error('Use an owned run and a deadline no longer than 300 seconds')
    status = json.loads((run/'status.json').read_text())
    if status.get('state')!='running' or status.get('mode')!='observe':
        parser.error('A live Observe sequence is required')
    libc = ctypes.CDLL(None,use_errno=True)
    libc.inotify_init1.argtypes=[ctypes.c_int]
    libc.inotify_add_watch.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_uint32]
    descriptor = libc.inotify_init1(os.O_NONBLOCK|os.O_CLOEXEC)
    if descriptor<0: raise OSError(ctypes.get_errno(),'inotify_init1')
    destination = run/'trace-diagnostics'
    destination.mkdir(exist_ok=True)
    captured = []
    deadline = time.monotonic()+args.seconds
    try:
        if libc.inotify_add_watch(descriptor,os.fsencode(WORK/'cache'),0x8|0x80|0x400)<0:
            raise OSError(ctypes.get_errno(),'inotify_add_watch')
        while time.monotonic()<deadline and len(captured)<2:
            if not select.select([descriptor],[],[],min(5,deadline-time.monotonic()))[0]:
                if json.loads((run/'status.json').read_text()).get('state')!='running': break
                continue
            events = os.read(descriptor,65536)
            offset = 0
            while offset+16<=len(events):
                _,mask,_,length=struct.unpack_from('=iIII',events,offset)
                name=events[offset+16:offset+16+length].split(b'\0',1)[0]
                offset+=16+length
                if mask&0x400: return
                if not name.startswith(b'observe_') or not name.endswith(b'.json'): continue
                path=WORK/'cache'/os.fsdecode(name)
                try:
                    with path.open('rb') as source: raw=source.read(32*1024**2+1)
                    if len(raw)>32*1024**2: continue
                    data=json.loads(raw)
                except (OSError,ValueError): continue
                dependencies=data.get('dependencies',[])
                names=[row.get('path') for row in dependencies if isinstance(row.get('path'),str)]
                for program in ('segment','classify'):
                    if program in captured or not any(name.endswith('/scripts/'+program+'.py') for name in names): continue
                    (destination/(program+'.json')).write_bytes(raw)
                    retained=[row for row in dependencies if isinstance(row.get('path'),str)
                              and row['path'].startswith('/') and not any(row['path']==prefix or row['path'].startswith(prefix+'/') for prefix in ('/proc','/dev','/sys'))]
                    summary={'time':datetime.now(timezone.utc).isoformat(),'program':program,
                        'dependency_version':data.get('dependency_version'),'barriers':data.get('replay_barriers'),
                        'uncacheable_dependencies':[row for row in retained if row.get('kind')=='uncacheable'],
                        'read_count':len(data.get('reads',[])),'write_count':len(data.get('writes',[]))}
                    atomic_json(destination/(program+'-summary.json'),summary)
                    captured.append(program)
                    print(json.dumps(summary),flush=True)
    finally:
        os.close(descriptor)
        atomic_json(destination/'capture-status.json',{'captured':captured,'deadline_seconds':args.seconds,
            'finished':datetime.now(timezone.utc).isoformat()})


if __name__=='__main__': main()
