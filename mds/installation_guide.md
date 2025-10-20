# levtiades atlas installation guide

## quick start for new users

### prerequisites
- python 3.8+
- git
- internet connection
- 8gb+ ram recommended
- 5gb+ free disk space

### one-command installation
```bash
# Install Python dependencies
python install/install_python_deps.py

# Install ANTs (neuroimaging tools)
bash install/install_ants.sh

# Verify everything works
python install/test_installation.py
```

if all tests pass, you're ready to run the pipeline!

## detailed installation steps

### 1. python dependencies
```bash
python install/install_python_deps.py
```

**what this installs:**
- nibabel, nilearn (neuroimaging i/o)
- templateflow (brain template api)
- numpy, scipy, pandas (scientific computing)
- matplotlib, seaborn (visualization)

### 2. ants installation
```bash
bash install/install_ants.sh
```

**installation strategy:**
1. **conda (preferred)**: complete ants toolset with all dependencies
2. **binary fallback**: precompiled binaries for linux x86_64
3. **manual**: instructions for custom compilation

**required ants tools:**
- `antsRegistration` - template-to-template registration
- `antsApplyTransforms` - transform application

### 3. verification
```bash
python install/test_installation.py
```

**tests performed:**
- python version compatibility (3.8+)
- package import verification
- ants tool availability
- templateflow download capability
- file structure validation
- system resource check

## platform-specific notes

### linux (ubuntu/debian)
```bash
# If conda installation fails, install build tools:
sudo apt-get install cmake gcc g++ git

# Then retry ANTs installation
bash install/install_ants.sh
```

### macos
```bash
# Install Homebrew if not available
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# ANTs installation will use Homebrew automatically
bash install/install_ants.sh
```

### windows
- **recommended**: use windows subsystem for linux (wsl2)
- **alternative**: manual ants installation from github releases

## troubleshooting

### common issues

#### "antsregistration: command not found"
```bash
# ANTs not installed or not in PATH
bash install/install_ants.sh

# If using binary installation, add to PATH:
export PATH="/path/to/ants/bin:$PATH"
```

#### "no module named 'nibabel'"
```bash
# Python dependencies not installed
python install/install_python_deps.py

# Alternative with conda:
conda install nibabel nilearn numpy scipy pandas matplotlib seaborn
pip install templateflow
```

#### "templateflow failed to get template"
```bash
# Clear TemplateFlow cache
rm -rf ~/.cache/templateflow

# Check internet connection and retry
python -c "import templateflow.api as tf; tf.get('MNI152NLin2009cAsym', suffix='T1w', resolution=2)"
```

#### memory errors during atlas creation
- ensure 8gb+ ram available
- close other applications
- consider using swap space

### advanced installation

#### custom conda environment
```bash
# Create dedicated environment
conda create -n levtiades python=3.11
conda activate levtiades

# Install ANTs and dependencies
conda install ants -c conda-forge
pip install nibabel nilearn templateflow numpy scipy pandas matplotlib seaborn
```

#### from source (if binary/conda fails)
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

## verification checklist

after installation, verify these commands work:

- [ ] `python --version` (shows 3.8+)
- [ ] `python -c "import nibabel; print('nibabel OK')"`
- [ ] `python -c "import nilearn; print('nilearn OK')"`
- [ ] `python -c "import templateflow; print('templateflow OK')"`
- [ ] `antsRegistration --help` (shows help message)
- [ ] `antsApplyTransforms --help` (shows help message)

## system requirements

### minimum
- python 3.8+
- 8gb ram
- 5gb disk space
- internet connection

### recommended
- python 3.9+
- 16gb ram
- 10gb disk space
- fast internet connection

## next steps

after successful installation:

1. **run the pipeline:**
   ```bash
   cd downloaded_atlases
   python 0_downloading_destriux.py

   cd ../levtiades_atlas
   python 1_setup_levtiades_project.py
   python 2_levtiades_to_mni2009c.py
   python 3_enhanced_qc_validation.py
   ```

2. **see pipeline documentation:**
   - `mds/WORKFLOW.md` - detailed pipeline steps
   - `mds/README.md` - project overview
   - `mds/TESTING_RESULTS.md` - validation results

## support

for installation issues:
1. check `install/README.md` for detailed troubleshooting
2. review error messages carefully
3. ensure internet connection for downloads
4. try conda installation method if binary fails