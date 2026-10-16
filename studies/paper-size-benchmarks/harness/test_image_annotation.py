import tempfile
from pathlib import Path
import unittest

from image_annotation import independent_checks, comparison_payload
from validate import compare


class ImageValidation(unittest.TestCase):
    def test_missing_or_modified_image_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp)
            (fixture/'inputs/images').mkdir(parents=True)
            (fixture/'outputs').mkdir()
            (fixture/'inputs/images/a.jpg').write_bytes(b'image payload')
            record = {'stdout_bytes': 0}
            self.assertTrue(independent_checks(fixture, record, {'bytes':0}))
            (fixture/'outputs/a title.jpg').write_bytes(b'image payload')
            self.assertEqual(independent_checks(fixture, record, {'bytes':0}), [])
            (fixture/'outputs/a title.jpg').write_bytes(b'corrupt')
            self.assertTrue(independent_checks(fixture, record, {'bytes':0}))

    def test_names_can_vary_but_payloads_cannot(self):
        first = {'one.jpg': {'kind':'file','content':'hash-a'}}
        second = {'different.jpg': {'kind':'file','content':'hash-a'}}
        self.assertEqual(comparison_payload(first), comparison_payload(second))
        second['different.jpg']['content'] = 'hash-b'
        self.assertNotEqual(comparison_payload(first), comparison_payload(second))

    def test_exact_default_and_explicit_policy(self):
        base = dict(returncode=0, stdout_sha256='s', normalized_stderr_sha256='e', outputs={'one':'a'})
        other = dict(base, outputs={'two':'a'})
        self.assertEqual(compare(base, other), ['outputs mismatch'])
        base.update(comparison_policy='payloads', comparison_outputs=['a'])
        other.update(comparison_policy='payloads', comparison_outputs=['a'])
        self.assertEqual(compare(base, other), [])
        other['comparison_outputs'] = ['b']
        self.assertEqual(compare(base, other), ['comparison_outputs mismatch'])


if __name__ == '__main__':
    unittest.main()
