# tests/test_scanner.py
"""Tests del escáner: filtros, secretos, binarios, tamaño, autoexclusión."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scanner import FileInfo, ScanResult, clean_input_path, scan_repository, sort_key


def make_repo(files: dict[str, str]) -> Path:
    tmp = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content.encode('utf-8') if isinstance(content, str) else content)
    return tmp


class ScannerTests(unittest.TestCase):
    def scan(self, files: dict, out_name: str = 'output', **kwargs):
        repo = make_repo(files)
        out = repo / out_name
        result = scan_repository(repo, out, **kwargs)
        return repo, result

    def test_secret_files_never_appear(self):
        repo, scan = self.scan({
            '.env': 'SECRET=1',
            '.env.local': 'X=2',
            'server.pem': 'key',
            'id_rsa': 'key',
            'credentials.json': '{}',
            'my_secret.txt': 'x',
            'app.py': 'print(1)',
        })
        rels = [f.rel_path for f in scan.files]
        self.assertEqual(rels, ['app.py'])
        self.assertEqual(len(scan.secrets_skipped), 6)

    def test_case_insensitive_extensions(self):
        _, scan = self.scan({'LOGO.PNG': 'x', 'photo.Png': 'x', 'keep.py': 'y'})
        rels = [f.rel_path for f in scan.files]
        self.assertEqual(rels, ['keep.py'])

    def test_binary_omitted_completely(self):
        _, scan = self.scan({'data.dat': b'\x00\x01\x02', 'code.py': 'x'})
        self.assertEqual([f.rel_path for f in scan.files], ['code.py'])
        self.assertEqual(scan.binaries_skipped, 1)

    def test_too_large_shows_as_stub(self):
        repo = make_repo({'big.txt': 'x' * 5000, 'small.py': 'y'})
        scan = scan_repository(repo, repo / 'output', max_file_kb=1)
        big_info = [f for f in scan.files if f.rel_path == 'big.txt'][0]
        self.assertEqual(big_info.skipped_reason, 'too_large')
        self.assertIsNone(big_info.text)
        self.assertEqual([f.rel_path for f in scan.included], ['small.py'])

    def test_empty_file_included(self):
        _, scan = self.scan({'empty.py': '', 'b.py': 'x\n'})
        empty = [f for f in scan.included if f.rel_path == 'empty.py'][0]
        self.assertEqual(empty.lines, 0)
        self.assertEqual(empty.text, '')

    def test_output_dir_auto_excluded(self):
        repo, scan = self.scan({
            'output/2_full.txt': 'viejo',
            'app.py': 'x',
        })
        rels = [f.rel_path for f in scan.files]
        self.assertNotIn('output/2_full.txt', rels)
        self.assertEqual(rels, ['app.py'])

    def test_symlink_loop_does_not_hang(self):
        repo = make_repo({'app.py': 'x'})
        os.symlink(str(repo), str(repo / 'loop'))
        scan = scan_repository(repo, repo / 'output', use_gitignore=False)
        self.assertEqual([f.rel_path for f in scan.files], ['app.py'])

    def test_root_readme_included(self):
        _, scan = self.scan({'README.md': '# Hola\n', 'app.py': 'x'})
        rels = [f.rel_path for f in scan.included]
        self.assertIn('README.md', rels)

    def test_dir_filters_apply_per_segment(self):
        _, scan = self.scan({'node_modules/pkg/index.js': 'x', 'src/app.py': 'y'})
        self.assertEqual([f.rel_path for f in scan.files], ['src/app.py'])

    def test_gitignore_respected_and_flag(self):
        repo = make_repo({'keep.py': 'x', 'build_out.txt': 'ruido'})
        subprocess.run(['git', 'init', '-q'], cwd=str(repo), check=True, capture_output=True)
        (repo / '.gitignore').write_text('build_out.txt\n')
        scan = scan_repository(repo, repo / 'output', use_gitignore=True)
        self.assertEqual([f.rel_path for f in scan.files], ['keep.py'])
        scan2 = scan_repository(repo, repo / 'output', use_gitignore=False)
        self.assertIn('build_out.txt', [f.rel_path for f in scan2.files])

    def test_commit_detected_only_in_git_repo(self):
        repo = make_repo({'app.py': 'x'})
        scan = scan_repository(repo, repo / 'output')
        self.assertIsNone(scan.commit)
        subprocess.run(['git', 'init', '-q'], cwd=str(repo), check=True, capture_output=True)
        subprocess.run(
            ['git', '-c', 'user.email=t@t', '-c', 'user.name=t',
             'commit', '--allow-empty', '-q', '-m', 'init'],
            cwd=str(repo), check=True, capture_output=True,
        )
        scan2 = scan_repository(repo, repo / 'output')
        self.assertIsNotNone(scan2.commit)

    def test_sort_dirs_first_case_insensitive(self):
        self.assertEqual(
            sort_key('B/c.txt'), sort_key('b/c.txt')
        )
        self.assertLess(sort_key('B/c.txt'), sort_key('a.txt'))
        self.assertLess(sort_key('a.txt'), sort_key('B.txt'))


if __name__ == '__main__':
    unittest.main()
