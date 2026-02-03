#!/usr/bin/env python3
"""
Python Code Formatter for QSUtils Project

This script formats all Python files in the project according to the
formatting configuration specified in pyproject.toml.

The script uses Black as the primary formatter, which is configured
with a line length of 88 characters and specific exclusion patterns.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def check_black_installed():
    """Check if Black formatter is installed."""
    try:
        import black

        return True
    except ImportError:
        return False


def get_black_version():
    """Get Black version if installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"], capture_output=True, text=True
        )
        return result.stdout.strip()
    except Exception:
        return None


def find_python_files(root_path, exclude_patterns=None):
    """
    Find all Python files in the given directory recursively.

    Args:
        root_path (str): Root directory to search
        exclude_patterns (list): List of patterns to exclude

    Returns:
        list: List of Python file paths
    """
    if exclude_patterns is None:
        exclude_patterns = []

    python_files = []
    root = Path(root_path)

    # Convert exclude patterns to Path objects for easier comparison
    exclude_paths = [Path(p) for p in exclude_patterns if p]

    # If root_path is a file, just return it if it's a Python file
    if root.is_file():
        if root.suffix == ".py":
            # Check if file is in excluded directory
            excluded = False
            for exclude_path in exclude_paths:
                if exclude_path in root.parents:
                    excluded = True
                    break

            # Also check if file is directly excluded
            if not excluded:
                for pattern in exclude_patterns:
                    if pattern and pattern in str(root):
                        excluded = True
                        break

            if not excluded:
                python_files.append(str(root))
        return python_files

    # If root_path is a directory, search recursively
    for py_file in root.rglob("*.py"):
        # Check if file is in excluded directory
        excluded = False
        for exclude_path in exclude_paths:
            if exclude_path in py_file.parents:
                excluded = True
                break

        # Also check if file is directly excluded
        if not excluded:
            for pattern in exclude_patterns:
                if pattern and pattern in str(py_file):
                    excluded = True
                    break

        if not excluded:
            python_files.append(str(py_file))

    return python_files


def format_files_with_black(file_paths, check_only=False, diff_only=False):
    """
    Format Python files using Black.

    Args:
        file_paths (list): List of file paths to format
        check_only (bool): Only check if files need formatting
        diff_only (bool): Show diff of changes without applying them

    Returns:
        tuple: (success_count, error_count, needs_formatting_count)
    """
    if not file_paths:
        print("No Python files found to format.")
        return 0, 0, 0

    print(f"Found {len(file_paths)} Python files to process.")

    # Build black command
    cmd = [sys.executable, "-m", "black"]

    if check_only:
        cmd.append("--check")
    elif diff_only:
        cmd.append("--diff")

    # Add all file paths
    cmd.extend(file_paths)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if check_only:
            print(f"Black check command returned code: {result.returncode}")
            # For check mode, stderr contains the summary, stdout contains the file list
            print(f"Black check stdout: {result.stdout}")
            print(f"Black check stderr: {result.stderr}")
            if result.returncode == 0:
                print("All files are already formatted correctly!")
                return len(file_paths), 0, 0
            else:
                print("Some files need formatting.")
                # Count files that need formatting (lines starting with "would reformat")
                needs_formatting = result.stderr.count("would reformat")
                unchanged_count = result.stderr.count("left unchanged")
                total_count = result.stderr.count("files would be")
                if "Oh no!" in result.stderr:
                    # Extract the numbers from the summary line
                    import re

                    match = re.search(
                        r"(\d+) files would be reformatted, (\d+) files would be left unchanged",
                        result.stderr,
                    )
                    if match:
                        needs_formatting = int(match.group(1))
                        unchanged_count = int(match.group(2))
                print(
                    f"Summary: {needs_formatting} files would be reformatted, {unchanged_count} files would be left unchanged."
                )
                return unchanged_count, 0, needs_formatting
        elif diff_only:
            print("Formatting diff:")
            print(result.stdout)
            return len(file_paths), 0, 0
        else:
            if result.returncode == 0:
                print("Formatting completed successfully!")
                # Count reformatted files (lines starting with "reformatted")
                reformatted = result.stdout.count("reformatted")
                unchanged = result.stdout.count("left unchanged")
                # Also check stderr for summary information
                if "All done!" in result.stderr:
                    import re

                    match = re.search(
                        r"(\d+) files reformatted, (\d+) files left unchanged",
                        result.stderr,
                    )
                    if match:
                        reformatted = int(match.group(1))
                        unchanged = int(match.group(2))
                    elif "1 file would be left unchanged" in result.stderr:
                        unchanged = 1
                        reformatted = 0
                print(f"Reformatted: {reformatted} files")
                print(f"Unchanged: {unchanged} files")
                return reformatted + unchanged, 0, 0
            else:
                print("Error during formatting:")
                print(result.stderr)
                return 0, len(file_paths), 0

    except FileNotFoundError:
        print("Error: Black formatter not found. Please install it with:")
        print("  pip install black")
        return 0, len(file_paths), 0
    except Exception as e:
        print(f"Error during formatting: {e}")
        return 0, len(file_paths), 0


def get_exclude_patterns():
    """
    Get exclude patterns from pyproject.toml configuration.

    Returns:
        list: List of exclude patterns
    """
    exclude_patterns = [
        ".eggs",
        ".git",
        ".hg",
        ".mypy_cache",
        ".tox",
        ".venv",
        "build",
        "dist",
        "QSUtils.egg-info",
        "robot-scripts-package/build",
        # Note: tests directory is excluded in build but not in formatting
        # The CI/CD pipeline explicitly checks tests/ directory, so we should format it
    ]

    return exclude_patterns


def format_project(check_only=False, diff_only=False, target_dir="."):
    """
    Format all Python files in the project.

    Args:
        check_only (bool): Only check if files need formatting
        diff_only (bool): Show diff without applying changes
        target_dir (str): Directory to format (default: current directory)

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Formatting Python files in: {os.path.abspath(target_dir)}")

    # Check if Black is installed
    if not check_black_installed():
        print("Warning: Black formatter is not installed.")
        print("To install Black, run: pip install black")
        print("Falling back to basic formatting check...")

        # Try to install black
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "black"],
                check=True,
                capture_output=True,
            )
            print("Black installed successfully!")
        except subprocess.CalledProcessError:
            print("Could not automatically install Black. Please install manually.")
            return False

    # Get exclude patterns
    exclude_patterns = get_exclude_patterns()
    print(f"Exclude patterns: {exclude_patterns}")

    # Find Python files
    python_files = find_python_files(target_dir, exclude_patterns)

    if not python_files:
        print("No Python files found to format.")
        return True

    print(f"Found {len(python_files)} Python files to process.")

    # Format files
    success_count, error_count, needs_formatting = format_files_with_black(
        python_files, check_only, diff_only
    )

    if check_only:
        if needs_formatting > 0:
            print(f"\n{needs_formatting} files need formatting.")
            print("Run this script without --check to format them.")
            return False
        else:
            print("All files are properly formatted!")
            return True
    else:
        if error_count > 0:
            print(f"\nFormatting failed for {error_count} files.")
            return False
        else:
            print(f"\nSuccessfully processed {success_count} files.")
            return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Format Python files in the QSUtils project"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if files need formatting without making changes",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show diff of formatting changes without applying them",
    )
    parser.add_argument(
        "--dir", default=".", help="Directory to format (default: current directory)"
    )
    parser.add_argument(
        "--install-black",
        action="store_true",
        help="Attempt to install Black formatter",
    )

    args = parser.parse_args()

    # Handle installation request
    if args.install_black:
        try:
            print("Installing Black formatter...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "black"], check=True
            )
            print("Black installed successfully!")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"Failed to install Black: {e}")
            return 1

    # Format project
    success = format_project(
        check_only=args.check, diff_only=args.diff, target_dir=args.dir
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
