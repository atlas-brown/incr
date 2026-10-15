"""Fault injection: hangs, background children, disk guard, evidence, validation."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

from common import WORK, atomic_json, children, remove_owned, supervise
from prepare import member_path, LimitedHTTP
from validate import compare, decoded_file, manifest, normalized_stderr


class HarnessTests(unittest.TestCase):
    def setUp(self):
        WORK.mkdir(exist_ok=True)
        self.temp = Path(tempfile.mkdtemp(prefix='test-', dir=WORK))

    def tearDown(self):
        remove_owned(self.temp)

    def run_child(self, code, timeout=3, reserve=0):
        return supervise([sys.executable, '-c', code], cwd=self.temp, env=dict(os.environ),
                         capture=self.temp / 'capture', timeout=timeout, reserve=reserve, budget=100 * 1024**3)

    def test_output_manifest_detects_unexpected_directories_and_links(self):
        fixture = self.temp/'fixture'
        (fixture/'outputs').mkdir(parents=True)
        (fixture/'scratch/nested').mkdir(parents=True)
        (fixture/'scratch/nested/result').write_text('unexpected effect')
        (fixture/'dangling').symlink_to('missing')
        (fixture/'tmp').mkdir()
        (fixture/'tmp/private').write_text('excluded infrastructure')
        before = manifest(fixture, 'covid')
        self.assertIn('scratch/nested/result', before)
        self.assertEqual(before['dangling']['kind'], 'symlink')
        self.assertNotIn('tmp/private', before)
        (fixture/'scratch/nested/result').write_text('different effect')
        self.assertNotEqual(before, manifest(fixture, 'covid'))

    def test_background_launch_preserves_dependency_search_path(self):
        from contextlib import nullcontext
        from unittest.mock import patch
        import launch
        search_path = '/custom/rust/bin:/usr/bin:/bin'
        with patch.object(launch, 'STUDY', self.temp), patch.object(launch, 'WORK', self.temp), \
             patch.object(launch, 'lock', return_value=nullcontext()), \
             patch.object(launch, 'selected', return_value=[]), \
             patch.object(launch.shutil, 'copytree'), \
             patch.object(launch.subprocess, 'run') as run, \
             patch.dict(os.environ, {'PATH': search_path}), \
             patch.object(sys, 'argv', ['launch.py', '--profile', 'min', '--only', 'dpt',
                                       '--run-id', 'launch-test', '--repetitions', '1']):
            run.return_value.returncode = 3
            launch.main()
        commands = [call.args[0] for call in run.call_args_list]
        command = next(command for command in commands if command[0] == 'systemd-run')
        self.assertIn('--setenv=PATH=' + search_path, command)
        self.assertIn('--setenv=INCR_BENCH_STUDY=' + str(self.temp), command)

    def test_monitor_rejects_failed_preflight_without_samples(self):
        from datetime import datetime, timezone
        from unittest.mock import patch
        import monitor
        atomic_json(self.temp/'status.json', {'state':'error',
                    'updated':datetime.now(timezone.utc).isoformat()})
        atomic_json(self.temp/'configuration.json', {'reserve_gib':0})
        with patch.object(monitor.subprocess, 'run') as run:
            run.return_value.stdout = 'inactive'
            result = monitor.check(self.temp)
        self.assertEqual(result['health'], 'attention')
        self.assertIn('Run terminated with state=error', result['monitor_issues'])

    def test_monitor_rejects_complete_status_with_missing_samples(self):
        from datetime import datetime, timezone
        from unittest.mock import patch
        import monitor
        atomic_json(self.temp/'status.json', {'state':'complete',
                    'updated':datetime.now(timezone.utc).isoformat()})
        atomic_json(self.temp/'configuration.json', {'reserve_gib':0})
        atomic_json(self.temp/'summary.json', {'complete':True, 'expected_invocations':3,
                    'invocations':3, 'valid_invocations':3, 'failed_sequences':[]})
        with patch.object(monitor.subprocess, 'run') as run:
            run.return_value.stdout = 'inactive'
            result = monitor.check(self.temp)
        self.assertEqual(result['health'], 'attention')
        self.assertIn('Complete status contradicts summary/sample counts', result['monitor_issues'])

    def test_cleanup_plans_new_and_legacy_state_but_preserves_evidence(self):
        from unittest.mock import patch
        import cleanup
        scratch = self.temp/'runner'
        (scratch/'cache').mkdir(parents=True)
        (self.temp/'cache').mkdir()
        (self.temp/'results').mkdir()
        with patch.object(cleanup, 'WORK', self.temp), patch.object(cleanup, 'SCRATCH', scratch):
            records = cleanup.plan(include_inputs=True, builds=['obsolete-01'])
            paths = {record['path'] for record in records}
            self.assertIn(str(scratch), paths)
            self.assertIn(str(self.temp/'cache'), paths)
            self.assertIn(str(self.temp/'data/paper'), paths)
            self.assertIn(str(self.temp/'builds/obsolete-01'), paths)
            self.assertNotIn(str(self.temp/'results'), paths)
            self.assertNotIn(str(self.temp/'data/min'), paths)
            self.assertTrue((scratch/'cache').is_dir())  # Planning never deletes.
            with self.assertRaises(ValueError):
                cleanup.plan(builds=['../escape'])
            (scratch/'cache/session.recovery').mkdir()
            with self.assertRaises(RuntimeError):
                cleanup.plan()

    def test_cleanup_rejects_ancestor_symlink_escape(self):
        from unittest.mock import patch
        import cleanup
        (self.temp/'builds').symlink_to('/tmp', target_is_directory=True)
        with patch.object(cleanup, 'WORK', self.temp), \
             patch.object(cleanup, 'SCRATCH', self.temp/'runner'):
            with self.assertRaises(ValueError):
                cleanup.plan(builds=['outside'])

    def test_framework_cache_is_outside_shared_temporary_directory(self):
        from study import environment
        env = environment('dpt', 'min', self.temp/'fixture', self.temp/'build')
        cache = Path(env['TORCHINDUCTOR_CACHE_DIR'])
        temporary = Path(env['TMPDIR'])
        self.assertFalse(cache.is_relative_to(temporary))
        self.assertEqual(cache, self.temp/'fixture/config/torch')
        self.assertNotIn('TORCHINDUCTOR_CACHE_DIR',
                         environment('poet', 'min', self.temp/'fixture', self.temp/'build'))

    def test_rejected_existing_run_id_preserves_saved_status(self):
        from unittest.mock import patch
        import study
        run = self.temp/'results/saved'
        atomic_json(run/'status.json', {'state':'complete', 'evidence':'keep'})
        atomic_json(run/'configuration.json', {'original':'configuration'})
        with patch.object(study, 'STUDY', self.temp), \
             patch.object(sys, 'argv', ['study.py','run','--profile','min','--only','weather','--run-id','saved']):
            with self.assertRaises(FileExistsError): study.main()
        self.assertEqual(json.loads((run/'status.json').read_text()), {'state':'complete','evidence':'keep'})

    def test_rejected_resume_preserves_saved_status(self):
        from unittest.mock import patch
        import study
        run = self.temp/'results/saved'
        atomic_json(run/'status.json', {'state':'complete', 'evidence':'keep'})
        atomic_json(run/'configuration.json', {'manifest_sha256':'incompatible','harness_sha256':{}})
        (self.temp/'manifest.json').write_bytes((study.STUDY/'manifest.json').read_bytes())
        with patch.object(study, 'STUDY', self.temp), \
             patch.object(sys, 'argv', ['study.py','run','--profile','min','--only','weather','--resume',str(run)]):
            with self.assertRaisesRegex(ValueError, 'Cannot resume'): study.main()
        self.assertEqual(json.loads((run/'status.json').read_text()), {'state':'complete','evidence':'keep'})

    def test_automatic_run_id_records_preflight_failure(self):
        from unittest.mock import patch
        import study
        (self.temp/'manifest.json').write_bytes((study.STUDY/'manifest.json').read_bytes())
        with patch.object(study, 'STUDY', self.temp), \
             patch.object(study, 'doctor', side_effect=RuntimeError('injected preflight failure')), \
             patch.object(sys, 'argv', ['study.py','run','--profile','min','--only','weather']):
            with self.assertRaisesRegex(RuntimeError, 'injected preflight'): study.main()
        statuses=list((self.temp/'results').glob('*/status.json'))
        self.assertEqual(len(statuses),1)
        self.assertEqual(json.loads(statuses[0].read_text())['state'],'error')

    def test_success_exact_bytes_and_status(self):
        result = self.run_child('import sys;sys.stdout.buffer.write(b"a\\0b");sys.stderr.write("diagnostic");sys.exit(7)')
        self.assertEqual(result['returncode'], 7)
        self.assertEqual((self.temp / 'capture/stdout').read_bytes(), b'a\0b')
        self.assertIsNone(result['failure'])
        self.assertEqual(children(os.getpid()), [])

    def test_measurement_excludes_slow_inventory_and_polling(self):
        import time
        from unittest.mock import patch
        def slow_inventory(path):
            time.sleep(.08)
            return 0
        with patch('common.allocated_bytes', side_effect=slow_inventory):
            result = self.run_child('pass')
        self.assertIsNone(result['failure'])
        self.assertLess(result['elapsed_sec'], .1)

    def test_timeout_stops_forked_session_and_reaps(self):
        result = self.run_child('import os,time; p=os.fork(); os.setsid() if p==0 else None; time.sleep(60)', timeout=.2)
        self.assertEqual(result['failure'], 'timeout')
        self.assertLess(result['elapsed_sec'], 2)
        self.assertEqual(children(os.getpid()), [])

    def test_detached_live_child_is_not_a_valid_fast_result(self):
        result = self.run_child('import os,time; p=os.fork(); time.sleep(60) if p==0 else os._exit(0)')
        self.assertEqual(result['failure'], 'surviving-descendants')
        self.assertEqual(children(os.getpid()), [])

    def test_disk_reserve_aborts_before_large_write(self):
        result = self.run_child('import time;time.sleep(60)', reserve=10**15)
        self.assertEqual(result['failure'], 'disk-reserve')
        self.assertEqual(children(os.getpid()), [])

    def test_cleanup_rejects_escape_and_handles_symlink(self):
        with self.assertRaises(ValueError):
            remove_owned(WORK / '..' / 'README.md')
        outside = self.temp / 'source'
        outside.mkdir()
        (outside / 'keep').write_text('keep')
        link = self.temp / 'link'
        link.symlink_to(outside, target_is_directory=True)
        remove_owned(link)
        self.assertEqual((outside / 'keep').read_text(), 'keep')

    def test_archive_traversal_rejected(self):
        for path in ('/absolute', '../escape', 'good/../../escape'):
            with self.assertRaises(ValueError):
                member_path(path)

    def test_tar_timestamps_do_not_hide_payload_mismatch(self):
        paths = []
        for index, payload in enumerate((b'correct', b'correct', b'wrong')):
            path = self.temp / f'{index}.tar'
            with tarfile.open(path, 'w') as archive:
                member = tarfile.TarInfo('payload')
                member.size = len(payload)
                member.mtime = index
                archive.addfile(member, io.BytesIO(payload))
            paths.append(path)
        self.assertEqual(decoded_file(paths[0]), decoded_file(paths[1]))
        self.assertNotEqual(decoded_file(paths[0]), decoded_file(paths[2]))

    def test_error_beyond_sample_is_detected(self):
        path = self.temp / 'stderr'
        path.write_bytes(b'ordinary line\n' * 10000 + b'Error: failed late\n')
        record = normalized_stderr(path, 'word-freq')
        self.assertNotIn('failed late', record['sample'])
        self.assertTrue(record['errors'])

    def test_comparison_includes_status_and_files(self):
        ref = dict(returncode=0, stdout_sha256='x', normalized_stderr_sha256='y', outputs={'file': 'good'})
        self.assertEqual(compare(ref, ref), [])
        self.assertIn('outputs mismatch', compare(ref, dict(ref, outputs={})))
        self.assertIn('returncode mismatch', compare(ref, dict(ref, returncode=1)))

    def test_atomic_evidence_parseable(self):
        path = self.temp / 'record.json'
        atomic_json(path, {'first': 1})
        atomic_json(path, {'second': 2})
        self.assertEqual(json.loads(path.read_text()), {'second': 2})
        self.assertFalse(path.with_suffix('.json.pending').exists())

    def test_exclusive_lock_rejects_second_process(self):
        from study import lock
        with lock():
            proc = subprocess.run([sys.executable, '-c', 'from study import lock;lock()'],
                                  cwd=Path(__file__).parent, capture_output=True, timeout=5)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn(b'never overlap', proc.stderr)

    def test_time_instrumentation_does_not_leak_descriptor(self):
        source = Path(__file__).parent / 'fdguard.c'
        guard = self.temp / 'fdguard'
        subprocess.run(['cc', '-O2', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(guard)],
                       check=True, timeout=30)
        code = ('import os,fcntl;fds=[];'
                '\nfor fd in range(3,64):'
                '\n try:'
                '\n  flags=fcntl.fcntl(fd,fcntl.F_GETFD)'
                '\n  if not flags & fcntl.FD_CLOEXEC:fds.append(fd)'
                '\n except OSError:pass'
                '\nprint(fds)')
        result = supervise(['/usr/bin/time', '-o', str(self.temp / 'resources'), str(guard),
                            sys.executable, '-c', code], cwd=self.temp, env=dict(os.environ),
                           capture=self.temp / 'capture', timeout=5, reserve=0, budget=100 * 1024**3)
        self.assertEqual(result['returncode'], 0)
        self.assertEqual((self.temp / 'capture/stdout').read_text().strip(), '[]')

    def test_source_archive_includes_new_files_and_excludes_generated_caches(self):
        from study import archive_sources
        source = self.temp/'repo'
        (source/'src/__pycache__').mkdir(parents=True)
        (source/'src/new.rs').write_text('new source not present in git diff')
        (source/'src/__pycache__/generated.pyc').write_bytes(b'cache')
        (source/'Cargo.toml').write_text('[package]')
        (source/'incr.sh').write_text('wrapper')
        outside = self.temp/'outside'
        outside.write_text('not source contents')
        (source/'src/link').symlink_to(outside)
        destination = self.temp/'sources/source.tar.gz'
        archive_sources(source, destination)
        with tarfile.open(destination) as archive:
            self.assertIn('src/new.rs', archive.getnames())
            self.assertIn('Cargo.toml', archive.getnames())
            self.assertIn('incr.sh', archive.getnames())
            self.assertFalse(any('__pycache__' in name for name in archive.getnames()))
            self.assertEqual(archive.extractfile('src/new.rs').read(), b'new source not present in git diff')
            self.assertTrue(archive.getmember('src/link').issym())

    def test_runner_artifact_churn_preserves_application_ancestor_metadata(self):
        root = self.temp/'workspace'
        fixture = root/'fixture'
        scratch = root/'runner'
        fixture.mkdir(parents=True)
        scratch.mkdir()
        (fixture/'scripts').mkdir()
        (scratch/'cache').mkdir()
        before = root.stat()
        for _ in range(3):
            for name in ('capture','validation-capture'):
                path = scratch/name
                path.mkdir()
                (path/'stdout').write_text('measurement evidence')
                remove_owned(path)
        after = root.stat()
        self.assertEqual((before.st_mtime_ns,before.st_ctime_ns),
                         (after.st_mtime_ns,after.st_ctime_ns))

    def test_cache_inventory_does_not_descend_into_sandboxes(self):
        from unittest.mock import patch
        from study import cache_inventory
        scratch = self.temp/'runner'
        entry = scratch/'cache/batch_1'
        (entry/'sandbox').mkdir(parents=True)
        (entry/'data.incr').write_bytes(b'metadata')
        (entry/'sandbox/data.incr').write_bytes(b'not cache metadata')
        with patch('study.SCRATCH',scratch):
            self.assertEqual(list(cache_inventory()),['batch_1/data.incr'])

    def test_stream_byte_and_deadline_limits(self):
        stream = LimitedHTTP(io.BytesIO(b'abcdef'), 3)
        with self.assertRaises(ValueError):
            stream.read(4)
        stream = LimitedHTTP(io.BytesIO(b'abcdef'), 100, deadline=-1)
        with self.assertRaises(TimeoutError):
            stream.read(1)
        stream = LimitedHTTP(io.BytesIO(b'abcdef'), 100)
        with self.assertRaises(ValueError):
            stream.read()


if __name__ == '__main__':
    unittest.main()
