FILES_TO_IGNORE = [
r'drive_credentials.json',
r'chromedriver',
r'logfile.txt',
r'package-lock.json',
r'package.json'
]

FILES_TO_IGNORE_BASED_ON_REGEX = [
# Hidden files (usually configuration files or metadata)
r'^\.',

# Jupyter Notebook files (often contain outputs and are not purely code)
r'.*\.ipynb$',

# Image files (binary data, not relevant to text/code extraction)
r'\.png$',      # PNG images
r'\.jpg$',      # JPG images
r'\.jpeg$',     # JPEG images
r'\.gif$',      # GIF images
r'\.webp$',     # WebP images
r'\.ico$',      # Icon files
r'\.svg$',      # Scalable Vector Graphics

# Video files (binary data, not relevant to text/code extraction)
r'\.mp4$',      # MP4 videos
r'\.webm$',     # WebM videos

# Audio files (binary data, not relevant to text/code extraction)
r'\.mp3$',      # MP3 audio files
r'\.wav$',      # WAV audio files

# Font files (binary data, not relevant to text/code extraction)
r'.*\.ttf$',    # TrueType Font files
r'\.woff2$',    # Web Open Font Format 2
r'\.woff$',     # Web Open Font Format
r'\.eot$',      # Embedded OpenType fonts
r'\.otf$',      # OpenType fonts

# Document files (non-code content, usually not relevant to source code analysis)
r'\.pdf$',      # PDF documents
r'\.epub$',     # EPUB book files
r'\.vsdx$',     # Visio documents
r'\.pptx$',     # PowerPoint presentations
r'\.msg$',      # Outlook messages
r'\.odt$',      # OpenDocument text files
r'\.docx$',     # Word documents
r'\.xlsx$',     # Excel spreadsheets

# Compressed and archive files (not directly readable text)
r'\.zip$',      # ZIP archives
r'\.tar$',      # TAR archives
r'\.gz$',       # Gzip compressed files
r'\.rar$',      # RAR archives
r'\.7z$',       # 7-Zip archives

# Model and binary data files (binary data, often large, not relevant to text extraction)
r'.*\.pt$',     # PyTorch model files
r'.*\.th$',     # Torch model files
r'\.pkl$',      # Pickle files
r'\.bin$',      # Binary files (generic)
r'\.exe$',      # Executable files
r'\.dll$',      # Dynamic Link Libraries
r'\.so$',       # Shared libraries (Unix)
r'\.faiss$',    # FAISS index files

# Data files (potentially large data sets, often not directly useful for source code analysis)
r'\.csv$',      # CSV files
r'\.db$',       # Database files (generic)

# Video and image formats for deep learning (not useful for text extraction)
r'\.lockb$',    # Lock files (specific formats)

# Log and temporary files (not useful for code analysis, often large or irrelevant)
r'\.log$',      # Log files
r'\.tmp$',      # Temporary files
r'\.bak$',      # Backup files
r'\.swp$',      # Swap files (typically Vim)

# System and environment-related directories/files (not useful for source code analysis)
r'__pycache__', # Python cache directories
r'venv/',       # Virtual environment directories
r'node_modules/',# Node.js modules directories


# Design files (binary files, not relevant for text extraction)
r'\.psd$',      # Photoshop files
r'\.ai$',       # Adobe Illustrator files
r'\.sketch$',   # Sketch design files

# Backup and distribution files (not relevant for source code analysis)
r'\.dist$',     # Distribution directories
r'\.bak$',      # Backup files (repeated for emphasis)

# Additional unnecessary binary data (unlikely to contain useful source code)
r'\.dmg$',      # macOS Disk Image files
r'\.iso$',      # ISO disk image files
r'\.jar$',      # Java Archive files (often contain compiled code)
r'\.class$',    # Java class files (compiled code)
r'\.obj$',      # Object files (compiled code)
r'\.o$',        # Object files (compiled code)
r'\.out$',      # Output files (compiled binaries)
r'\.a$',        # Static libraries (Unix)
r'\.lib$',      # Static libraries (Windows)
r'\.pdb$',      # Program database files (debugging information)
r'\.app$',      # macOS Application bundles
r'\.apk$'       # Android operation system app
r'\.aapt$'
r'\.caffemodel'


]


DIRECTORIES_TO_IGNORE = [
r'__pycache__',
r'venv',
r'node_modules',
r"_site",
r".cache"
]

DIRECTORIES_TO_IGNORE_BASED_ON_REGEX = [
r'^\.'
]