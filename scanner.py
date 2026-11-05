# scanner.py
"""Escaneo del repositorio: UNA sola pasada, UNA sola lectura por archivo.

Todo lo demás (árbol, overview, volcado, extract) se renderiza desde la
lista de FileInfo que devuelve `scan_repository`.
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from config import (
    DEFAULT_FILE_GLOBS,
    DIRECTORIES_TO_IGNORE,
    DIRECTORIES_TO_IGNORE_BASED_ON_REGEX,
    FILES_TO_IGNORE,
    FILES_TO_IGNORE_BASED_ON_REGEX,
    MAX_FILE_KB,
    SECRET_PATTERNS,
)
from tokens import estimate_tokens

# Binario = byte NUL dentro de los primeros 8192 bytes.
_BINARY_SNIFF_BYTES = 8192


@dataclass
class FileInfo:
    rel_path: str                     # siempre con separador '/'
    abs_path: str
    size: int                         # bytes
    lines: int
    tokens: int
    text: str | None                  # None si skipped
    skipped_reason: str | None = None  # None | "too_large" | "unreadable"


@dataclass
class ScanResult:
    repo_path: Path
    repo_name: str
    commit: str | None
    files: list[FileInfo] = field(default_factory=list)  # incluidos + too_large/unreadable
    secrets_skipped: list[str] = field(default_factory=list)
    binaries_skipped: int = 0

    @property
    def included(self) -> list[FileInfo]:
        """Solo archivos con contenido real."""
        return [f for f in self.files if f.skipped_reason is None]

    @property
    def skipped_too_large(self) -> list[FileInfo]:
        return [f for f in self.files if f.skipped_reason == 'too_large']

    @property
    def skipped_unreadable(self) -> list[FileInfo]:
        return [f for f in self.files if f.skipped_reason == 'unreadable']


# ---------------------------------------------------------------------------
# Filtros (todos case-insensitive)
# ---------------------------------------------------------------------------

def _matches_exact(name: str, exact: list[str]) -> bool:
    low = name.lower()
    return any(e.lower() == low for e in exact)


def _matches_regex(name: str, patterns: list[str]) -> bool:
    return any(re.search(p, name, re.IGNORECASE) for p in patterns)


def _matches_glob(name: str, rel_path: str, globs: list[str]) -> bool:
    low_name = name.lower()
    low_rel = rel_path.lower()
    return any(
        fnmatch.fnmatchcase(low_name, g.lower()) or fnmatch.fnmatchcase(low_rel, g.lower())
        for g in globs
    )


def is_secret_path(name: str, rel_path: str) -> bool:
    """Los secretos se checan primero y nada los puede reincluir."""
    return _matches_glob(name, rel_path, SECRET_PATTERNS)


def _dir_segment_ignored(segment: str) -> bool:
    return (
        _matches_exact(segment, DIRECTORIES_TO_IGNORE)
        or _matches_regex(segment, DIRECTORIES_TO_IGNORE_BASED_ON_REGEX)
    )


def _file_ignored(name: str, rel_path: str) -> bool:
    return (
        _matches_exact(name, FILES_TO_IGNORE)
        or _matches_regex(name, FILES_TO_IGNORE_BASED_ON_REGEX)
        or _matches_glob(name, rel_path, DEFAULT_FILE_GLOBS)
    )


def rel_path_ignored(rel_path: str) -> bool:
    """Aplica TODOS los filtros de config a una ruta relativa con '/'.

    Se checa cada segmento de directorio también, para que un archivo dentro
    de node_modules/ se ignore aunque venga de `git ls-files`.
    """
    parts = rel_path.split('/')
    for segment in parts[:-1]:
        if _dir_segment_ignored(segment):
            return True
    name = parts[-1]
    if name == '':
        return _dir_segment_ignored(parts[-2]) if len(parts) > 1 else False
    return _file_ignored(name, rel_path)


# ---------------------------------------------------------------------------
# Orden determinista: DFS con directorios primero, alfabético case-insensitive
# ---------------------------------------------------------------------------

def sort_key(rel_path: str):
    parts = rel_path.split('/')
    return tuple(
        (0, part.lower()) for part in parts[:-1]   # directorios primero
    ) + ((1, parts[-1].lower()),)


# ---------------------------------------------------------------------------
# Fuentes de archivos
# ---------------------------------------------------------------------------

def _git_ls_files(repo: Path) -> list[str] | None:
    """`git ls-files --cached --others --exclude-standard`; None si falla."""
    try:
        proc = subprocess.run(
            ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
            cwd=str(repo), capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return [p for p in proc.stdout.decode('utf-8', 'replace').split('\0') if p]


def _walk_files(repo: Path) -> list[str]:
    """os.walk sin seguir symlinks; respeta los mismos filtros de config."""
    found: list[str] = []
    for root, dirs, files in os.walk(str(repo), topdown=True, followlinks=False):
        dirs[:] = [d for d in dirs if not _dir_segment_ignored(d)]
        rel_root = os.path.relpath(root, str(repo))
        for name in files:
            rel = name if rel_root == '.' else f"{rel_root.replace(os.sep, '/')}/{name}"
            found.append(rel)
    return found


# ---------------------------------------------------------------------------
# Escaneo principal
# ---------------------------------------------------------------------------

def clean_input_path(raw: str) -> Path:
    """Normaliza el path ingresado: comillas, expanduser y '\\ ' de drag&drop."""
    cleaned = raw.strip().strip("\"'")
    cleaned = cleaned.replace('\\ ', ' ')
    return Path(cleaned).expanduser()


def _is_inside_output(abs_path: Path, out_dir: Path) -> bool:
    try:
        abs_path.resolve().relative_to(out_dir.resolve())
        return True
    except ValueError:
        return False


def _git_commit(repo: Path) -> str | None:
    try:
        proc = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=str(repo), capture_output=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode().strip() or None


def scan_repository(
    repo_path: Path,
    out_dir: Path,
    use_gitignore: bool = True,
    max_file_kb: int = MAX_FILE_KB,
) -> ScanResult:
    """Escanea el repo una sola vez y devuelve la lista de FileInfo."""
    if not repo_path.is_dir():
        raise NotADirectoryError(f"No es un directorio válido: {repo_path}")

    result = ScanResult(
        repo_path=repo_path,
        repo_name=repo_path.resolve().name,
        commit=_git_commit(repo_path) if (repo_path / '.git').exists() else None,
    )
    max_bytes = max_file_kb * 1024

    if use_gitignore and (repo_path / '.git').exists():
        rels = _git_ls_files(repo_path)
    else:
        rels = None
    if rels is None:
        rels = _walk_files(repo_path)

    for rel in sorted(set(rels)):
        rel = rel.replace(os.sep, '/').strip('/')
        if not rel:
            continue
        name = rel.split('/')[-1]

        # 1) Secretos primero: nada los puede reincluir.
        if is_secret_path(name, rel):
            result.secrets_skipped.append(rel)
            continue
        if rel_path_ignored(rel):
            continue

        abs_path = repo_path / rel
        if not abs_path.is_file():
            continue  # entradas de git que ya no existen en el disco
        if _is_inside_output(abs_path, out_dir):
            continue  # autoexclusión del directorio de salida

        try:
            with open(abs_path, 'rb') as f:
                head = f.read(_BINARY_SNIFF_BYTES)
                if b'\x00' in head:
                    result.binaries_skipped += 1
                    continue
                data = head + f.read() if len(head) == _BINARY_SNIFF_BYTES else head
        except OSError:
            result.files.append(
                FileInfo(rel, str(abs_path), abs_path.stat().st_size
                         if abs_path.exists() else 0,
                         0, 0, None, 'unreadable')
            )
            continue

        size = len(data)
        if size > max_bytes:
            result.files.append(
                FileInfo(rel, str(abs_path), size, 0, 0, None, 'too_large')
            )
            continue

        text = data.decode('utf-8', errors='replace')
        lines = data.count(b'\n') + (1 if data and not data.endswith(b'\n') else 0)
        result.files.append(
            FileInfo(rel, str(abs_path), size, lines, estimate_tokens(text), text)
        )

    result.files.sort(key=lambda f: sort_key(f.rel_path))
    result.secrets_skipped.sort()
    return result
