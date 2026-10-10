#!/usr/bin/env bash
source "$DEMO/lib.sh"
# Two jobs must share SQLite's writer lock. Python supplies the standard SQL CLI.
python3 - <<'PY'
import os
import sqlite3
import subprocess

writer = '''import sqlite3
db = sqlite3.connect('jobs.db', timeout=0)
try:
    db.execute("insert into jobs values ('second')")
    db.commit()
    print('database: concurrent writer')
except sqlite3.OperationalError as error:
    if 'locked' not in str(error):
        raise
    print('database: writer blocked')
finally:
    db.close()
'''
with sqlite3.connect('jobs.db') as db:
    db.execute('create table jobs (name text)')
    db.commit()
    db.execute('begin immediate')
    subprocess.run([os.environ['DEMO'] + '/backend.sh', 'python3', '-c', writer], check=True)
    db.rollback()
PY
