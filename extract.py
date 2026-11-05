# extract.py
"""Extract: arma el paquete final de archivos que pidió el LLM.

Lee los archivos DESDE EL DISCO con las mismas reglas del escáner (secretos,
binarios, tamaño). Los paths pueden venir de:
  - argumentos:            python extract.py src/app.py README.md
  - un archivo de lista:   python extract.py --from-file paths.txt
  - stdin:                 cat lista.txt | python extract.py
  - interactivo (sin args): pegá la respuesta cruda del LLM y terminá con
    una línea vacía.

El parser es tolerante: si hay un bloque ```paths usa solo ese; si no,
toma cada línea no vacía. Limpia bullets, backticks, comillas, el prefijo
`./` y backslashes. Soporta globs y directorios (expansión recursiva).
"""

from __future__ import annotations

import argparse
import difflib
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

from config import MAX_FILE_KB
from render import FileInfo, format_tokens, render_full
from scanner import (
    _BINARY_SNIFF_BYTES,
    _is_inside_output,
    is_secret_path,
    rel_path_ignored,
    sort_key,
)

GLOB_CHARS = set('*?[')

_BULLET_RE = re.compile(r'^\s*(?:[-*•]|\d+[.)])\s+')


# ---------------------------------------------------------------------------
# Parser tolerante de la respuesta del LLM
# ---------------------------------------------------------------------------

def clean_path_line(raw: str) -> str:
    s = raw.strip()
    s = _BULLET_RE.sub('', s)
    s = s.strip('`"\'')
    s = s.replace('\\', '/')
    s = re.sub(r'^\./+', '', s)
    return s.strip()


def parse_path_list(raw: str) -> list[str]:
    """Extrae paths de una respuesta cruda. Un bloque ```paths gana."""
    m = re.search(r'```paths\s*\n(.*?)(?:```|$)', raw, re.DOTALL)
    lines = m.group(1).splitlines() if m else raw.splitlines()
    out = []
    for line in lines:
        cleaned = clean_path_line(line)
        if not cleaned:
            continue
        # Comentario inline ("path.py # nota") y prosa del LLM: los paths y
        # los globs nunca llevan espacios, así que lo demás se descarta.
        cleaned = re.split(r'\s+#', cleaned)[0].strip()
        if cleaned and ' ' not in cleaned:
            out.append(cleaned)
    return out


# ---------------------------------------------------------------------------
# Seguridad: nada que resuelva fuera del repo
# ---------------------------------------------------------------------------

def normalize_rel_path(raw: str, repo: Path) -> tuple[str | None, str | None]:
    """Devuelve (rel_path, motivo_de_rechazo). Exactamente uno es None."""
    s = clean_path_line(raw)
    if not s:
        return None, None
    if s.startswith('/') or re.match(r'^[A-Za-z]:', s):
        return None, f'ruta absoluta rechazada: {s}'
    parts = [p for p in s.split('/') if p not in ('', '.')]
    if not parts:
        return None, None
    if any(p == '..' for p in parts):
        return None, f'path traversal rechazado: {s}'
    rel = '/'.join(parts)
    resolved = (repo / rel).resolve()
    if not resolved.is_relative_to(repo.resolve()):
        return None, f'path fuera del repo rechazado: {s}'
    return rel, None


# ---------------------------------------------------------------------------
# Lectura de archivos desde el disco (mismas reglas que el escáner)
# ---------------------------------------------------------------------------

def read_file_info(repo: Path, rel: str, max_bytes: int, out_dir: Path | None) -> FileInfo | None:
    abs_path = repo / rel
    name = rel.split('/')[-1]

    if is_secret_path(name, rel):
        return None  # los secretos nunca se entregan, ni a pedido
    if not abs_path.is_file():
        return None
    if out_dir is not None and _is_inside_output(abs_path, out_dir):
        return None

    try:
        with open(abs_path, 'rb') as f:
            head = f.read(_BINARY_SNIFF_BYTES)
            if b'\x00' in head:
                return None  # binario: se omite por completo
            data = head + f.read() if len(head) == _BINARY_SNIFF_BYTES else head
    except OSError:
        return FileInfo(rel, str(abs_path), 0, 0, 0, None, 'unreadable')

    size = len(data)
    if size > max_bytes:
        return FileInfo(rel, str(abs_path), size, 0, 0, None, 'too_large')

    from tokens import estimate_tokens
    text = data.decode('utf-8', errors='replace')
    lines = data.count(b'\n') + (1 if data and not data.endswith(b'\n') else 0)
    return FileInfo(rel, str(abs_path), size, lines, estimate_tokens(text), text)


def _walk_dir_files(repo: Path, rel_dir: str) -> list[str]:
    found = []
    base = repo / rel_dir
    for root, dirs, files in os.walk(str(base), topdown=True, followlinks=False):
        rel_root = Path(root).resolve().relative_to(repo.resolve()).as_posix()
        for name in files:
            rel = f'{rel_root}/{name}' if rel_root != '.' else name
            if is_secret_path(name, rel) or rel_path_ignored(rel):
                continue
            found.append(rel)
    return found


def _expand_glob(repo: Path, pattern: str) -> list[str]:
    import glob as globmod
    matches = globmod.glob(str(repo / pattern), recursive=True)
    out = []
    for m in matches:
        p = Path(m)
        if not p.is_file():
            continue
        rel = p.resolve().relative_to(repo.resolve()).as_posix()
        if is_secret_path(p.name, rel) or rel_path_ignored(rel):
            continue
        out.append(rel)
    return out


# ---------------------------------------------------------------------------
# Selección
# ---------------------------------------------------------------------------

def collect_files(
    repo: Path,
    requested: list[str],
    max_file_kb: int = MAX_FILE_KB,
    out_dir: Path | None = None,
) -> tuple[list[FileInfo], list[str], list[tuple[str, str]]]:
    """Devuelve (infos_encontrados, faltantes, rechazados)."""
    max_bytes = max_file_kb * 1024
    selected: dict[str, None] = {}
    direct_requests: list[tuple[str, str]] = []  # (raw, rel) pedidos uno a uno
    missing: list[str] = []
    rejected: list[tuple[str, str]] = []

    for raw in requested:
        rel, reject_reason = normalize_rel_path(raw, repo)
        if reject_reason:
            rejected.append((raw, reject_reason))
            continue
        if not rel:
            continue
        target = repo / rel
        if target.is_dir():
            for f in _walk_dir_files(repo, rel):
                selected.setdefault(f, None)
        elif any(c in rel for c in GLOB_CHARS):
            matches = _expand_glob(repo, rel)
            if matches:
                for f in matches:
                    selected.setdefault(f, None)
            else:
                missing.append(raw)
        elif target.is_file():
            if not any(r == rel for _, r in direct_requests):
                direct_requests.append((raw, rel))
        else:
            missing.append(raw)

    to_read = set(selected) | {rel for _, rel in direct_requests}
    infos = []
    for rel in sorted(to_read, key=sort_key):
        info = read_file_info(repo, rel, max_bytes, out_dir)
        if info is not None and info.skipped_reason is None:
            infos.append(info)
    infos.sort(key=lambda f: sort_key(f.rel_path))

    # Un pedido explícito que el lector descartó (secreto, binario, too_large)
    # se reporta como faltante en vez de desaparecer en silencio.
    delivered = {f.rel_path for f in infos}
    for raw, rel in direct_requests:
        if rel not in delivered:
            missing.append(raw)

    return infos, missing, rejected


def suggest_for_missing(missing: list[str], universe: list[str], n: int = 3) -> dict[str, list[str]]:
    """Sugerencias difusas para los paths inexistentes."""
    suggestions = {}
    for m in missing:
        close = difflib.get_close_matches(m, universe, n=n, cutoff=0.6)
        if close:
            suggestions[m] = close
    return suggestions


def find_latest_manifest(output_root: Path) -> Path | None:
    """El manifest.json más reciente entre output/<repo>/manifest.json."""
    if not output_root.is_dir():
        return None
    candidates = sorted(
        output_root.glob('*/manifest.json'), key=lambda p: p.stat().st_mtime, reverse=True
    )
    return candidates[0] if candidates else None


# ---------------------------------------------------------------------------
# Portapapeles (best-effort, silencioso si no hay comando)
# ---------------------------------------------------------------------------

def copy_to_clipboard(text: str) -> bool:
    commands = [['pbcopy'], ['clip'], ['xclip', '-selection', 'clipboard'], ['xsel', '--clipboard']]
    for cmd in commands:
        try:
            proc = subprocess.run(cmd, input=text.encode('utf-8'), capture_output=True, timeout=10)
            if proc.returncode == 0:
                return True
        except (OSError, subprocess.TimeoutExpired):
            continue
    return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _read_requested(args, output_root: Path) -> tuple[str, Path | None]:
    if args.from_file:
        return Path(args.from_file).read_text(encoding='utf-8', errors='replace'), None
    if args.paths:
        return '\n'.join(args.paths), None
    if not sys.stdin.isatty():
        return sys.stdin.read(), None
    # Modo interactivo: pegar la respuesta del LLM y terminar con línea vacía.
    print('Pegá la respuesta del LLM (paths, bullets, lo que sea).')
    print('Terminá con una línea vacía (Ctrl+D también sirve).')
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == '':
            break
        lines.append(line)
    return '\n'.join(lines), None


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Extrae del repo los archivos que pidió el LLM y arma un solo .txt.'
    )
    parser.add_argument('paths', nargs='*', help='paths relativos al repo (también globs y directorios)')
    parser.add_argument('--from-file', metavar='FILE', help='archivo con la lista de paths')
    parser.add_argument('--repo', metavar='PATH', help='repo de origen (default: manifest más reciente)')
    parser.add_argument('--out', metavar='DIR', help='raíz de salidas (default: <script>/output)')
    parser.add_argument('--max-file-kb', type=int, default=MAX_FILE_KB)
    parser.add_argument('--copy', action='store_true', help='copiar el resultado al portapapeles (best-effort)')
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    output_root = Path(args.out).expanduser() if args.out else script_dir / 'output'

    manifest_path = find_latest_manifest(output_root)
    if args.repo:
        repo = Path(args.repo).expanduser().resolve()
    elif manifest_path is not None:
        import json
        data = json.loads(manifest_path.read_text(encoding='utf-8'))
        repo = Path(data['repo_path'])
        print(f'📎 Repo de origen (manifest más reciente): {repo}')
    else:
        print('[ERROR] No hay manifest.json en output/ y no pasaste --repo.')
        sys.exit(1)

    if not repo.is_dir():
        print(f'[ERROR] El repo de origen no existe: {repo}')
        sys.exit(1)

    raw_text, _ = _read_requested(args, output_root)
    if not raw_text.strip():
        print('[ERROR] Lista de paths vacía.')
        sys.exit(1)

    requested = parse_path_list(raw_text)
    infos, missing, rejected = collect_files(repo, requested, args.max_file_kb, output_root)

    # Sugerencias para los faltantes, contra los archivos conocidos del repo.
    universe: list[str] = []
    if manifest_path is not None:
        import json
        universe = [f['path'] for f in json.loads(
            manifest_path.read_text(encoding='utf-8'))['files'] if not f['skipped']]
    if not universe:
        universe = _walk_dir_files(repo, '.')

    if missing:
        print(f'\n[WARN] {len(missing)} path(s) no encontrados:')
        for m in missing:
            sugg = suggest_for_missing([m], universe)
            hint = f'  ¿quisiste decir: {", ".join(sugg[m])}?' if m in sugg else ''
            print(f'  - {m}{hint}')

    if rejected:
        print(f'\n[RECHAZADOS] {len(rejected)} path(s) por seguridad:')
        for raw, reason in rejected:
            print(f'  - {reason}')

    if not infos:
        print('\n[ERROR] Ningún archivo válido para extraer.')
        sys.exit(1)

    content = render_full(infos)
    out_path = output_root / repo.name / '3_custom.txt'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding='utf-8')

    total_tokens = sum(f.tokens for f in infos)
    print(f'\n[OK] {len(infos)} archivo(s) -> {out_path} ({format_tokens(total_tokens)})')
    for f in infos:
        print(f'  - {f.rel_path}')

    if args.copy and copy_to_clipboard(content):
        print('📋 Copiado al portapapeles.')


if __name__ == '__main__':
    main()
