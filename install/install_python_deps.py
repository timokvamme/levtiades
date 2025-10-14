#!/usr/bin/env python3
"""
Install Python Dependencies for Levtiades Atlas Pipeline
=======================================================

This script installs all required Python packages for the Levtiades Atlas pipeline.
Run this script first before running the atlas creation steps.

Usage:
    python install/install_python_deps.py

Requirements:
    - Python 3.8+
    - pip package manager
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is sufficient"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required. Current version:", f"{version.major}.{version.minor}")
        print("   Please install Python 3.8 or higher")
        return False

    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_requirements():
    """Install packages from requirements.txt"""

    requirements_file = Path(__file__).parent / "requirements.txt"

    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return False

    print("📦 Installing Python dependencies...")
    print(f"   Reading requirements from: {requirements_file}")

    try:
        # Install packages
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ All Python dependencies installed successfully!")
            return True
        else:
            print("❌ Error installing dependencies:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error during installation: {e}")
        return False

def test_imports():
    """Test that key packages can be imported"""

    print("\n🔍 Testing package imports...")

    test_packages = [
        "nibabel",
        "nilearn",
        "templateflow",
        "numpy",
        "scipy",
        "pandas",
        "matplotlib",
        "seaborn"
    ]

    failed_imports = []

    for package in test_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError as e:
            print(f"   ❌ {package}: {e}")
            failed_imports.append(package)

    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("   Try running: pip install --upgrade " + " ".join(failed_imports))
        return False

    print("\n✅ All packages imported successfully!")
    return True

def main():
    """Main installation function"""

    print("🧠 LEVTIADES ATLAS - PYTHON DEPENDENCIES INSTALLER")
    print("=" * 60)

    # Check Python version
    if not check_python_version():
        return 1

    # Install requirements
    if not install_requirements():
        return 1

    # Test imports
    if not test_imports():
        return 1

    print("\n🎉 Python environment setup complete!")
    print("\n📝 Next steps:")
    print("   1. Install ANTs: run install/install_ants.sh")
    print("   2. Run pipeline: cd downloaded_atlases && python 0_downloading_destriux.py")

    return 0

if __name__ == "__main__":
    sys.exit(main())