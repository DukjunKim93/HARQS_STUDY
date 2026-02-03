#!/bin/bash

# QSUtils Installation Script
# This script provides easy installation, uninstallation, and force reinstallation of QSUtils

set -e # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Package information
PACKAGE_NAME="QSUtils"
PACKAGE_VERSION="1.2.0"
WHEEL_FILE="qsutils-1.2.0-py3-none-any.whl"

# Function to print colored output
print_status() {
	echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
	echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
	echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
	echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if package is installed
is_installed() {
	pip show qsutils >/dev/null 2>&1
	return $?
}

# Function to check if build tools are installed
check_build_tools() {
	if ! command -v python &>/dev/null; then
		print_error "Python is not installed or not in PATH"
		exit 1
	fi

	if ! python -c "import build" 2>/dev/null; then
		print_status "Installing build tools..."
		if pip install build; then
			print_success "Build tools installed successfully"
		else
			print_error "Failed to install build tools"
			exit 1
		fi
	fi
}

# Function to install requirements
install_requirements() {
	# Install development dependencies from requirements.txt
	if [ -f "requirements.txt" ]; then
		print_status "Installing development dependencies from requirements.txt..."
		if pip install -r requirements.txt; then
			print_success "Development dependencies installed successfully"
		else
			print_warning "Failed to install development dependencies (continuing anyway)"
		fi
	fi

	# Install runtime dependencies using pip install -e . (this will read from pyproject.toml)
	print_status "Installing runtime dependencies from pyproject.toml..."
	if pip install -e . --no-deps; then
		print_success "Runtime dependencies will be installed with the package"
	else
		print_warning "Failed to pre-install package (continuing with full install)"
	fi
}

# Function to build package
build_package() {
	print_status "Building package..."

	# Clean previous build artifacts to ensure a fresh build
	print_status "Cleaning previous build artifacts..."
	rm -rf dist/ build/ *.egg-info

	print_status "Running python -m build..."
	if python -m build; then
		print_success "Package built successfully"
	else
		print_error "Failed to build package"
		exit 1
	fi
}

# Function to install package
install_package() {
	print_status "Installing $PACKAGE_NAME v$PACKAGE_VERSION..."

	# Install development dependencies first
	if [ -f "requirements.txt" ]; then
		print_status "Installing development dependencies..."
		if pip install -r requirements.txt; then
			print_success "Development dependencies installed successfully"
		else
			print_warning "Failed to install development dependencies (continuing anyway)"
		fi
	fi

	# Install directly from pyproject.toml (modern approach)
	print_status "Installing package from pyproject.toml using hatchling backend..."
	if pip install -e .; then
		print_success "$PACKAGE_NAME has been successfully installed"
		print_status "You can now run 'qsmonitor' to start the application"
	else
		print_error "Failed to install $PACKAGE_NAME"
		exit 1
	fi
}

# Function to uninstall package
uninstall_package() {
	print_status "Uninstalling $PACKAGE_NAME..."

	if is_installed; then
		if pip uninstall -y qsutils; then
			print_success "$PACKAGE_NAME has been successfully uninstalled"
		else
			print_error "Failed to uninstall $PACKAGE_NAME"
			exit 1
		fi
	else
		print_warning "$PACKAGE_NAME is not installed"
	fi
}

# Function to force reinstall package
force_reinstall_package() {
	print_status "Force reinstalling $PACKAGE_NAME..."

	# Install development dependencies first
	if [ -f "requirements.txt" ]; then
		print_status "Installing development dependencies..."
		if pip install -r requirements.txt; then
			print_success "Development dependencies installed successfully"
		else
			print_warning "Failed to install development dependencies (continuing anyway)"
		fi
	fi

	# Force reinstall directly from pyproject.toml (modern approach)
	print_status "Force reinstalling package from pyproject.toml using hatchling backend..."
	if pip install -e . --force-reinstall; then
		print_success "$PACKAGE_NAME has been successfully reinstalled"
		print_status "You can now run 'qsmonitor' to start the application"
	else
		print_error "Failed to reinstall $PACKAGE_NAME"
		exit 1
	fi
}

# Function to show help
show_help() {
	echo "QSUtils Installation Script (Modern pyproject.toml + hatchling)"
	echo ""
	echo "Usage: $0 [OPTION]"
	echo ""
	echo "Options:"
	echo "  (no option)   Install $PACKAGE_NAME (default)"
	echo "  --uninstall   Uninstall $PACKAGE_NAME"
	echo "  --force       Force reinstall $PACKAGE_NAME"
	echo "  --help        Show this help message"
	echo ""
	echo "Examples:"
	echo "  $0              # Install the package (default)"
	echo "  $0 --uninstall   # Uninstall the package"
	echo "  $0 --force       # Force reinstall the package"
	echo ""
	echo "Features:"
	echo "  - Modern pyproject.toml based installation"
	echo "  - Uses hatchling build backend for faster builds"
	echo "  - Automatically installs development dependencies from requirements.txt"
	echo "  - Runtime dependencies managed through pyproject.toml"
	echo "  - Editable installation for development convenience"
	echo "  - Checks for existing installations before proceeding"
	echo ""
	echo "Note: Python must be installed and available in PATH"
	echo "      The script uses 'pip install -e .' to install from pyproject.toml"
}

# Main script logic
case "${1:---install}" in
--install)
	if is_installed; then
		print_warning "$PACKAGE_NAME is already installed."
		print_status "To rebuild and reinstall, please use the '$0 --force' option."
		print_status "To uninstall, please use the '$0 --uninstall' option."
		exit 0
	fi
	install_package
	;;
--uninstall)
	uninstall_package
	;;
--force)
	force_reinstall_package
	;;
--help)
	show_help
	;;
"")
	# Default behavior - install
	if is_installed; then
		print_warning "$PACKAGE_NAME is already installed."
		print_status "To rebuild and reinstall, please use the '$0 --force' option."
		print_status "To uninstall, please use the '$0 --uninstall' option."
		exit 0
	fi
	install_package
	;;
*)
	print_error "Unknown option: $1"
	echo ""
	show_help
	exit 1
	;;
esac
