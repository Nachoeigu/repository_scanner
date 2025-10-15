# Repository Scanner to XML

This project is a command-line tool developed in Python that scans a local repository directory and generates a single XML file containing its entire structure and the content of its files. It is ideal for obtaining a complete and portable representation of a project, useful for code analysis, migrations, or as input for other LLM tools.

## Features

- **Directory Structure**: Generates an XML map of the entire folder and file structure of the project.
- **File Content**: Embeds the content of each text file within `CDATA` tags for easy parsing and processing.
- **Highly Configurable**: Allows you to ignore specific files and directories through lists and regular expressions in a central configuration file.
- **Smart Filters**: By default, it ignores binary files, configuration files, dependencies (like `node_modules`), and other files commonly irrelevant for source code analysis.
- **Clean Output**: The result is printed to the console and automatically saved to a `logfile.txt` file.

## 🚀 Getting Started

To use this tool, you only need to have Python installed on your system.

### 1. Prerequisites

- Python 3.x

No external libraries beyond Python's standard library are required.

### 2. How to Use

1.  **Clone or download** the project files into a folder:
    *   `main.py`
    *   `functions.py`
    *   `config.py`

2.  **Open a terminal** and navigate to the directory where you saved the files.

3.  **Run the main script**:
    ```bash
    python main.py
    ```

4.  **Enter the path**: The script will prompt you to enter the full path of the directory you want to analyze.
    ```
    Put your entire path: /full/path/to/your/project
    ```

5.  **Get the output**: The XML output will be displayed in the terminal and saved to a file named `logfile.txt` in the same directory where you ran the script.

## ⚙️ Configuration

You can customize which files and directories are ignored during the scan by editing the `config.py` file.

### Exclusion Lists

-   `FILES_TO_IGNORE`: A list of exact filenames to be omitted.
    ```python
    FILES_TO_IGNORE = ['drive_credentials.json', 'logfile.txt']
    ```

-   `FILES_TO_IGNORE_BASED_ON_REGEX`: A list of regular expressions to skip files that match certain patterns (e.g., all images, videos, or hidden files).
    ```python
    FILES_TO_IGNORE_BASED_ON_REGEX = [r'^\.', r'\.png$', r'\.pdf$']
    ```

-   `DIRECTORIES_TO_IGNORE`: A list of exact directory names to be completely ignored.
    ```python
    DIRECTORIES_TO_IGNORE = ['__pycache__', 'venv', 'node_modules']
    ```

-   `DIRECTORIES_TO_IGNORE_BASED_ON_REGEX`: A list of regular expressions to skip directories that match a pattern (e.g., all directories starting with a dot).
    ```python
    DIRECTORIES_TO_IGNORE_BASED_ON_REGEX = [r'^\.']
    ```

## 📄 Example XML Output

The final output will have a structure similar to the following:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<repositoryAnalysis name="project_name">
  <structure>
    <dir name="src">
      <file name="main.py"/>
      <file name="utils.py"/>
    </dir>
    <file name="README.md"/>
  </structure>
  <readme>
    <content><![CDATA[
      # README.md content
      This is a sample project.
    ]]></content>
  </readme>
  <files>
    <file path="src/main.py">
      <content><![CDATA[
        # Content of main.py
        print("Hello, world!")
      ]]></content>
    </file>
    <file path="src/utils.py">
      <content><![CDATA[
        # Content of utils.py
        def my_function():
            return True
      ]]></content>
    </file>
  </files>
</repositoryAnalysis>