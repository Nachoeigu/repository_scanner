# render.py
"""Renderizado de las salidas pensadas para LLM.

- `1_overview.txt`: árbol anotado + README recortado (+ outline opcional).
- `2_full.txt`: UN solo archivo de contenidos, crudo y sin CDATA.
- `manifest.json`: metadatos por archivo; lo usa extract.
"""

from __future__ import annotations

import ast
import json
import re
import xml.sax.saxutils as saxutils
from datetime import date
from pathlib import Path

from config import (
    ENTRYPOINT_FILENAMES,
    ENTRYPOINT_PREFIXES,
    INSTRUCTIONS,
    LANG_BY_EXT,
    MAX_ENTRIES_PER_DIR,
)
from scanner import FileInfo, ScanResult


def format_tokens(n: int) -> str:
    if n < 1000:
        return f"~{n}t"
    if n < 1_000_000:
        return f"~{n / 1000:.1f}k"
    return f"~{n / 1_000_000:.1f}M"


def format_size(n: int) -> str:
    if n < 1024:
        return f"{n}B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f}KB"
    return f"{n / (1024 * 1024):.1f}MB"


def _attr(value: str) -> str:
    """Escapa un valor para atributo XML."""
    return saxutils.quoteattr(str(value))[1:-1] if value is not None else '""'


# ---------------------------------------------------------------------------
# Descripciones de una línea (solo si salen baratas)
# ---------------------------------------------------------------------------

def file_description(info: FileInfo) -> str:
    text = info.text
    if not text:
        return ''
    suffix = Path(info.rel_path).suffix.lower()
    name = Path(info.rel_path).name.lower()
    try:
        if suffix == '.py':
            tree = ast.parse(text[:65536])
            doc = ast.get_docstring(tree)
            if doc:
                return doc.strip().splitlines()[0][:100]
        elif suffix in ('.md', '.rst'):
            for line in text.splitlines():
                if line.startswith('#'):
                    return line.lstrip('#').strip()[:100]
        elif name == 'package.json':
            desc = json.loads(text).get('description')
            return str(desc)[:100] if desc else ''
        elif name == 'pyproject.toml':
            m = re.search(r'^description\s*=\s*"([^"]+)"', text, re.MULTILINE)
            if m:
                return m.group(1)[:100]
    except Exception:
        pass
    return ''


# ---------------------------------------------------------------------------
# Outline (--outline): mapa de símbolos por archivo
# ---------------------------------------------------------------------------

_JS_SYMBOL_RE = re.compile(
    r'^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(function|class|const|let)\s+([A-Za-z_$][\w$]*)',
    re.MULTILINE,
)


def file_outline(info: FileInfo) -> list[str]:
    text = info.text
    if not text:
        return []
    suffix = Path(info.rel_path).suffix.lower()
    out: list[str] = []
    try:
        if suffix == '.py':
            tree = ast.parse(text[:262144])
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    kind = 'async def' if isinstance(node, ast.AsyncFunctionDef) else 'def'
                    try:
                        args = ast.unparse(node.args)
                    except Exception:
                        args = '...'
                    out.append(f'  {kind} {node.name}({args})')
                elif isinstance(node, ast.ClassDef):
                    out.append(f'  class {node.name}')
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    doc = ast.get_docstring(node)
                    if doc:
                        out.append(f'      # {doc.strip().splitlines()[0][:90]}')
        elif suffix in ('.js', '.ts', '.jsx', '.tsx'):
            for m in _JS_SYMBOL_RE.finditer(text):
                out.append(f'  {m.group(1)} {m.group(2)}')
    except SyntaxError:
        return []
    return out


# ---------------------------------------------------------------------------
# Árbol ASCII
# ---------------------------------------------------------------------------

def _build_filetree(files: list[FileInfo]) -> dict:
    tree: dict = {}
    for info in files:
        node = tree
        parts = info.rel_path.split('/')
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = info
    return tree


def _render_tree(node: dict, prefix: str = '', lines_out: list[str] | None = None) -> list[str]:
    if lines_out is None:
        lines_out = []

    dirs = sorted(
        (k for k, v in node.items() if isinstance(v, dict)),
        key=str.lower,
    )
    files = sorted(
        ((k, v) for k, v in node.items() if isinstance(v, FileInfo)),
        key=lambda kv: kv[0].lower(),
    )
    entries = [(d, None) for d in dirs] + files

    total = len(entries)
    collapsed = total > MAX_ENTRIES_PER_DIR
    shown = entries[:MAX_ENTRIES_PER_DIR] if collapsed else entries

    for i, (name, info) in enumerate(shown):
        is_last_visible = (i == len(shown) - 1) and not collapsed
        connector = '└── ' if is_last_visible else '├── '
        if info is None:
            lines_out.append(f'{prefix}{connector}{name}/')
            _render_tree(node[name], prefix + ('    ' if is_last_visible else '│   '), lines_out)
        else:
            lines_out.append(f'{prefix}{connector}{_file_line(info)}')

    if collapsed:
        lines_out.append(f'{prefix}└── ... (+{total - len(shown)} más)')
    return lines_out


def _file_line(info: FileInfo) -> str:
    if info.skipped_reason == 'too_large':
        return f'{Path(info.rel_path).name}  (omitido: too_large, {format_size(info.size)})'
    if info.skipped_reason == 'unreadable':
        return f'{Path(info.rel_path).name}  (omitido: unreadable)'
    desc = file_description(info)
    suffix = f'  # {desc}' if desc else ''
    return f'{Path(info.rel_path).name}  {info.lines}L  {format_tokens(info.tokens)}{suffix}'


def build_tree_text(scan: ScanResult) -> str:
    lines = [f'{scan.repo_name}/']
    lines.extend(_render_tree(_build_filetree(scan.files)))
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Métricas del overview
# ---------------------------------------------------------------------------

def language_stats(scan: ScanResult) -> str:
    by_lang: dict[str, int] = {}
    total = 0
    for info in scan.included:
        ext = Path(info.rel_path).suffix.lower()
        lang = LANG_BY_EXT.get(ext)
        if not lang:
            continue
        by_lang[lang] = by_lang.get(lang, 0) + info.lines
        total += info.lines
    if total == 0:
        return ''
    parts = sorted(by_lang.items(), key=lambda kv: -kv[1])
    return ', '.join(f'{lang} {100 * lines // total}%' for lang, lines in parts[:4])


def entrypoints(scan: ScanResult) -> list[str]:
    names = {Path(f.rel_path).name.lower() for f in scan.included}
    found = []
    for f in scan.included:
        name = Path(f.rel_path).name
        if name.lower() in [n.lower() for n in ENTRYPOINT_FILENAMES] or any(
            name.lower().startswith(p) for p in ENTRYPOINT_PREFIXES
        ):
            found.append(f.rel_path)
    return found


def summary_line(scan: ScanResult) -> str:
    files = len(scan.included)
    total_lines = sum(f.lines for f in scan.included)
    total_tokens = sum(f.tokens for f in scan.included)
    langs = language_stats(scan)
    parts = [f'files: {files}', f'lines: {total_lines}', f'~tokens: {format_tokens(total_tokens)[1:]}']
    if langs:
        parts.append(f'languages: {langs}')
    return ' · '.join(parts)


def root_readme(scan: ScanResult) -> FileInfo | None:
    for f in scan.included:
        name = Path(f.rel_path).name.lower()
        if Path(f.rel_path).parent == Path('.') and name.startswith('readme'):
            return f
    return None


# ---------------------------------------------------------------------------
# Salidas
# ---------------------------------------------------------------------------

def render_overview(scan: ScanResult, readme_max_chars: int = 2000, outline: bool = False) -> str:
    out: list[str] = []
    commit_attr = f' commit="{_attr(scan.commit)}"' if scan.commit else ''
    out.append(
        f'<repo_overview name="{_attr(scan.repo_name)}"{commit_attr} '
        f'generated="{date.today().isoformat()}">'
    )
    out.append(f'<summary>{summary_line(scan)}</summary>')

    eps = entrypoints(scan)
    if eps:
        out.append(f'<entrypoints>{", ".join(eps)}</entrypoints>')

    out.append('<tree>')
    out.append(build_tree_text(scan))
    out.append('</tree>')

    readme = root_readme(scan)
    if readme and readme.text:
        text = readme.text
        truncated = len(text) > readme_max_chars
        shown = text[:readme_max_chars] if truncated else text
        out.append(
            f'<readme chars="{len(shown)}/{len(text)}" truncated="{"true" if truncated else "false"}">'
        )
        out.append(shown)
        out.append('</readme>')

    if outline:
        out.append('<outline>')
        for f in scan.included:
            syms = file_outline(f)
            if syms:
                out.append(f.rel_path)
                out.extend(syms)
        out.append('</outline>')

    out.append('<instructions>')
    out.append(INSTRUCTIONS)
    out.append('</instructions>')
    out.append('</repo_overview>')
    return '\n'.join(out) + '\n'


def render_full(files: list[FileInfo], line_numbers: bool = False) -> str:
    """UN solo archivo de contenidos: crudo, sin CDATA ni escapes."""
    out = ['<documents>']
    for i, info in enumerate(files, start=1):
        attrs = f'index="{i}" lines="{info.lines}" tokens="{info.tokens}"'
        if info.skipped_reason:
            attrs += f' skipped="{info.skipped_reason}" size="{info.size}"'
        out.append(f'<document {attrs}>')
        out.append(f'<source>{info.rel_path}</source>')
        if info.text is not None:
            out.append('<document_content>')
            text = info.text
            if line_numbers:
                text = ''.join(
                    f'{n + 1:>5}  {line}\n'
                    for n, line in enumerate(text.splitlines(keepends=True))
                )
            # El contenido va tal cual; solo se garantiza salto de línea
            # antes del cierre para que la etiqueta no quede pegada.
            if text and not text.endswith('\n'):
                text += '\n'
            out.append(text)
            out.append('</document_content>')
        out.append('</document>')
    out.append('</documents>')
    return '\n'.join(out) + '\n'


def render_manifest(scan: ScanResult) -> str:
    data = {
        'repo_path': str(scan.repo_path.resolve()),
        'repo_name': scan.repo_name,
        'commit': scan.commit,
        'generated': date.today().isoformat(),
        'files': [
            {
                'path': f.rel_path,
                'lines': f.lines,
                'tokens': f.tokens,
                'skipped': f.skipped_reason,
            }
            for f in scan.files
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + '\n'
