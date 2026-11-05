# main.py

import os
import sys
import logging
from config import FILES_TO_IGNORE, DIRECTORIES_TO_IGNORE
from functions import (
    MessageOnlyFormatter,
    print_directory_structure_xml,
    print_main_readme_xml,
    print_file_contents_xml,
    generate_yaml_catalog
)

def create_file_logger(logger_name: str, output_file: str) -> logging.Logger:
    """Crea un logger independiente que escribe directamente en un archivo de destino."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.handlers = []

    handler = logging.FileHandler(output_file, mode='w', encoding='utf-8')
    handler.setFormatter(MessageOnlyFormatter())
    logger.addHandler(handler)
    return logger

def build_overview_xml(target_directory: str, output_file: str):
    """Genera 1_overview.xml: solo árbol con pesos/líneas y README principal."""
    logger = create_file_logger("overview", output_file)
    project_name = os.path.basename(target_directory)

    logger.info('<?xml version="1.0" encoding="UTF-8"?>')
    logger.info(f'<repositoryAnalysis name="{project_name}" mode="overview">')
    
    logger.info('  <structure>')
    print_directory_structure_xml(target_directory, logger, indent_level=2)
    logger.info('  </structure>')

    print_main_readme_xml(target_directory, logger)

    logger.info('</repositoryAnalysis>')
    
    for h in logger.handlers:
        h.close()

def build_full_xml(target_directory: str, output_file: str):
    """Genera 2_full.xml: estructura, README y el volcado completo de código."""
    logger = create_file_logger("full", output_file)
    project_name = os.path.basename(target_directory)

    logger.info('<?xml version="1.0" encoding="UTF-8"?>')
    logger.info(f'<repositoryAnalysis name="{project_name}" mode="full">')
    
    logger.info('  <structure>')
    print_directory_structure_xml(target_directory, logger, indent_level=2)
    logger.info('  </structure>')

    print_main_readme_xml(target_directory, logger)

    logger.info('  <files>')
    print_file_contents_xml(target_directory, logger, FILES_TO_IGNORE)
    logger.info('  </files>')

    logger.info('</repositoryAnalysis>')

    for h in logger.handlers:
        h.close()

if __name__ == "__main__":
    raw_path = input('Put your entire path: ').strip().strip("\"'")
    target_directory = os.path.abspath(os.path.expanduser(raw_path))

    if not os.path.isdir(target_directory):
        print(f"\n[ERROR] La ruta '{target_directory}' no es un directorio válido.")
        sys.exit(1)

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    os.makedirs(output_dir, exist_ok=True)

    overview_path = os.path.join(output_dir, '1_overview.xml')
    full_path     = os.path.join(output_dir, '2_full.xml')
    yaml_path     = os.path.join(output_dir, '3_files.yaml')

    print(f"\n🔍 Escaneando repositorio: {target_directory}")
    
    print("  [1/3] Generando 1_overview.xml (estructura liviana + README)...")
    build_overview_xml(target_directory, overview_path)

    print("  [2/3] Generando 2_full.xml (repositorio completo en XML)...")
    build_full_xml(target_directory, full_path)

    print("  [3/3] Generando 3_files.yaml (catálogo ordenado por archivos)...")
    generate_yaml_catalog(target_directory, yaml_path, FILES_TO_IGNORE)

    print("\n✅ ¡Escaneo finalizado con éxito!")
    print(f"📁 Archivos generados en: {output_dir}/")
    print(f"  ├── 1_overview.xml  --> Pegás este en el Turno 1 (~95% ahorro de tokens)")
    print(f"  ├── 2_full.xml      --> Volcado completo XML (de respaldo)")
    print(f"  └── 3_files.yaml    --> Buscás con Ctrl+F y copiás los archivos que te pida")
    
    #/Users/nachoeigu/Desktop/Personal/sandbox-ai-app