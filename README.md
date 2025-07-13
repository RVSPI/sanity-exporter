# SANITY Exporter

Universal console utility to export project structure and files contents to TXT/JSON/HTML formats.
Perfect for documentation, code reviews, and project analysis.

## Features
- Interactive and CLI modes
- Export to TXT/JSON/HTML
- Predefined templates (Android, Web, Python)
- Exclusion filters for files/directories
- Handles UTF-8/16, ASCII

## Installation
```bash
git clone https://github.com/rvspi/sanity-exporter.git
cd sanity-exporter
pip install -r requirements.txt
```

# Usage

## Interactive Mode
```bash
python sanity-exporter.py
```

## CLI Mode
```bash
python sanity-exporter.py --dir /path/to/project --output export --format html --mode both
```

## Options
```bash
-d, --dir          Project directory
-o, --output       Output filename (default: export)
-m, --mode         Export mode: both, structure, content (default: both)
-f, --format       Output format: txt, json, html (default: txt)
-t, --template     Template name (Android, Web, Python)
--exclude-dirs     Comma-separated directories to exclude
--exclude-files    Comma-separated files to exclude
```

## Example
Export Android project with template:
```bash
python sanity-exporter.py --dir ~/projects/myapp --template Android --format json
```
