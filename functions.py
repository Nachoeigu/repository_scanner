# functions.py

import os
import re
import logging
from config import (
    FILES_TO_IGNORE,
    FILES_TO_IGNORE_BASED_ON_REGEX,
    DIRECTORIES_TO_IGNORE,
    DIRECTORIES_TO_IGNORE_BASED_ON_REGEX
)

class MessageOnlyFormatter(logging.Formatter):
    def format(self, record):
        return record.getMessage()

def escape_cdata(text: str) -> str:
    """En XML estándar, la secuencia ']]]]><![CDATA[>' no puede existir dentro de un CDATA.
    Se divide cerrando y reabriendo el bloque CDATA de forma válida."""
    return text.replace("]]]]><![CDATA[>", "]]]]]]><![CDATA[><![CDATA[>")

def is_binary_file(file_path: str) -> bool:
    """Detecta archivos binarios inspeccionando los primeros 1024 bytes en busca de null bytes."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except Exception:
        return True

def should_ignore_dir(dir_name: str) -> bool:
    if dir_name in DIRECTORIES_TO_IGNORE:
        return True
    return any(re.search(pattern, dir_name) for pattern in DIRECTORIES_TO_IGNORE_BASED_ON_REGEX)

def should_ignore_file(file_name: str, ignore_files: list) -> bool:
    if file_name in ignore_files:
        return True
    return any(re.search(pattern, file_name) for pattern in FILES_TO_IGNORE_BASED_ON_REGEX)

def format_file_size(size_in_bytes: int) -> str:
    """Retorna un string legible para humanos del tamaño de archivo."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes}B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f}KB"
    return f"{size_in_bytes / (1024 * 1024):.1f}MB"

def get_file_metadata(file_path: str) -> tuple[int, str]:
    """Calcula la cantidad de líneas y el tamaño de un archivo."""
    try:
        size = os.path.getsize(file_path)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = sum(1 for _ in f)
        return lines, format_file_size(size)
    except Exception:
        return 0, "0B"

def print_directory_structure_xml(directory: str, logger: logging.Logger, indent_level: int = 2):
    """Genera el árbol XML del repositorio incluyendo estadísticas de líneas y peso."""
    indent = "  " * indent_level
    try:
        items = sorted(os.listdir(directory))
    except Exception as e:
        logger.error(f"{indent}<error>No se pudo listar el directorio {directory}: {e}</error>")
        return

    for item in items:
        path = os.path.join(directory, item)
        if os.path.isdir(path):
            if should_ignore_dir(item):
                continue
            logger.info(f'{indent}<dir name="{item}">')
            print_directory_structure_xml(path, logger, indent_level + 1)
            logger.info(f'{indent}</dir>')
        else:
            if should_ignore_file(item, FILES_TO_IGNORE):
                continue
            lines, size = get_file_metadata(path)
            logger.info(f'{indent}<file name="{item}" lines="{lines}" size="{size}"/>')

def print_main_readme_xml(target_directory: str, logger: logging.Logger):
    """Imprime el README principal de la raíz dentro de etiquetas <readme>."""
    readme_path = os.path.join(target_directory, "README.md")
    if os.path.exists(readme_path):
        logger.info('  <readme>')
        try:
            with open(readme_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            logger.info('    <content><![CDATA[')
            logger.info(escape_cdata(content))
            logger.info('    ]]]]><![CDATA[></content>')
        except Exception as e:
            logger.info(f'    <error>No se pudo leer el archivo README.md: {e}</error>')
        logger.info('  </readme>')

def get_scannable_files(directory: str, ignore_files: list) -> list[tuple[str, str]]:
    """
    Retorna una lista ordenada de tuplas (ruta_relativa, ruta_absoluta)
    omitiendo binarios, archivos ignorados y el README de la raíz.
    """
    valid_files = []
    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = [d for d in dirs if not should_ignore_dir(d)]

        for file in files:
            # El README de la raíz se gestiona por separado
            if file.lower() == 'readme.md' and os.path.abspath(root) == os.path.abspath(directory):
                continue

            if should_ignore_file(file, ignore_files):
                continue

            file_path = os.path.join(root, file)

            if is_binary_file(file_path):
                continue

            rel_path = os.path.relpath(file_path, directory).replace('\\', '/')
            valid_files.append((rel_path, file_path))

    return sorted(valid_files, key=lambda x: x[0])

def print_file_contents_xml(directory: str, logger: logging.Logger, ignore_files: list):
    """Vuelca el contenido de cada archivo en formato XML con bloques CDATA."""
    files_to_dump = get_scannable_files(directory, ignore_files)

    for rel_path, abs_path in files_to_dump:
        logger.info(f'    <file path="{rel_path}">')
        try:
            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            logger.info('      <content><![CDATA[')
            logger.info(escape_cdata(content))
            logger.info('      ]]]]><![CDATA[></content>')
        except Exception as e:
            logger.info(f'      <error>No se pudo leer el archivo: {e}</error>')
        logger.info('    </file>')

def generate_yaml_catalog(directory: str, output_path: str, ignore_files: list):
    """
    Genera un archivo YAML estándar con cada archivo indexado bajo su ruta relativa
    utilizando bloques literales multilínea (|), facilitando su búsqueda y copiado rápido.
    """
    files_to_dump = get_scannable_files(directory, ignore_files)

    with open(output_path, 'w', encoding='utf-8') as yf:
        yf.write("# ====================================================================\n")
        yf.write("# REPOSITORIO: CATÁLOGO DE ARCHIVOS (YAML FORMAT)\n")
        yf.write("# Para copiar un archivo: buscá su ruta (Ctrl+F) y copiá el bloque indentado.\n")
        yf.write("# ====================================================================\n\n")

        for rel_path, abs_path in files_to_dump:
            yf.write(f'"{rel_path}": |\n')
            try:
                with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        # Indentar 2 espacios cada línea para formar un bloque YAML literal válido
                        yf.write(f"  {line}")
                if not line.endswith('\n'):
                    yf.write("\n")
            except Exception as e:
                yf.write(f"  # Error al leer archivo: {e}\n")
            yf.write("\n")