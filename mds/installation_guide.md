# Levtiades Atlas Installation Guide

## Quick Start for New Users

### Prerequisites
- Python 3.8+
- Git
- Internet connection
- 8GB+ RAM recommended
- 5GB+ free disk space

### One-Command Installation
```bash
# Install Python dependencies
python install/install_python_deps.py

# Install ANTs (neuroimaging tools)
bash install/install_ants.sh

# Verify everything works
python install/test_installation.py
```

If all tests pass, you're ready to run the pipeline!

## Detailed Installation Steps

### 1. Python Dependencies
```bash
python install/install_python_deps.py
```

**What this installs:**
- nibabel, nilearn (neuroimaging I/O)
- templateflow (brain template API)
- numpy, scipy, pandas (scientific computing)
- matplotlib, seaborn (visualization)

### 2. ANTs Installation
```bash
bash install/install_ants.sh
```

**Installation Strategy:**
1. **Conda (preferred)**: Complete ANTs toolset with all dependencies
2. **Binary fallback**: Precompiled binaries for Linux x86_64
3. **Manual**: Instructions for custom compilation

**Required ANTs Tools:**
- `antsRegistration` - Template-to-template registration
- `antsApplyTransforms` - Transform application

### 3. Verification
```bash
python install/test_installation.py
```

**Tests Performed:**
- Python version compatibility (3.8+)
- Package import verification
- ANTs tool availability
- TemplateFlow download capability
- File structure validation
- System resource check

## Platform-Specific Notes

### Linux (Ubuntu/Debian)
```bash
# If conda installation fails, install build tools:
sudo apt-get install cmake gcc g++ git

# Then retry ANTs installation
bash install/install_ants.sh
```

### macOS
```bash
# Install Homebrew if not available
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# ANTs installation will use Homebrew automatically
bash install/install_ants.sh
```

### Windows
- **Recommended**: Use Windows Subsystem for Linux (WSL2)
- **Alternative**: Manual ANTs installation from GitHub releases

## Troubleshooting

### Common Issues

#### "antsRegistration: command not found"
```bash
# ANTs not installed or not in PATH
bash install/install_ants.sh

# If using binary installation, add to PATH:
export PATH="/path/to/ants/bin:$PATH"
```

#### "No module named 'nibabel'"
```bash
# Python dependencies not installed
python install/install_python_deps.py

# Alternative with conda:
conda install nibabel nilearn numpy scipy pandas matplotlib seaborn
pip install templateflow
```

#### "TemplateFlow failed to get template"
```bash
# Clear TemplateFlow cache
rm -rf ~/.cache/templateflow

# Check internet connection and retry
python -c "import templateflow.api as tf; tf.get('MNI152NLin2009cAsym', suffix='T1w', resolution=2)"
```

#### Memory errors during atlas creation
- Ensure 8GB+ RAM available
- Close other applications
- Consider using swap space

### Advanced Installation

#### Custom Conda Environment
```bash
# Create dedicated environment
conda create -n levtiades python=3.11
conda activate levtiades

# Install ANTs and dependencies
conda install ants -c conda-forge
pip install nibabel nilearn templateflow numpy scipy pandas matplotlib seaborn
```

#### From Source (if binary/conda fails)
```bash
# Install build dependencies
sudo apt-get install cmake gcc g++ git

# Clone and build ANTs
git clone https://github.com/ANTsX/ANTs.git
cd ANTs
mkdir build && cd build
cmake ..
make -j4
```

## Verification Checklist

After installation, verify these commands work:

- [ ] `python --version` (shows 3.8+)
- [ ] `python -c "import nibabel; print('nibabel OK')"`
- [ ] `python -c "import nilearn; print('nilearn OK')"`
- [ ] `python -c "import templateflow; print('templateflow OK')"`
- [ ] `antsRegistration --help` (shows help message)
- [ ] `antsApplyTransforms --help` (shows help message)

## System Requirements

### Minimum
- Python 3.8+
- 8GB RAM
- 5GB disk space
- Internet connection

### Recommended
- Python 3.9+
- 16GB RAM
- 10GB disk space
- Fast internet connection

## Next Steps

After successful installation:

1. **Run the pipeline:**
   ```bash
   cd downloaded_atlases
   python 0_downloading_destriux.py

   cd ../levtiades_atlas
   python 1_setup_levtiades_project.py
   python 2_levtiades_to_mni2009c.py
   python 3_enhanced_qc_validation.py
   ```

2. **See pipeline documentation:**
   - `mds/WORKFLOW.md` - Detailed pipeline steps
   - `mds/README.md` - Project overview
   - `mds/TESTING_RESULTS.md` - Validation results

## Support

For installation issues:
1. Check `install/README.md` for detailed troubleshooting
2. Review error messages carefully
3. Ensure internet connection for downloads
4. Try conda installation method if binary fails