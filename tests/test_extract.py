# tests/test_extract.py
"""Tests de extract: parser tolerante, seguridad, globs, secretos."""

import tempfile
import unittest
from pathlib import Path

from extract import (
    clean_path_line,
    collect_files,
    normalize_rel_path,
    parse_path_list,
    suggest_for_missing,
)


def make_repo(files: dict[str, str]) -> Path:
    tmp = Path(tempfile.mkdtemp())
    for rel, text in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
    return tmp


class ParserTests(unittest.TestCase):
    def test_tolerant_cleaning(self):
        self.assertEqual(clean_path_line('- main.py'), 'main.py')
        self.assertEqual(clean_path_line('1. src/app.py'), 'src/app.py')
        self.assertEqual(clean_path_line('`render.py`'), 'render.py')
        self.assertEqual(clean_path_line('./config.py'), 'config.py')
        self.assertEqual(clean_path_line('src\\app.py'), 'src/app.py')
        self.assertEqual(clean_path_line('  *  "tokens.py"  '), 'tokens.py')

    def test_inline_comment_stripped(self):
        self.assertEqual(parse_path_list('main.py # comentario'), ['main.py'])

    def test_paths_block_wins(self):
        raw = 'Estos son:\n- main.py\n```paths\nscanner.py\ntokens.py\n```'
        self.assertEqual(parse_path_list(raw), ['scanner.py', 'tokens.py'])

    def test_plain_lines_without_block(self):
        raw = 'archivos:\n- main.py\n- render.py'
        self.assertEqual(parse_path_list(raw), ['archivos:', 'main.py', 'render.py'])

    def test_prose_with_spaces_dropped(self):
        raw = 'Claro! Estos son los archivos:\n- main.py'
        self.assertEqual(parse_path_list(raw), ['main.py'])


class SecurityTests(unittest.TestCase):
    def test_traversal_rejected(self):
        repo = make_repo({'a.py': 'x'})
        rel, reason = normalize_rel_path('../../etc/passwd', repo)
        self.assertIsNone(rel)
        self.assertIn('traversal', reason)

    def test_absolute_rejected(self):
        repo = make_repo({'a.py': 'x'})
        rel, reason = normalize_rel_path('/etc/passwd', repo)
        self.assertIsNone(rel)
        self.assertIn('absoluta', reason)

    def test_valid_path_passes(self):
        repo = make_repo({'src/app.py': 'x'})
        rel, reason = normalize_rel_path('./src/app.py', repo)
        self.assertEqual(rel, 'src/app.py')
        self.assertIsNone(reason)


class CollectTests(unittest.TestCase):
    def test_missing_reported_and_valid_continue(self):
        repo = make_repo({'a.py': 'x', 'app.py': 'y'})
        infos, missing, _ = collect_files(repo, ['a.py', 'no_existe.py'])
        self.assertEqual([f.rel_path for f in infos], ['a.py'])
        self.assertEqual(missing, ['no_existe.py'])

    def test_suggestion_for_close_match(self):
        sugg = suggest_for_missing(['ap.py'], ['app.py', 'main.py'])
        self.assertIn('app.py', sugg.get('ap.py', []))

    def test_secret_never_extracted_even_if_requested(self):
        repo = make_repo({'.env': 'SECRET=1', 'a.py': 'x'})
        infos, missing, _ = collect_files(repo, ['.env', 'a.py'])
        self.assertEqual([f.rel_path for f in infos], ['a.py'])
        self.assertEqual(missing, ['.env'])

    def test_directory_expansion(self):
        repo = make_repo({'src/a.py': 'x', 'src/sub/b.py': 'y', 'src/env.key': 'z'})
        infos, _, _ = collect_files(repo, ['src'])
        rels = [f.rel_path for f in infos]
        # dirs primero: sub/b.py antes que a.py
        self.assertEqual(rels, ['src/sub/b.py', 'src/a.py'])

    def test_glob_expansion(self):
        repo = make_repo({'src/a.py': 'x', 'src/b.txt': 'y', 'other/c.py': 'z'})
        infos, _, _ = collect_files(repo, ['src/**/*.py'])
        self.assertEqual([f.rel_path for f in infos], ['src/a.py'])

    def test_too_large_becomes_stub_not_content(self):
        repo = make_repo({'big.txt': 'x' * 5000})
        infos, _, _ = collect_files(repo, ['big.txt'], max_file_kb=1)
        self.assertEqual(len(infos), 0)  # too_large no entra al custom


if __name__ == '__main__':
    unittest.main()
