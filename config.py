# config.py

FILES_TO_IGNORE = [
    'drive_credentials.json',
    'chromedriver',
    'logfile.txt',
    'package-lock.json',
    # Nota: se removió package.json y managed-settings.json para permitir auditar dependencias y políticas
]

FILES_TO_IGNORE_BASED_ON_REGEX = [
    # Archivos ocultos (metadata o configs de usuario local)
    r'^\.',
    # Jupyter Notebooks con outputs pesados
    r'.*\.ipynb$',

    # Imágenes
    r'\.png$',
    r'\.jpg$',
    r'\.jpeg$',
    r'\.gif$',
    r'\.webp$',
    r'\.ico$',
    r'\.svg$',
    r'\.mov$',     # Corregido de \nmov$
    r'\.heic$',    # Corregido de \nheic$

    # Videos
    r'\.mp4$',
    r'\.webm$',

    # Audio
    r'\.mp3$',
    r'\.wav$',

    # Tipografías
    r'.*\.ttf$',
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
    r'.*\.pt$',
    r'.*\.th$',
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

DIRECTORIES_TO_IGNORE = [
    '__pycache__',
    'venv',
    'node_modules',
    '_site',
    '.cache',
    'dist',
    'build',
    'entrega_al_cliente',  # Corregido: sin comodines /** incompatibles
    'imagenes_extraidas',
]

DIRECTORIES_TO_IGNORE_BASED_ON_REGEX = [
    r'^\.',
]