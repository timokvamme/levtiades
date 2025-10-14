#!/bin/bash

# ANTs Installation Script for Levtiades Atlas Pipeline
# =====================================================
#
# This script installs ANTs (Advanced Neuroimaging Tools) which is required
# for the template-to-template registration in the Levtiades pipeline.
#
# Usage:
#   bash install/install_ants.sh
#
# Requirements:
#   - Linux or macOS
#   - wget or curl
#   - cmake, gcc, g++ (for compilation)

set -e  # Exit on any error

echo "🧠 LEVTIADES ATLAS - ANTs INSTALLER"
echo "===================================="

# Detect OS
OS=$(uname -s)
ARCH=$(uname -m)

echo "🖥️  Detected system: $OS $ARCH"

# Check if ANTs is already installed
if command -v antsRegistrationSyNQuick.sh &> /dev/null && command -v antsApplyTransforms &> /dev/null; then
    echo "✅ ANTs already installed and on PATH"
    echo "   antsRegistrationSyNQuick.sh: $(which antsRegistrationSyNQuick.sh)"
    echo "   antsApplyTransforms: $(which antsApplyTransforms)"
    echo "🎉 ANTs installation check complete!"
    exit 0
fi

echo "📦 ANTs not found. Installing..."

# Create install directory
INSTALL_DIR="$PWD/install/ants_local"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo "📁 Installing to: $INSTALL_DIR"

case "$OS" in
    "Linux")
        echo "🐧 Installing ANTs for Linux..."

        # Try conda first (most reliable)
        if command -v conda &> /dev/null; then
            echo "🐍 Installing ANTs via conda (recommended)..."
            conda install ants -c conda-forge -y
            if command -v antsRegistration &> /dev/null && command -v antsApplyTransforms &> /dev/null; then
                echo "✅ ANTs installed successfully via conda"
                exit 0
            else
                echo "⚠️  Conda installation incomplete, trying binary fallback..."
            fi
        fi

        # Try to download precompiled binary as fallback
        if [ "$ARCH" = "x86_64" ]; then
            echo "📥 Downloading precompiled ANTs binary..."

            # Download latest ANTs release
            ANTS_VERSION="2.5.0"
            ANTS_URL="https://github.com/ANTsX/ANTs/releases/download/v${ANTS_VERSION}/ants-${ANTS_VERSION}-centos7-X64-gcc.zip"

            if command -v wget &> /dev/null; then
                wget -O ants.zip "$ANTS_URL"
            elif command -v curl &> /dev/null; then
                curl -L -o ants.zip "$ANTS_URL"
            else
                echo "❌ Neither wget nor curl found. Please install one of them."
                exit 1
            fi

            # Extract
            if command -v unzip &> /dev/null; then
                unzip ants.zip
                rm ants.zip

                # Find the extracted directory
                ANTS_DIR=$(find . -name "ants-*" -type d | head -1)
                if [ -n "$ANTS_DIR" ]; then
                    echo "✅ ANTs extracted to: $ANTS_DIR"
                    ANTS_BIN="$INSTALL_DIR/$ANTS_DIR/bin"
                else
                    echo "❌ Could not find extracted ANTs directory"
                    exit 1
                fi
            else
                echo "❌ unzip not found. Please install unzip."
                exit 1
            fi
        else
            echo "⚠️  No precompiled binary for $ARCH. Trying conda installation..."
            if command -v conda &> /dev/null; then
                echo "🐍 Installing ANTs via conda..."
                conda install ants -c conda-forge -y
                if command -v antsRegistration &> /dev/null && command -v antsApplyTransforms &> /dev/null; then
                    echo "✅ ANTs installed successfully via conda"
                    exit 0
                else
                    echo "❌ Conda installation failed or incomplete"
                    exit 1
                fi
            else
                echo "❌ Conda not available. You may need to compile from source."
                echo "   See: https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Linux-and-Mac-OS"
                exit 1
            fi
        fi
        ;;

    "Darwin")
        echo "🍎 Installing ANTs for macOS..."

        # Check if Homebrew is available
        if command -v brew &> /dev/null; then
            echo "🍺 Installing ANTs via Homebrew..."
            brew install ants
            echo "✅ ANTs installed via Homebrew"
            exit 0
        else
            echo "⚠️  Homebrew not found. You can install it from: https://brew.sh"
            echo "   Or compile ANTs from source: https://github.com/ANTsX/ANTs"
            exit 1
        fi
        ;;

    *)
        echo "❌ Unsupported operating system: $OS"
        echo "   Please install ANTs manually: https://github.com/ANTsX/ANTs"
        exit 1
        ;;
esac

# Add to PATH for current session
if [ -n "$ANTS_BIN" ] && [ -d "$ANTS_BIN" ]; then
    export PATH="$ANTS_BIN:$PATH"

    echo "✅ ANTs installed successfully!"
    echo "📍 ANTs location: $ANTS_BIN"

    # Test installation
    if command -v antsRegistrationSyNQuick.sh &> /dev/null; then
        echo "✅ antsRegistrationSyNQuick.sh found"
    else
        echo "❌ antsRegistrationSyNQuick.sh not found in PATH"
    fi

    if command -v antsApplyTransforms &> /dev/null; then
        echo "✅ antsApplyTransforms found"
    else
        echo "❌ antsApplyTransforms not found in PATH"
        echo "🔄 Binary installation incomplete. Trying conda fallback..."
        if command -v conda &> /dev/null; then
            echo "🐍 Installing ANTs via conda as fallback..."
            conda install ants -c conda-forge -y
            if command -v antsApplyTransforms &> /dev/null; then
                echo "✅ ANTs completed via conda fallback"
            else
                echo "❌ Complete ANTs installation failed"
                exit 1
            fi
        else
            echo "❌ Conda not available for fallback. Installation incomplete."
            exit 1
        fi
    fi

    echo ""
    echo "🔧 To use ANTs in future sessions, add this to your ~/.bashrc or ~/.zshrc:"
    echo "   export PATH=\"$ANTS_BIN:\$PATH\""
    echo ""
    echo "   Or run this command:"
    echo "   echo 'export PATH=\"$ANTS_BIN:\$PATH\"' >> ~/.bashrc"
    echo ""
fi

echo "🎉 ANTs installation complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Add ANTs to your PATH (see instructions above)"
echo "   2. Run the Levtiades pipeline:"
echo "      cd downloaded_atlases && python 0_downloading_destriux.py"