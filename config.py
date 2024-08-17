FILES_TO_IGNORE = [
'drive_credentials.json',
'chromedriver',
'logfile.txt'
]

FILES_TO_IGNORE_BASED_ON_REGEX = [
# Hidden files (usually configuration files or metadata)
'^\.',

# Jupyter Notebook files (often contain outputs and are not purely code)
'.*\.ipynb$',

# Image files (binary data, not relevant to text/code extraction)
'\.png$',      # PNG images
'\.jpg$',      # JPG images
'\.jpeg$',     # JPEG images
'\.gif$',      # GIF images
'\.webp$',     # WebP images
'\.ico$',      # Icon files
'\.svg$',      # Scalable Vector Graphics

# Video files (binary data, not relevant to text/code extraction)
'\.mp4$',      # MP4 videos
'\.webm$',     # WebM videos

# Audio files (binary data, not relevant to text/code extraction)
'\.mp3$',      # MP3 audio files
'\.wav$',      # WAV audio files

# Font files (binary data, not relevant to text/code extraction)
'.*\.ttf$',    # TrueType Font files
'\.woff2$',    # Web Open Font Format 2
'\.woff$',     # Web Open Font Format
'\.eot$',      # Embedded OpenType fonts
'\.otf$',      # OpenType fonts

# Document files (non-code content, usually not relevant to source code analysis)
'\.pdf$',      # PDF documents
'\.epub$',     # EPUB book files
'\.vsdx$',     # Visio documents
'\.pptx$',     # PowerPoint presentations
'\.msg$',      # Outlook messages
'\.odt$',      # OpenDocument text files
'\.docx$',     # Word documents
'\.xlsx$',     # Excel spreadsheets

# Compressed and archive files (not directly readable text)
'\.zip$',      # ZIP archives
'\.tar$',      # TAR archives
'\.gz$',       # Gzip compressed files
'\.rar$',      # RAR archives
'\.7z$',       # 7-Zip archives

# Model and binary data files (binary data, often large, not relevant to text extraction)
'.*\.pt$',     # PyTorch model files
'.*\.th$',     # Torch model files
'\.pkl$',      # Pickle files
'\.bin$',      # Binary files (generic)
'\.exe$',      # Executable files
'\.dll$',      # Dynamic Link Libraries
'\.so$',       # Shared libraries (Unix)
'\.faiss$',    # FAISS index files

# Data files (potentially large data sets, often not directly useful for source code analysis)
'\.csv$',      # CSV files
'\.db$',       # Database files (generic)

# Video and image formats for deep learning (not useful for text extraction)
'\.lockb$',    # Lock files (specific formats)

# Log and temporary files (not useful for code analysis, often large or irrelevant)
'\.log$',      # Log files
'\.tmp$',      # Temporary files
'\.bak$',      # Backup files
'\.swp$',      # Swap files (typically Vim)

# System and environment-related directories/files (not useful for source code analysis)
'__pycache__', # Python cache directories
'venv/',       # Virtual environment directories
'node_modules/',# Node.js modules directories


# Design files (binary files, not relevant for text extraction)
'\.psd$',      # Photoshop files
'\.ai$',       # Adobe Illustrator files
'\.sketch$',   # Sketch design files

# Backup and distribution files (not relevant for source code analysis)
'\.dist$',     # Distribution directories
'\.bak$',      # Backup files (repeated for emphasis)

# Additional unnecessary binary data (unlikely to contain useful source code)
'\.dmg$',      # macOS Disk Image files
'\.iso$',      # ISO disk image files
'\.jar$',      # Java Archive files (often contain compiled code)
'\.class$',    # Java class files (compiled code)
'\.obj$',      # Object files (compiled code)
'\.o$',        # Object files (compiled code)
'\.out$',      # Output files (compiled binaries)
'\.a$',        # Static libraries (Unix)
'\.lib$',      # Static libraries (Windows)
'\.pdb$',      # Program database files (debugging information)
'\.app$',      # macOS Application bundles
'\.apk$'       # Android operation system app
'\.aapt$'
'\.caffemodel'


]


DIRECTORIES_TO_IGNORE = [
'__pycache__',
'venv'
]

DIRECTORIES_TO_IGNORE_BASED_ON_REGEX = [
'^\.'
]