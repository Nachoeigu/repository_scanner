# main.py
"""Repository Scanner: CLI para volcar un repo a texto listo para un LLM.

Uso:
    python main.py [path] [flags]

Sin path, mantiene el prompt interactivo de siempre.
Salidas en output/<repo_name>/: 1_overview.txt, 2_full.txt, manifest.json.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config import MAX_FILE_KB, README_MAX_CHARS, TOKEN_WARN_THRESHOLD
from render import format_tokens, render_full, render_manifest, render_overview
from scanner import clean_input_path, scan_repository
from tokens import estimate_tokens


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Escanea un repo y genera overview + volcado completo para un LLM.'
    )
    parser.add_argument('path', nargs='?', help='ruta del repo a escanear (si falta, prompt interactivo)')
    parser.add_argument('--out', metavar='DIR', help=f'raíz de salidas (default: <script>/output)')
    parser.add_argument('--max-file-kb', type=int, default=MAX_FILE_KB,
                        help=f'tamaño máximo por archivo en KB (default: {MAX_FILE_KB})')
    parser.add_argument('--outline', action='store_true',
                        help='agregar mapa de símbolos por archivo al overview')
    parser.add_argument('--readme-max-chars', type=int, default=README_MAX_CHARS,
                        help=f'recorte del README en el overview (default: {README_MAX_CHARS})')
    parser.add_argument('--line-numbers', action='store_true',
                        help='numerar las líneas en 2_full.txt')
    parser.add_argument('--no-gitignore', action='store_true',
                        help='ignorar .gitignore y usar os.walk (los filtros de config.py aplican igual)')
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    if args.path:
        raw = args.path
    else:
        raw = input('Put your entire path: ')
    repo = clean_input_path(raw).resolve()

    if not repo.is_dir():
        print(f"\n[ERROR] La ruta '{repo}' no es un directorio válido.")
        return 1

    script_dir = Path(__file__).resolve().parent
    output_root = Path(args.out).expanduser().resolve() if args.out else script_dir / 'output'

    print(f'\n🔍 Escaneando repositorio: {repo}')
    scan = scan_repository(
        repo, output_root,
        use_gitignore=not args.no_gitignore,
        max_file_kb=args.max_file_kb,
    )

    overview_text = render_overview(scan, readme_max_chars=args.readme_max_chars, outline=args.outline)
    full_text = render_full(scan.files, line_numbers=args.line_numbers)
    manifest_text = render_manifest(scan)

    repo_out = output_root / scan.repo_name
    repo_out.mkdir(parents=True, exist_ok=True)
    overview_path = repo_out / '1_overview.txt'
    full_path = repo_out / '2_full.txt'
    manifest_path = repo_out / 'manifest.json'
    overview_path.write_text(overview_text, encoding='utf-8')
    full_path.write_text(full_text, encoding='utf-8')
    manifest_path.write_text(manifest_text, encoding='utf-8')

    # --- Resumen de consola (sin volcar contenido) ---
    included = scan.included
    full_tokens = sum(f.tokens for f in included)
    overview_tokens = estimate_tokens(overview_text)

    print('\n✅ Escaneo terminado.')
    print(f'  Archivos incluidos: {len(included)}')
    if scan.skipped_too_large:
        print(f'  Omitidos por tamaño: {len(scan.skipped_too_large)} '
              f'({", ".join(f.rel_path for f in scan.skipped_too_large[:5])})')
    if scan.skipped_unreadable:
        print(f'  Ilegibles: {len(scan.skipped_unreadable)} '
              f'({", ".join(f.rel_path for f in scan.skipped_unreadable[:5])})')
    if scan.binaries_skipped:
        print(f'  Binarios omitidos: {scan.binaries_skipped}')
    if scan.secrets_skipped:
        # Se listan a propósito: ayuda a detectar falsos positivos del glob.
        print(f'  🔒 Secretos omitidos ({len(scan.secrets_skipped)}): '
              + ', '.join(scan.secrets_skipped[:10]))

    print(f'\n  Tokens estimados del volcado completo: {format_tokens(full_tokens)}')
    if full_tokens > TOKEN_WARN_THRESHOLD:
        print(f'  ⚠️  Supera el umbral de {TOKEN_WARN_THRESHOLD:,} tokens: '
              f'pegá solo el overview y usá extract para el resto.')
    if full_tokens > 0:
        saving = 100 * (1 - overview_tokens / full_tokens)
        print(f'  Ahorro del overview vs volcado completo: {saving:.0f}%')

    print(f'\n  Salidas en {repo_out}/:')
    print(f'  ├── 1_overview.txt   → pegá este en el turno 1 ({format_tokens(overview_tokens)})')
    print(f'  ├── 2_full.txt       → volcado completo ({format_tokens(full_tokens)})')
    print(f'  └── manifest.json    → índice que usa extract')

    print(f'\n  Próximo paso: cuando el LLM te pida archivos, pasáselos a extract:')
    print(f'    python extract.py --repo {repo} src/app.py README.md')
    return 0


if __name__ == '__main__':
    sys.exit(main())
