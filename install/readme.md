# levtiades atlas installation guide

## 🚀 **quick start installation**

follow these steps to set up the levtiades atlas pipeline on a new computer:

### **prerequisites**
- python 3.8+
- git (to clone this repository)
- internet connection (for downloading dependencies and atlases)

---

## 📋 **step-by-step installation**

### **1. install python dependencies**
```bash
# Install required Python packages
python install/install_python_deps.py
```

this will install:
- nibabel, nilearn, templateflow (neuroimaging)
- numpy, scipy, pandas (scientific computing)
- matplotlib, seaborn (visualization)

### **2. install ants (advanced neuroimaging tools)**
```bash
# Install ANTs for template registration
bash install/install_ants.sh
```

**for linux**: downloads precompiled binaries
**for macos**: uses homebrew if available
**for windows**: manual installation required (see troubleshooting)

### **3. verify installation**
```bash
# Test that everything is working
python install/test_installation.py
```

---

## 🔧 **troubleshooting**

### **python issues**
```bash
# If pip install fails, try upgrading pip first:
python -m pip install --upgrade pip

# If you get permission errors, try:
python -m pip install --user -r install/requirements.txt

# For conda users:
conda install nibabel nilearn numpy scipy pandas matplotlib seaborn
pip install templateflow
```

### **ants issues**

**linux:**
- if precompiled binary fails, install build tools:
  ```bash
  sudo apt-get install cmake gcc g++ git
  # Then compile from source (see ANTs documentation)
  ```

**macos:**
- install homebrew first: https://brew.sh
- then run: `brew install ants`

**windows:**
- use windows subsystem for linux (wsl2)
- or install ants manually from: https://github.com/antsx/ants/releases

### **templateflow issues**
```bash
# If templateflow fails to download templates:
export TEMPLATEFLOW_HOME=/path/to/templateflow
python -c "import templateflow; templateflow.api.get('MNI152NLin2009cAsym', resolution=2)"
```

---

## 🧪 **testing your installation**

after installation, test with a minimal example:

```bash
# Quick test
cd downloaded_atlases
python 0_downloading_destriux.py

cd ../levtiades_atlas
python 1_setup_levtiades_project.py

# If this succeeds, your installation is working!
```

---

## 🆘 **getting help**

### **common error messages**

1. **"antsregistrationsynquick.sh: command not found"**
   - ants not installed or not in path
   - run `bash install/install_ants.sh`
   - add ants to path: `export PATH="/path/to/ants/bin:$PATH"`

2. **"no module named 'nibabel'"**
   - python dependencies not installed
   - run `python install/install_python_deps.py`

3. **"runtimeerror: templateflow failed to get"**
   - internet connection issue or templateflow cache problem
   - try: `rm -rf ~/.cache/templateflow` and retry

4. **memory errors during atlas creation**
   - ensure 8gb+ ram available
   - close other applications
   - consider using swap space

### **system requirements**

**minimum:**
- python 3.8+
- 8gb ram
- 5gb disk space
- internet connection

**recommended:**
- python 3.9+
- 16gb ram
- 10gb disk space
- fast internet connection

---

## 📚 **additional resources**

- **ants documentation**: https://github.com/antsx/ants
- **nilearn documentation**: https://nilearn.github.io/
- **templateflow**: https://www.templateflow.org/

---

## ✅ **verification checklist**

after installation, verify these commands work:

- [ ] `python --version` (shows 3.8+)
- [ ] `python -c "import nibabel; print('nibabel OK')"`
- [ ] `python -c "import nilearn; print('nilearn OK')"`
- [ ] `python -c "import templateflow; print('templateflow OK')"`
- [ ] `antsRegistrationSyNQuick.sh` (shows help message)
- [ ] `antsApplyTransforms` (shows help message)

if all checkboxes pass, you're ready to run the levtiades pipeline!