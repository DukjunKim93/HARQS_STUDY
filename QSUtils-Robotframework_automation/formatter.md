# Python Code Formatter for QSUtils

This formatter script ensures consistent code formatting across the entire QSUtils project according to the Black code style.

## Overview

The formatter uses [Black](https://github.com/psf/black) as the primary Python code formatter with the following configuration:
- Line length: 88 characters (Black default)
- Target versions: Python 3.8 through 3.14
- Excluded directories: 
  - `.eggs`, `.git`, `.hg`, `.mypy_cache`, `.tox`, `.venv`
  - `build`, `dist`, `QSUtils.egg-info`
  - `tests` (as configured in pyproject.toml)

## Requirements

- Python 3.8 or higher
- Black formatter (automatically installed if missing)

## Usage

### Check if files need formatting (without making changes)

```bash
python formatter.py --check
```

This will scan all Python files in the project and report which ones need formatting.

### Show diff of changes without applying them

```bash
python formatter.py --diff
```

This will show what changes would be made to files without actually modifying them.

### Format all files in the project

```bash
python formatter.py
```

This will format all Python files that need formatting.

### Format files in a specific directory

```bash
python formatter.py --dir src/QSUtils
```

This will format only the Python files in the specified directory.

### Format a specific file

```bash
python formatter.py --dir src/QSUtils/__init__.py
```

This will format only the specified Python file.

### Install Black formatter

```bash
python formatter.py --install-black
```

This will automatically install the Black formatter if it's not already available.

## Features

- **Recursive scanning**: Automatically finds all Python files in subdirectories
- **Smart exclusion**: Respects the exclusion patterns defined in pyproject.toml
- **Safe operation**: Won't format files in excluded directories like tests, .git, etc.
- **Progress reporting**: Shows detailed information about the formatting process
- **Error handling**: Gracefully handles missing dependencies and formatting errors
- **Cross-platform**: Works on Windows, macOS, and Linux

## Integration with CI/CD

To ensure all code passes formatting checks in CI/CD pipelines:

```bash
python formatter.py --check
```

If this command returns a non-zero exit code, it means some files need formatting.

## Troubleshooting

### Black not found

If you see an error about Black not being found, install it manually:

```bash
pip install black
```

Or use the built-in installer:

```bash
python formatter.py --install-black
```

### Permission errors

If you encounter permission errors, make sure you have write permissions to the files being formatted.

### Incorrect exclusions

If files that should be excluded are being processed, check the `get_exclude_patterns()` function in the formatter script.
