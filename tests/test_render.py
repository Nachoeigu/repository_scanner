# tests/test_render.py
"""Tests del render: contenido idéntico, overview barato, colapso, manifest."""

import re
import tempfile
import unittest
from pathlib import Path

from render import (
    build_tree_text,
    format_tokens,
    render_full,
    render_manifest,
    render_overview,
)
from scanner import FileInfo, ScanResult


def make_scan(files: dict[str, str], name: str = 'repo') -> ScanResult:
    tmp = Path(tempfile.mkdtemp())
    infos = []
    for i, (rel, text) in enumerate(files.items()):
        abs_p = tmp / rel
        abs_p.parent.mkdir(parents=True, exist_ok=True)
        abs_p.write_text(text, encoding='utf-8')
        lines = text.count('\n') + (1 if text and not text.endswith('\n') else 0)
        infos.append(FileInfo(rel, str(abs_p), len(text.encode()), lines, len(text) // 4, text))
    from scanner import sort_key
    infos.sort(key=lambda f: sort_key(f.rel_path))
    return ScanResult(repo_path=tmp, repo_name=name, commit='a1b2c3d', files=infos)


def content_of(full: str, rel_path: str) -> str:
    m = re.search(
        rf'<source>{re.escape(rel_path)}</source>\n<document_content>\n(.*?)\n</document_content>',
        full, re.DOTALL,
    )
    return m.group(1) if m else ''


class RenderTests(unittest.TestCase):
    def test_content_identical_no_cdata_mangling(self):
        tricky = 'Texto feo: "quotes", \\backslash\\, \ttab y línea\nsin salto final'
        scan = make_scan({'src/app.py': tricky})
        full = render_full(scan.files)
        self.assertNotIn('<![CDATA[', full)
        # Contrato: contenido tal cual, más un único salto de línea antes
        # del cierre si el original no terminaba en '\n'.
        expected = tricky if tricky.endswith('\n') else tricky + '\n'
        self.assertEqual(content_of(full, 'src/app.py'), expected)

    def test_empty_file_render(self):
        scan = make_scan({'empty.txt': '', 'a.py': 'x'})
        full = render_full(scan.files)
        self.assertIn('<document index="2" lines="0" tokens="0">', full)
        self.assertIn('<source>empty.txt</source>', full)

    def test_line_numbers_flag(self):
        scan = make_scan({'a.py': 'uno\ndos\n'})
        plain = render_full(scan.files)
        numbered = render_full(scan.files, line_numbers=True)
        self.assertNotIn('1  uno', plain)
        self.assertIn('1  uno', numbered)

    def test_too_large_stub_in_full(self):
        info = FileInfo('big.bin', '/x/big.bin', 999999, 0, 0, None, 'too_large')
        scan = make_scan({})
        scan.files = [info]
        full = render_full(scan.files)
        self.assertIn('skipped="too_large"', full)
        self.assertNotIn('<document_content>', full)

    def test_overview_budget_under_10_percent(self):
        files = {}
        for i in range(30):
            files[f'src/mod_{i:02}.py'] = f'"""Módulo {i}."""\n' + f'x = {i}\n' * 300
        files['README.md'] = '# Repo\n' + 'texto\n' * 200
        scan = make_scan(files)
        overview = render_overview(scan)
        full = render_full(scan.files)
        ratio = len(overview) / len(full)
        self.assertLess(ratio, 0.10, f'overview ocupa {ratio:.1%} del full')

    def test_tree_collapse_with_more_entry(self):
        files = {f'dir/f_{i:02}.py': 'x' for i in range(20)}
        scan = make_scan(files)
        tree = build_tree_text(scan)
        self.assertIn('(+5 más)', tree)

    def test_overview_readme_truncated_flag(self):
        scan = make_scan({'README.md': '#' + 'x' * 5000})
        overview = render_overview(scan, readme_max_chars=100)
        self.assertIn('truncated="true"', overview)

    def test_manifest_fields(self):
        scan = make_scan({'a.py': 'x\n', 'big.bin': 'y'})
        scan.files.append(FileInfo('big.bin', '/x/big.bin', 99999, 0, 0, None, 'too_large'))
        import json
        data = json.loads(render_manifest(scan))
        self.assertEqual(data['repo_name'], 'repo')
        self.assertEqual(data['commit'], 'a1b2c3d')
        paths = [f['path'] for f in data['files']]
        self.assertIn('a.py', paths)
        skipped = [f for f in data['files'] if f['skipped']]
        self.assertEqual(skipped[0]['skipped'], 'too_large')

    def test_format_tokens(self):
        self.assertEqual(format_tokens(0), '~0t')
        self.assertEqual(format_tokens(900), '~900t')
        self.assertEqual(format_tokens(4200), '~4.2k')
        self.assertEqual(format_tokens(2_500_000), '~2.5M')


if __name__ == '__main__':
    unittest.main()
