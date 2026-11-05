# config.py
"""Configuración del Repository Scanner.

Tres estilos de filtro (todos case-insensitive):
  - Nombres exactos:     FILES_TO_IGNORE, DIRECTORIES_TO_IGNORE
  - Regex (re.search):   FILES_TO_IGNORE_BASED_ON_REGEX, DIRECTORIES_TO_IGNORE_BASED_ON_REGEX
  - Globs (fnmatch):     SECRET_PATTERNS, DEFAULT_FILE_GLOBS

Los secretos (SECRET_PATTERNS) se aplican primero y nada los puede reincluir:
ni el modo git, ni extract. Sus nombres no aparecen en ninguna salida.
"""

# ---------------------------------------------------------------------------
# Archivos ignorados por nombre exacto
# ---------------------------------------------------------------------------
# Nota: drive_credentials.json y chromedriver parecen de otros proyectos,
# pero se dejan a pedido del usuario (ver resumen de entrega).
FILES_TO_IGNORE = [
    'drive_credentials.json',
    'chromedriver',
    'logfile.txt',
    'package-lock.json',
]

FILES_TO_IGNORE_BASED_ON_REGEX = [
    # Archivos ocultos (metadata o configs de usuario local)
    r'^\.',
    # Jupyter Notebooks con outputs pesados
    r'\.ipynb$',

    # Imágenes
    r'\.png$',
    r'\.jpg$',
    r'\.jpeg$',
    r'\.gif$',
    r'\.webp$',
    r'\.ico$',
    r'\.svg$',
    r'\.mov$',
    r'\.heic$',

    # Videos
    r'\.mp4$',
    r'\.webm$',

    # Audio
    r'\.mp3$',
    r'\.wav$',

    # Tipografías
    r'\.ttf$',
    r'\.woff2$',
    r'\.woff$',
    r'\.eot$',
    r'\.otf$',

    # Documentos y formatos ofimáticos
    r'\.pdf$',
    r'\.epub$',
    r'\.vsdx$',
    r'\.pptx$',
    r'\.msg$',
    r'\.odt$',
    r'\.docx$',
    r'\.xlsx$',

    # Comprimidos y binarios empaquetados
    r'\.zip$',
    r'\.tar$',
    r'\.gz$',
    r'\.rar$',
    r'\.7z$',

    # Pesos de modelos y checkpoints
    r'\.pt$',
    r'\.th$',
    r'\.pkl$',
    r'\.bin$',
    r'\.faiss$',
    r'\.caffemodel$',

    # Binarios ejecutables y bibliotecas compiladas
    r'\.exe$',
    r'\.dll$',
    r'\.so$',
    r'\.dylib$',
    r'\.a$',
    r'\.lib$',
    r'\.o$',
    r'\.obj$',
    r'\.out$',

    # Datos y bases locales
    r'\.csv$',
    r'\.db$',
    r'\.lockb$',

    # Logs y temporales
    r'\.log$',
    r'\.tmp$',
    r'\.bak$',
    r'\.swp$',

    # Diseños y paquetes de sistema
    r'\.psd$',
    r'\.ai$',
    r'\.sketch$',
    r'\.dmg$',
    r'\.iso$',
    r'\.jar$',
    r'\.class$',
    r'\.pdb$',
    r'\.app$',
    r'\.apk$',
    r'\.aapt$',
    r'\.plist$',
]

# ---------------------------------------------------------------------------
# Directorios ignorados
# ---------------------------------------------------------------------------
DIRECTORIES_TO_IGNORE = [
    '__pycache__',
    'venv',
    'node_modules',
    '_site',
    '.cache',
    'dist',
    'build',
    # Entradas que parecen de otros proyectos (se conservan a pedido):
    'entrega_al_cliente',
    'imagenes_extraidas',
]

DIRECTORIES_TO_IGNORE_BASED_ON_REGEX = [
    r'^\.',
]

# ---------------------------------------------------------------------------
# Secretos: se omiten SIEMPRE. Ni git ni extract pueden reincluirlos.
# Globs con fnmatch, contra el nombre y contra la ruta relativa completa.
# ---------------------------------------------------------------------------
SECRET_PATTERNS = [
    '.env*',
    '*.pem',
    '*.key',
    'id_rsa*',
    '*credentials*',
    '*secret*',
]

# ---------------------------------------------------------------------------
# Ignorados por defecto (ruido de dependencias/build). A diferencia de los
# secretos, un flag --no-gitignore o extract NO los reincluye: también son
# filtros de config. Se separan solo para que sean fáciles de relajar.
# ---------------------------------------------------------------------------
DEFAULT_FILE_GLOBS = [
    # Lockfiles
    'package-lock.json',
    'yarn.lock',
    'pnpm-lock.yaml',
    'poetry.lock',
    'Pipfile.lock',
    'uv.lock',
    'Cargo.lock',
    # Build de frontend
    '*.min.js',
    '*.min.css',
    '*.map',
]

# ---------------------------------------------------------------------------
# Umbrales y comportamiento
# ---------------------------------------------------------------------------
# Archivos más grandes que esto NO se omiten en silencio: aparecen en el
# árbol marcados y en el contenido como stub (skipped="too_large").
MAX_FILE_KB = 200

# Umbral de warning del total de tokens estimados del volcado completo.
TOKEN_WARN_THRESHOLD = 150_000

# Directorios con más entradas que esto se colapsan en el árbol del overview.
MAX_ENTRIES_PER_DIR = 15

# Recorte del README en el overview (chars). Flag --readme-max-chars.
README_MAX_CHARS = 2000

# Nombre del directorio de salida (nunca se autoescanea; comparar resuelto).
OUTPUT_DIRNAME = 'output'

# Extensiones que se tratan como texto para detectar lenguaje (por líneas).
LANG_BY_EXT = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.jsx': 'JavaScript',
    '.tsx': 'TypeScript',
    '.java': 'Java',
    '.go': 'Go',
    '.rs': 'Rust',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.c': 'C',
    '.h': 'C',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.hpp': 'C++',
    '.cs': 'C#',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.sh': 'Shell',
    '.bash': 'Shell',
    '.sql': 'SQL',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'CSS',
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.toml': 'TOML',
    '.md': 'Markdown',
    '.txt': 'Text',
    '.xml': 'XML',
}

# Archivos que anuncian entry points (detectados para el overview).
ENTRYPOINT_FILENAMES = [
    'package.json',
    'pyproject.toml',
    'requirements.txt',
    'setup.py',
    'Dockerfile',
    'Makefile',
    'docker-compose.yml',
]

# Prefijos de nombre que se muestran como entry points además de los de arriba.
ENTRYPOINT_PREFIXES = ['main.', 'index.', 'app.']

# ---------------------------------------------------------------------------
# Bloque <instructions> del overview (editable; se pega tal cual al LLM).
# ---------------------------------------------------------------------------
INSTRUCTIONS = (
    'Esto es solo un overview del repositorio. Elegí los archivos que '
    'necesites y respondé ÚNICAMENTE con una lista de paths relativos, uno '
    'por línea, dentro de un bloque ```paths, sin comentarios.'
)
