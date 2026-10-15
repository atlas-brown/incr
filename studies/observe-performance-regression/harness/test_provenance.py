"""Ensure edits cannot silently turn diagnostic probes into valid evidence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'paper-size-benchmarks/harness'))
from provenance import fingerprint, verify


class ProvenanceTests(unittest.TestCase):
    def test_new_sources_and_entrypoints_are_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base/'incr'
            for name in ('incr', 'observe', 'incr-main-qualification'):
                repo = base/name
                (repo/'src').mkdir(parents=True)
                (repo/'src/new-untracked.rs').write_text('initial')
                (repo/'target/release').mkdir(parents=True)
                (repo/'target/release'/('observe' if name=='observe' else 'incr')).write_text('binary')
                (repo/'incr.sh').write_text('wrapper')
            driver = root/'probes/driver.py'
            driver.parent.mkdir()
            driver.write_text('driver')
            (root/'studies/paper-size-benchmarks/harness').mkdir(parents=True)
            result = base/'result'
            result.mkdir()
            with patch('provenance.platform.platform', return_value='test'), \
                 patch('provenance.subprocess.check_output', side_effect=lambda argv, **kwargs: b'' if 'ls-files' in argv else ('fixed' if kwargs.get('text') else b'fixed')):
                fingerprint(root, result, driver)
                verify(root, result, driver)
                (result/'summary.json').write_text('{"valid": true}')
                (root/'src/new-untracked.rs').write_text('changed')
                with self.assertRaisesRegex(RuntimeError, 'results invalidated'):
                    verify(root, result, driver)
                self.assertFalse(json.loads((result/'summary.json').read_text())['valid'])
                fingerprint(root, result, driver)
                (root/'incr.sh').write_text('new wrapper')
                with self.assertRaises(RuntimeError):
                    verify(root, result, driver)


if __name__ == '__main__':
    unittest.main()
