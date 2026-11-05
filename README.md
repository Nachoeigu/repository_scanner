# Repository Scanner

A stdlib-only Python CLI that turns a local repository into LLM-ready text: a
cheap **overview** you paste in turn 1, and an **extract** step that packages
exactly the files the model asks for.

The workflow is built around a simple idea: don't paste the whole repo into an
LLM. Show it a compact map first, let it request files, and deliver only those.

## The 3-step flow

```
┌──────────────────┐    ┌───────────────────────────┐    ┌──────────────────┐
│ 1. python main.py│ →  │ 2. LLM replies with a     │ →  │ 3. python        │
│    <repo path>   │    │    ```paths block         │    │    extract.py    │
│    → overview    │    │    listing the files      │    │    → custom .txt │
└──────────────────┘    └───────────────────────────┘    └──────────────────┘
```

### Step 1 — Scan

```bash
python main.py /path/to/your/project
# or interactive (same as always):
python main.py
```

Writes to `output/<project_name>/`:

| File            | Purpose                                                      |
|-----------------|--------------------------------------------------------------|
| `1_overview.txt`| Annotated tree + README excerpt (+ optional outline). Paste this in turn 1. Typically ~90%+ smaller than the full dump. |
| `2_full.txt`    | Every file's raw content in one document. Backup / small repos. |
| `manifest.json` | Per-file index (lines, tokens, skipped). Used by extract.     |

### Step 2 — Ask the LLM

Paste `1_overview.txt` into your LLM. The overview ends with an
`<instructions>` block (editable in `config.py`) telling the model to answer
with only a list of paths, e.g.:

````
```paths
src/app.py
config/loader.py
```
````

### Step 3 — Extract

Feed the model's raw reply (prose, bullets, backticks — it's tolerant) to extract:

```bash
# interactive: paste the LLM answer, finish with an empty line
python extract.py

# from a file or stdin
cat llm_answer.txt | python extract.py
python extract.py --from-file paths.txt

# direct args, globs and whole directories work too
python extract.py --repo /path/to/project src/**/*.py config/
```

Extract re-reads the requested files **from disk** with the same rules as the
scanner (secrets, binaries, size limits) and writes
`output/<project_name>/3_custom.txt`. Paths that don't exist get fuzzy
suggestions; anything resolving outside the repo (`../`, absolute paths) is
rejected. Secrets are never delivered, even when explicitly requested.

## CLI flags

```
python main.py [path] [--out DIR] [--max-file-kb N] [--outline]
               [--readme-max-chars N] [--line-numbers] [--no-gitignore]

python extract.py [paths...] [--from-file FILE] [--repo PATH] [--out DIR]
                  [--max-file-kb N] [--copy]
```

- `--outline` — adds a per-file symbol map (Python `ast`; regex for JS/TS) to
  the overview. Costs some tokens, helps the model pick files.
- `--max-file-kb` — files above this size appear as stubs
  (`skipped="too_large"`), never dropped silently. Default 200.
- `--no-gitignore` — ignore `.gitignore` and walk the tree instead of using
  `git ls-files`. The `config.py` filters always apply either way.

## What gets excluded

- **Secrets, always**: `.env*`, `*.pem`, `*.key`, `id_rsa*`, `*credentials*`,
  `*secret*` (see `SECRET_PATTERNS` in `config.py`). Nothing can re-include
  them; their names don't appear in any output. The console lists how many
  were skipped (with names) so you can spot false positives.
- **Binary files**: NUL byte in the first 8 KB → omitted entirely.
- **Noise**: lockfiles, `*.min.js`, `node_modules`, `__pycache__`, images,
  media, fonts, model weights, etc. — all in `config.py`.
- **The tool's own output**: the `output/` directory is never scanned.

## Output formats

`1_overview.txt`:

```
<repo_overview name="myapp" commit="a1b2c3d" generated="2026-01-15">
<summary>files: 42 · lines: 8211 · ~tokens: 38.1k · languages: Python 78%, Markdown 22%</summary>
<entrypoints>main.py, package.json, Dockerfile</entrypoints>
<tree>
myapp/
├── main.py        120L  ~1.1k  # Entry point.
├── src/
│   ├── app.py     220L  ~1.8k  # Docstring's first line.
│   └── big.sql    (omitido: too_large, 1.2MB)
</tree>
<readme chars="2000/3600" truncated="true">
...README excerpt...
</readme>
<instructions>...</instructions>
</repo_overview>
```

`2_full.txt` (and `3_custom.txt`) — raw content, no CDATA, no escaping:

```
<documents>
<document index="1" lines="165" tokens="1700">
<source>src/app.py</source>
<document_content>
...file content, byte-for-byte...
</document_content>
</document>
</documents>
```

Token counts are estimates: `tiktoken` (`cl100k_base`) if installed, otherwise
`len(text) / 4`. A console warning appears when the full dump exceeds
`TOKEN_WARN_THRESHOLD` (default 150k).

## Configuration

Everything lives in `config.py`: filter lists (exact names, regex, globs),
`MAX_FILE_KB`, `MAX_ENTRIES_PER_DIR` (tree collapsing), `README_MAX_CHARS`,
`TOKEN_WARN_THRESHOLD` and the `<instructions>` text.

## Tests

```bash
python -m unittest discover -s tests
```

## Requirements

- Python 3.10+ (uses `X | Y` type hints)
- `tiktoken` — optional, for better token estimates
- A git binary — optional, only for `git ls-files` and the commit hash
