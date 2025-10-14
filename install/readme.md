# Levtiades Atlas Installation Guide

## 🚀 **Quick Start Installation**

Follow these steps to set up the Levtiades Atlas pipeline on a new computer:

### **Prerequisites**
- Python 3.8+
- Git (to clone this repository)
- Internet connection (for downloading dependencies and atlases)

---

## 📋 **Step-by-Step Installation**

### **1. Install Python Dependencies**
```bash
# Install required Python packages
python install/install_python_deps.py
```

This will install:
- nibabel, nilearn, templateflow (neuroimaging)
- numpy, scipy, pandas (scientific computing)
- matplotlib, seaborn (visualization)

### **2. Install ANTs (Advanced Neuroimaging Tools)**
```bash
# Install ANTs for template registration
bash install/install_ants.sh
```

**For Linux**: Downloads precompiled binaries
**For macOS**: Uses Homebrew if available
**For Windows**: Manual installation required (see troubleshooting)

### **3. Verify Installation**
```bash
# Test that everything is working
python install/test_installation.py
```

---

## 🔧 **Troubleshooting**

### **Python Issues**
```bash
# If pip install fails, try upgrading pip first:
python -m pip install --upgrade pip

# If you get permission errors, try:
python -m pip install --user -r install/requirements.txt

# For conda users:
conda install nibabel nilearn numpy scipy pandas matplotlib seaborn
pip install templateflow
```

### **ANTs Issues**

**Linux:**
- If precompiled binary fails, install build tools:
  ```bash
  sudo apt-get install cmake gcc g++ git
  # Then compile from source (see ANTs documentation)
  ```

**macOS:**
- Install Homebrew first: https://brew.sh
- Then run: `brew install ants`

**Windows:**
- Use Windows Subsystem for Linux (WSL2)
- Or install ANTs manually from: https://github.com/ANTsX/ANTs/releases

### **TemplateFlow Issues**
```bash
# If templateflow fails to download templates:
export TEMPLATEFLOW_HOME=/path/to/templateflow
python -c "import templateflow; templateflow.api.get('MNI152NLin2009cAsym', resolution=2)"
```

---

## 🧪 **Testing Your Installation**

After installation, test with a minimal example:

```bash
# Quick test
cd downloaded_atlases
python 0_downloading_destriux.py

cd ../levtiades_atlas
python 1_setup_levtiades_project.py

# If this succeeds, your installation is working!
```

---

## 🆘 **Getting Help**

### **Common Error Messages**

1. **"antsRegistrationSyNQuick.sh: command not found"**
   - ANTs not installed or not in PATH
   - Run `bash install/install_ants.sh`
   - Add ANTs to PATH: `export PATH="/path/to/ants/bin:$PATH"`

2. **"No module named 'nibabel'"**
   - Python dependencies not installed
   - Run `python install/install_python_deps.py`

3. **"RuntimeError: TemplateFlow failed to get"**
   - Internet connection issue or TemplateFlow cache problem
   - Try: `rm -rf ~/.cache/templateflow` and retry

4. **Memory errors during atlas creation**
   - Ensure 8GB+ RAM available
   - Close other applications
   - Consider using swap space

### **System Requirements**

**Minimum:**
- Python 3.8+
- 8GB RAM
- 5GB disk space
- Internet connection

**Recommended:**
- Python 3.9+
- 16GB RAM
- 10GB disk space
- Fast internet connection

---

## 📚 **Additional Resources**

- **ANTs Documentation**: https://github.com/ANTsX/ANTs
- **Nilearn Documentation**: https://nilearn.github.io/
- **TemplateFlow**: https://www.templateflow.org/

---

## ✅ **Verification Checklist**

After installation, verify these commands work:

- [ ] `python --version` (shows 3.8+)
- [ ] `python -c "import nibabel; print('nibabel OK')"`
- [ ] `python -c "import nilearn; print('nilearn OK')"`
- [ ] `python -c "import templateflow; print('templateflow OK')"`
- [ ] `antsRegistrationSyNQuick.sh` (shows help message)
- [ ] `antsApplyTransforms` (shows help message)

If all checkboxes pass, you're ready to run the Levtiades pipeline!