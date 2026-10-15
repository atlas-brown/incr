"""Execution parity and safe fallback for the opt-in native compiler."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import shlex

ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'target/release/incr'
PYTHON=ROOT/'qualification/.venv/bin/python'
OBSERVE=ROOT.parent/'observe/target/release/observe'


class NativeTransformTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='native-transform-')
        self.base=Path(self.temp.name)
        self.env={k:os.environ[k] for k in ('HOME','USER','LOGNAME') if k in os.environ}
        self.env.update(PATH=str(PYTHON.parent)+':/usr/local/bin:/usr/bin:/bin',LC_ALL='C',LANG='C',INCR_EFFECT_POLICY='final')

    def tearDown(self):self.temp.cleanup()

    def arguments(self,source,cache,ready,helper=None):
        return ['--sys-path',str(BINARY),'--try-path',str(ROOT/'src/scripts/try.sh'),
                '--cache-path',str(cache),'--observe-path',str(OBSERVE),
                '--helper-source',str(helper or ROOT/'src/scripts/insert.py'),'--ready',str(ready),'--',str(source)]

    def test_execution_matches_native_and_python_compilation(self):
        cases=[
            "printf 'b\\na\\nb\\n' | sort -u >out; cat out\n",
            "# keep comments\nneedle='a b'\nprintf 'a b\\nx\\n' >input\n>out grep \"$needle\" input; cat out\n",
            "value='a b'; printf '%s\\n' \"${value}\" | tr a-z A-Z\n",
            "value=$(printf 'b\\na\\n' | sort); printf '%s\\n' \"$value\"\n",
            "printf 'x\\n' | grep x && printf ok || printf bad\n",
            "printf 'x\\000y\\n' | tr x z\n",
            "printf 'b\\na\\n' > 'input with space'; sort 'input with space' >out; cat out\n",
            "[[ -n \"$HOME\" ]] || echo missing; printf '9\\n1\\n' | sort -n >out; cat out\n",
        ]
        for index,text in enumerate(cases):
            expected=None
            for mode in ('native','python','fast'):
                with self.subTest(case=index,mode=mode):
                    app=self.base/f'{index}-{mode}';app.mkdir()
                    source=app/'program.sh';source.write_text(text)
                    cache=self.base/f'cache with space {index}-{mode}';cache.mkdir()
                    program=source
                    if mode=='python':
                        argv=[str(PYTHON),str(ROOT/'src/scripts/insert.py'),
                            '--sys-path',str(BINARY),'--try-path',str(ROOT/'src/scripts/try.sh'),
                            '--cache-path',str(cache),'--observe-path',str(OBSERVE),str(source)]
                        compiled=subprocess.run(argv,env=self.env,capture_output=True,timeout=10)
                        self.assertEqual(compiled.returncode,0,compiled.stderr)
                        program=app/'compiled.sh';program.write_bytes(compiled.stdout)
                    elif mode=='fast':
                        ready=app/'ready'
                        compiled=subprocess.run([str(BINARY),'--internal-transform-fast',*self.arguments(source,cache,ready)],
                            env=self.env,capture_output=True,timeout=10)
                        self.assertEqual(compiled.returncode,0,compiled.stderr)
                        self.assertEqual(ready.read_bytes(),b'incr-native-transform-v1\n')
                        program=app/'compiled.sh';program.write_bytes(compiled.stdout)
                    result=subprocess.run(['/bin/bash',str(program)],cwd=app,env=self.env,capture_output=True,timeout=15)
                    outputs={p.name:p.read_bytes() for p in app.iterdir() if p.name in ('out','input','input with space')}
                    observed=(result.returncode,result.stdout,result.stderr,outputs)
                    if mode=='native':expected=observed
                    else:self.assertEqual(observed,expected)

    def test_root_pipeline_uses_native_path_without_python(self):
        source=self.base/'pipeline.sh';source.write_text("printf 'b\\na\\n' | sort >out; cat out\n")
        cache=self.base/'cache'
        env=dict(self.env,INCR_NATIVE_TRANSFORM='1',INCR_CACHE_DIR=str(cache),INCR_TOP=str(ROOT),
                 INCR_OBSERVE='1',INCR_PYTHON='/bin/false')
        result=subprocess.run(['/bin/bash',str(ROOT/'incr.sh'),str(source)],cwd=self.base,
                              env=env,capture_output=True,timeout=10)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'a\nb\n',b''))
        self.assertEqual(list(cache.glob('incr-script.*')),[])

    def test_rejection_has_no_capability_marker(self):
        for index,text in enumerate(["f() { echo hi; }; f", "echo $LINENO", "echo $(", "cat <<EOF\nx\nEOF", "echo ${x:?bad}", "sort &", "sort |& cat", "sort 2>&1"]):
            source=self.base/f'reject-{index}.sh';source.write_text(text)
            ready=self.base/f'ready-{index}'
            result=subprocess.run([str(BINARY),'--internal-transform-fast',*self.arguments(source,self.base/'cache',ready)],
                                  env=self.env,capture_output=True,timeout=10)
            self.assertEqual(result.returncode,3)
            self.assertFalse(ready.exists());self.assertEqual(result.stdout,b'')
        altered=self.base/'insert.py';altered.write_bytes(b'changed helper')
        source=self.base/'simple.sh';source.write_text('sort\n')
        ready=self.base/'altered-ready'
        result=subprocess.run([str(BINARY),'--internal-transform-fast',*self.arguments(source,self.base/'cache',ready,altered)],
                              env=self.env,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,3);self.assertFalse(ready.exists())

    def test_builtin_only_root_wrapper_cleans_capability_file(self):
        source=self.base/'simple.sh';source.write_text('echo ok\n')
        cache=self.base/'cache'
        env=dict(self.env,INCR_NATIVE_TRANSFORM='1',INCR_CACHE_DIR=str(cache),INCR_TOP=str(ROOT),INCR_OBSERVE='1')
        result=subprocess.run(['/bin/bash',str(ROOT/'incr.sh'),str(source)],env=env,capture_output=True,timeout=10)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'ok\n',b''))
        self.assertEqual(list(cache.glob('incr-script.*')),[])

    def test_hanging_control_binary_falls_back_with_no_diagnostics(self):
        top=self.base/'hanging';(top/'src/scripts').mkdir(parents=True);(top/'target/release').mkdir(parents=True)
        for name in ('insert.py','shell_ast.py'):shutil.copy2(ROOT/'src/scripts'/name,top/'src/scripts'/name)
        binary=top/'target/release/incr';binary.write_text("#!/bin/sh\ntrap '' TERM\nsleep 60\n");binary.chmod(0o755)
        source=self.base/'simple.sh';source.write_text('echo ok\n')
        env=dict(self.env,INCR_NATIVE_TRANSFORM='1',INCR_CACHE_DIR=str(self.base/'cache'),INCR_TOP=str(top),
                 INCR_OBSERVE='0',INCR_PYTHON=str(PYTHON))
        result=subprocess.run(['/bin/bash',str(ROOT/'incr.sh'),str(source)],env=env,capture_output=True,timeout=12)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'ok\n',b''))

    def test_arbitrary_successful_control_binary_cannot_bypass_python(self):
        top=self.base/'fake';(top/'src/scripts').mkdir(parents=True);(top/'target/release').mkdir(parents=True)
        for name in ('insert.py','shell_ast.py'):shutil.copy2(ROOT/'src/scripts'/name,top/'src/scripts'/name)
        binary=top/'target/release/incr';binary.write_text('#!/bin/sh\necho arbitrary-successful-output\n');binary.chmod(0o755)
        source=self.base/'simple.sh';source.write_text('echo ok\n')
        hook=self.base/'hook';python=self.base/'python'
        python.write_text('#!/bin/sh\nprintf called > "$HOOK_LOG"\nexec '+shlex.quote(str(PYTHON))+' "$@"\n');python.chmod(0o755)
        env=dict(self.env,INCR_NATIVE_TRANSFORM='1',INCR_CACHE_DIR=str(self.base/'cache'),INCR_TOP=str(top),
                 INCR_OBSERVE='0',INCR_PYTHON=str(python),HOOK_LOG=str(hook))
        result=subprocess.run(['/bin/bash',str(ROOT/'incr.sh'),str(source)],env=env,capture_output=True,timeout=10)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'ok\n',b''))
        self.assertEqual(hook.read_text(),'called')


if __name__=='__main__':unittest.main()
