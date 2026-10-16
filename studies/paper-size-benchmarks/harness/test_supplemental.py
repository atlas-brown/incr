"""Fault checks for supplemental workload coverage and artifact validation."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from supplemental import independent_checks, prepare_inputs


class SupplementalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.fixture = Path(self.temporary.name)
        (self.fixture / 'inputs/articles').mkdir(parents=True)
        (self.fixture / 'outputs').mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def search_fixture(self):
        (self.fixture / 'inputs/index.txt').write_text('./page.html\nstop\n')
        (self.fixture / 'inputs/articles/page.html').write_text('<p>example</p>')
        (self.fixture / 'outputs/visited.txt').write_text('page.html\n')
        (self.fixture / 'outputs/global-index.txt').write_text('example | page.html 2\n')

    def test_search_requires_all_seed_articles(self):
        self.search_fixture()
        self.assertEqual(independent_checks(self.fixture, 'web-search', 'engine.sh'), [])
        (self.fixture / 'inputs/index.txt').write_text('page.html\nsecond.html\nstop\n')
        self.assertIn('Article index was not fully visited', independent_checks(self.fixture, 'web-search', 'engine.sh'))

    def test_search_rejects_empty_or_invalid_postings(self):
        self.search_fixture()
        for content in ('', 'example | page.html 0\n', 'example | unknown.html 1\n',
                        'example | page.html nope\n', 'example | page.html\n'):
            with self.subTest(content=content):
                (self.fixture / 'outputs/global-index.txt').write_text(content)
                self.assertTrue(independent_checks(self.fixture, 'web-search', 'engine.sh'))

    def test_search_rejects_unsorted_index_and_unavailable_visits(self):
        self.search_fixture()
        (self.fixture / 'outputs/global-index.txt').write_text('zebra | page.html 1\nalpha | page.html 2\n')
        self.assertTrue(independent_checks(self.fixture, 'web-search', 'engine.sh'))
        (self.fixture / 'outputs/global-index.txt').write_text('alpha | page.html 2\n')
        (self.fixture / 'outputs/visited.txt').write_text('page.html\n../outside\n')
        self.assertTrue(independent_checks(self.fixture, 'web-search', 'engine.sh'))

    def test_min_preparation_rejects_escaping_article_names(self):
        source = self.fixture / 'source'
        (source / 'web-search/min_inputs').mkdir(parents=True)
        (source / 'web-search/min_inputs/index_min.txt').write_text('../../outside\n')
        with patch('prepare.SOURCE', source):
            with self.assertRaisesRegex(ValueError, 'Unsafe article'):
                prepare_inputs('web-search', 'min', self.fixture / 'inputs', 0, {'recipes': []})

    @unittest.skipUnless(importlib.util.find_spec('PIL'), 'Pillow is available in the evaluation venv')
    def test_tufte_requires_every_city_year_plot_and_valid_png(self):
        from PIL import Image
        (self.fixture / 'inputs/tuft-weather.txt').write_text(
            '1\t1\t1995\t20\tCountry\tCity One\tContinent\n'
            '1\t1\t1996\t21\tCountry\tCity One\tContinent\n')
        temporary = self.fixture / 'outputs/plots/tmp/City_One'
        temporary.mkdir(parents=True)
        for name in ('formatted.txt', 'processed.txt'):
            (temporary / name).write_text('data\n')
        plots = self.fixture / 'outputs/plots/City_One'
        plots.mkdir()
        for year in ('1995', '1996'):
            Image.new('RGB', (1, 1)).save(plots / f'{year}.png')
        self.assertEqual(independent_checks(self.fixture, 'weather-tufte', 'tuft-weather-3.sh'), [])
        (plots / '1996.png').unlink()
        self.assertTrue(independent_checks(self.fixture, 'weather-tufte', 'tuft-weather-3.sh'))
        (plots / '1996.png').write_bytes(b'not a PNG')
        self.assertTrue(independent_checks(self.fixture, 'weather-tufte', 'tuft-weather-3.sh'))

    def test_report_selection_distinguishes_suites(self):
        from study import selected
        self.assertEqual([b['name'] for b in selected('web-search', 'supplemental')], ['web-search'])
        self.assertEqual([b['name'] for b in selected('word-freq', 'paper')], ['word-freq'])
        with self.assertRaisesRegex(ValueError, 'Unknown benchmarks'):
            selected('web-search', 'paper')

    def test_archived_manifest_survives_new_suite_configuration_and_detects_tampering(self):
        import json
        from common import file_hash
        from study import run_benchmarks
        manifest = self.fixture / 'manifest.json'
        manifest.write_text(json.dumps({'benchmarks': [{'name': 'old-workload', 'scripts': ['one.sh']}]}))
        config = {'only': 'old-workload', 'suite': 'supplemental', 'manifest_sha256': file_hash(manifest)}
        self.assertEqual(run_benchmarks(self.fixture, config)[0]['name'], 'old-workload')
        manifest.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Archived run manifest changed'):
            run_benchmarks(self.fixture, config)


if __name__ == '__main__':
    unittest.main()
