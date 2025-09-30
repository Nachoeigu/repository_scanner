import os
from config import *
import logging
import re

# Define a custom log formatter that includes only the message
class MessageOnlyFormatter(logging.Formatter):
    def format(self, record):
        return record.getMessage()

def print_directory_structure_xml(directory, indent_level=0):
    """
    Genera y registra una estructura de directorios en formato XML.
    """
    indent = "  " * indent_level
    try:
        items = sorted(os.listdir(directory))
    except FileNotFoundError:
        logging.error(f"{indent}<error>Directorio no encontrado: {directory}</error>")
        return

    for item in items:
        path = os.path.join(directory, item)
        
        if os.path.isdir(path):
            if item in DIRECTORIES_TO_IGNORE or any(re.search(regex, item) for regex in DIRECTORIES_TO_IGNORE_BASED_ON_REGEX):
                continue
            logging.info(f'{indent}<dir name="{item}">')
            print_directory_structure_xml(path, indent_level + 1)
            logging.info(f'{indent}</dir>')
        else:
            if item in FILES_TO_IGNORE or any(re.search(regex, item) for regex in FILES_TO_IGNORE_BASED_ON_REGEX):
                continue
            logging.info(f'{indent}<file name="{item}"/>')

def print_main_readme_xml(target_directory):
    """
    Busca el README.md, lo lee y lo imprime en formato XML.
    """
    readme_path = os.path.join(target_directory, "README.md")
    if os.path.exists(readme_path):
        logging.info('  <readme>')
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logging.info('    <content><![CDATA[')
            logging.info(content)
            logging.info('    ]]></content>')
        except Exception as e:
            logging.info(f'    <error>No se pudo leer el archivo README.md: {e}</error>')
        logging.info('  </readme>')

def print_file_contents_xml(directory, ignore_files, ignore_directories, map_specific_extension_file=None):
    """
    Recorre el directorio e imprime el contenido de cada archivo en formato XML.
    """
    for root, dirs, files in os.walk(directory, topdown=True):
        # Filtrado de directorios para que os.walk no entre en ellos
        dirs[:] = [d for d in dirs if d not in ignore_directories and not any(re.search(regex, d) for regex in DIRECTORIES_TO_IGNORE_BASED_ON_REGEX)]
        
        for file in sorted(files):
            # Omitir el README principal, ya que se maneja por separado
            if file.lower() == 'readme.md' and os.path.abspath(root) == os.path.abspath(directory):
                continue

            # Filtrado por extensión específica si se proporciona
            if map_specific_extension_file:
                if os.path.splitext(file)[1].lower() not in [ext.lower() for ext in map_specific_extension_file]:
                    continue
            
            # Filtrado por nombre de archivo y expresiones regulares
            if file in ignore_files or any(re.search(regex, file) for regex in FILES_TO_IGNORE_BASED_ON_REGEX):
                continue

            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, directory)
            
            logging.info(f'    <file path="{relative_path}">')
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logging.info('      <content><![CDATA[')
                logging.info(content)
                logging.info('      ]]></content>')
            except Exception as e:
                logging.info(f'      <error>No se pudo leer el archivo: {e}</error>')
            logging.info(f'    </file>')