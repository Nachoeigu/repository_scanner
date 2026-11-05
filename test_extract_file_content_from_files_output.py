# test_extract_file_content_from_files_output.py
#
# Extrae bloques de output/3_files.yaml según una lista de rutas
# y los guarda en output/custom_selected_files.yaml.

import os
import re
import sys

FILES_TO_EXTRACT  = [

]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SOURCE = os.path.join(SCRIPT_DIR, "output", "3_files.yaml")
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "output", "custom_selected_files.yaml")

FILE_HEADER_RE = re.compile(r'^"(.+)": \|$')


def parse_yaml_catalog(yaml_path: str) -> dict[str, str]:
    """Parsea el catálogo generado por generate_yaml_catalog (claves quoted + bloque |)."""
    catalog = {}
    current_path = None
    content_lines = []

    def flush():
        nonlocal current_path, content_lines
        if current_path is not None:
            catalog[current_path] = "".join(content_lines)
        current_path = None
        content_lines = []

    with open(yaml_path, "r", encoding="utf-8") as f:
        for line in f:
            header = FILE_HEADER_RE.match(line.rstrip("\n"))
            if header:
                flush()
                current_path = header.group(1)
                continue

            if current_path is None:
                continue

            if line.startswith("  "):
                content_lines.append(line[2:])
            elif line.strip() == "":
                continue
            else:
                flush()

    flush()
    return catalog


def extract_selected_files(catalog: dict[str, str], requested: list[str]) -> tuple[dict[str, str], list[str]]:
    selected = {}
    missing = []
    for rel_path in requested:
        key = rel_path.strip().strip("\"'")
        if not key:
            continue
        if key in catalog:
            selected[key] = catalog[key]
        else:
            missing.append(key)
    return selected, missing


def write_custom_yaml(output_path: str, selected: dict[str, str]):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as yf:
        yf.write("# ====================================================================\n")
        yf.write("# ARCHIVOS SELECCIONADOS (extraídos de 3_files.yaml)\n")
        yf.write("# ====================================================================\n\n")

        for rel_path, content in selected.items():
            yf.write(f'"{rel_path}": |\n')
            if content:
                for line in content.splitlines(keepends=True):
                    yf.write(f"  {line}")
                if not content.endswith("\n"):
                    yf.write("\n")
            yf.write("\n")


def main():
    requested = sys.argv[1:] if len(sys.argv) > 1 else FILES_TO_EXTRACT
    if not requested:
        print("[ERROR] Pasá al menos una ruta, o completá FILES_TO_EXTRACT en el script.")
        sys.exit(1)

    if not os.path.isfile(DEFAULT_SOURCE):
        print(f"[ERROR] No existe el catálogo: {DEFAULT_SOURCE}")
        sys.exit(1)

    catalog = parse_yaml_catalog(DEFAULT_SOURCE)
    selected, missing = extract_selected_files(catalog, requested)

    if missing:
        print("[WARN] No se encontraron en 3_files.yaml:")
        for path in missing:
            print(f"  - {path}")

    if not selected:
        print("[ERROR] Ningún archivo de la lista está en el catálogo.")
        sys.exit(1)

    write_custom_yaml(DEFAULT_OUTPUT, selected)
    print(f"[OK] Extraídos {len(selected)} archivo(s) -> {DEFAULT_OUTPUT}")
    for path in selected:
        print(f"  - {path}")


if __name__ == "__main__":
    main()
