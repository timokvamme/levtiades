#!/usr/bin/env python3
"""
Test Installation for Levtiades Atlas Pipeline
==============================================

This script tests that all dependencies are properly installed
and ready for running the Levtiades Atlas creation pipeline.

Usage:
    python install/test_installation.py
"""

import sys
import subprocess
import os
from pathlib import Path

def test_python_version():
    """Test Python version is sufficient"""
    print("🐍 Testing Python version...")

    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current: {version.major}.{version.minor}")
        return False

    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def test_python_packages():
    """Test that required Python packages are installed"""
    print("\n📦 Testing Python packages...")

    required_packages = [
        ("nibabel", "Neuroimaging file I/O"),
        ("nilearn", "Neuroimaging machine learning"),
        ("templateflow", "Template flow API"),
        ("numpy", "Numerical computing"),
        ("scipy", "Scientific computing"),
        ("pandas", "Data analysis"),
        ("matplotlib", "Plotting"),
        ("seaborn", "Statistical visualization")
    ]

    failed_packages = []

    for package, description in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package:<12} - {description}")
        except ImportError as e:
            print(f"   ❌ {package:<12} - MISSING: {e}")
            failed_packages.append(package)

    if failed_packages:
        print(f"\n❌ Missing packages: {', '.join(failed_packages)}")
        print("   Run: python install/install_python_deps.py")
        return False

    return True

def test_ants_installation():
    """Test that ANTs tools are available"""
    print("\n🧠 Testing ANTs installation...")

    ants_tools = [
        ("antsRegistrationSyNQuick.sh", "Template registration"),
        ("antsApplyTransforms", "Transform application")
    ]

    missing_tools = []

    for tool, description in ants_tools:
        try:
            result = subprocess.run([tool, "--help"],
                                  capture_output=True,
                                  text=True,
                                  timeout=10)
            print(f"   ✅ {tool:<25} - {description}")
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            print(f"   ❌ {tool:<25} - MISSING")
            missing_tools.append(tool)

    if missing_tools:
        print(f"\n❌ Missing ANTs tools: {', '.join(missing_tools)}")
        print("   Run: bash install/install_ants.sh")
        print("   OR if conda is available: conda install ants -c conda-forge")
        return False

    return True

def test_templateflow():
    """Test TemplateFlow can download templates"""
    print("\n🗺️  Testing TemplateFlow...")

    try:
        import templateflow.api as tf

        # Test downloading a small template
        print("   🔄 Testing template download (this may take a moment)...")
        template = tf.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w')

        if template and Path(template).exists():
            print(f"   ✅ Template downloaded: {Path(template).name}")
            return True
        else:
            print("   ❌ Template download failed")
            return False

    except Exception as e:
        print(f"   ❌ TemplateFlow error: {e}")
        print("   Check internet connection and try:")
        print("   rm -rf ~/.cache/templateflow")
        return False

def test_file_structure():
    """Test that required files are present"""
    print("\n📁 Testing file structure...")

    required_files = [
        "downloaded_atlases/0_downloading_destriux.py",
        "levtiades_atlas/1_setup_levtiades_project.py",
        "levtiades_atlas/2_levtiades_to_mni2009c.py",
        "levtiades_atlas/3_enhanced_qc_validation.py"
    ]

    missing_files = []

    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        return False

    return True

def test_system_resources():
    """Test system has sufficient resources"""
    print("\n💾 Testing system resources...")

    try:
        import psutil

        # Check RAM
        ram_gb = psutil.virtual_memory().total / (1024**3)
        print(f"   💿 Total RAM: {ram_gb:.1f} GB")

        if ram_gb < 8:
            print("   ⚠️  Warning: <8GB RAM may cause issues with large atlases")
        else:
            print("   ✅ Sufficient RAM available")

        # Check disk space
        disk_gb = psutil.disk_usage('.').free / (1024**3)
        print(f"   💽 Available disk: {disk_gb:.1f} GB")

        if disk_gb < 5:
            print("   ⚠️  Warning: <5GB disk space may be insufficient")
        else:
            print("   ✅ Sufficient disk space")

    except ImportError:
        print("   ⚠️  psutil not available, skipping resource check")
        print("   Install with: pip install psutil")

def main():
    """Run all installation tests"""

    print("🧠 LEVTIADES ATLAS - INSTALLATION TEST")
    print("=" * 50)

    tests = [
        ("Python Version", test_python_version),
        ("Python Packages", test_python_packages),
        ("ANTs Tools", test_ants_installation),
        ("TemplateFlow", test_templateflow),
        ("File Structure", test_file_structure)
    ]

    failed_tests = []

    for test_name, test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            failed_tests.append(test_name)

    # System resources (non-critical)
    test_system_resources()

    print("\n" + "=" * 50)

    if failed_tests:
        print(f"❌ FAILED TESTS: {', '.join(failed_tests)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Run: python install/install_python_deps.py")
        print("   2. Run: bash install/install_ants.sh")
        print("   3. Check internet connection for TemplateFlow")
        print("   4. See install/README.md for detailed help")
        return 1
    else:
        print("✅ ALL TESTS PASSED!")
        print("\n🎉 Installation successful!")
        print("\n📝 Ready to run Levtiades pipeline:")
        print("   cd downloaded_atlases && python 0_downloading_destriux.py")
        print("   cd ../levtiades_atlas && python 1_setup_levtiades_project.py")
        return 0

if __name__ == "__main__":
    sys.exit(main())