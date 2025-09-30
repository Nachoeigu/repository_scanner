import logging
import os
from config import *
from functions import (
    MessageOnlyFormatter,
    print_directory_structure_xml,
    print_main_readme_xml,
    print_file_contents_xml
)

# Configuración del logging (una sola vez)
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('logfile.txt', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
# Aplicar el formateador personalizado para eliminar metadatos del log
for handler in logging.root.handlers:
    handler.setFormatter(MessageOnlyFormatter())

if __name__ == "__main__":
    target_directory = input('Put your entire path:')
    PROJECT_ROOT_NAME = os.path.basename(target_directory)
    
    # --- INICIO DEL DOCUMENTO XML ---
    logging.info('<?xml version="1.0" encoding="UTF-8"?>')
    logging.info(f'<repositoryAnalysis name="{PROJECT_ROOT_NAME}">')
    
    # 1. Sección de Estructura del Repositorio
    logging.info('  <structure>')
    print_directory_structure_xml(target_directory, indent_level=2)
    logging.info('  </structure>')
    
    # 2. Sección del README
    print_main_readme_xml(target_directory)
    
    # 3. Sección con el contenido de todos los archivos
    logging.info('  <files>')
    print_file_contents_xml(
        target_directory,
        ignore_files=FILES_TO_IGNORE,
        ignore_directories=DIRECTORIES_TO_IGNORE
        # map_specific_extension_file=['.py'] # Descomentar para filtrar por extensión
    )
    logging.info('  </files>')
    
    # --- FIN DEL DOCUMENTO XML ---
    logging.info('</repositoryAnalysis>')

    #/Users/nachoeigu/Desktop/Personal/psicologia