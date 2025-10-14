# Quality Control Images - Levtiades Atlas

## Overview

The Levtiades Atlas pipeline generates multiple quality control (QC) images to validate registration accuracy and atlas combination. All QC images are stored in the `qc_validation/` folder.

## QC Images from Step 2 (Atlas Creation)

The Step 2 script (`2_levtiades_to_mni2009c.py`) generates basic QC overlays:

### Basic Overlap Visualization
- **File**: `qc_validation/overlap_visualization.nii.gz`
- **Purpose**: Shows spatial overlaps between component atlases
- **Values**:
  - 0 = No atlas coverage
  - 1 = Levinson-Tian overlap
  - 2 = Levinson-Destrieux overlap
  - 3 = Tian-Destrieux overlap
  - 4 = All three atlases overlap

### Individual Atlas Masks
- **levinson_mask.nii.gz** (value=100): Brainstem nuclei coverage
- **tian_mask.nii.gz** (value=150): Subcortical structure coverage
- **destrieux_mask.nii.gz** (value=200): Cortical area coverage

## QC Images from Step 3 (Enhanced Validation)

The Step 3 script (`3_enhanced_qc_validation.py`) generates comprehensive validation:

### Registration Quality Control
- **Location**: `qc_validation/registration_qc/`
- **Files**: PNG images showing template-to-template alignment quality
- **Purpose**: Visual inspection of anatomical registration accuracy

### Overlap Analysis
- **Location**: `qc_validation/qc_overlays/`
- **Files**: Detailed overlap visualizations and statistics
- **Purpose**: Quantitative analysis of atlas boundary interactions

### Centroid Validation
- **Location**: `qc_validation/centroid_validation/`
- **Files**: Analysis of region centroid displacement during processing
- **Purpose**: Measure registration accuracy (<2mm acceptable)

## Expert Review Process

### Visual Inspection Checklist
1. **Registration Quality**: Check anatomical plausibility in registration_qc images
2. **Overlap Patterns**: Verify expected boundary overlaps in qc_overlays
3. **Centroid Accuracy**: Confirm <95% of regions show <2mm displacement
4. **Template Alignment**: Verify proper MNI2009c space alignment
5. **Hierarchical Priority**: Ensure brainstem nuclei take precedence

### Quality Thresholds
- **Registration**: Smooth, anatomically plausible transformations
- **Centroid displacement**: <2mm acceptable, <1mm excellent
- **Overlap areas**: Minimal overlaps at anatomical boundaries only
- **Coverage**: Complete brain coverage without gaps

## Technical Implementation

### Step 2 QC Function
```python
def create_qc_overlays(lev_path, tian_path, des_path, out_dir, ref_tpl):
    # Creates basic overlap visualization and individual masks
    # Outputs to qc_validation/ folder
```

### Output Format
- **File format**: NIfTI (.nii.gz) for 3D visualization
- **Coordinate system**: MNI152NLin2009cAsym (2mm isotropic)
- **Visualization**: Compatible with FSLView, MRIcroGL, and other neuroimaging viewers

### Quality Assurance
- All QC images use same spatial template as final atlas
- Consistent coordinate system across all outputs
- Integer values for clear region identification
- Expert-reviewable format for validation workflow

## Usage in Validation Workflow

1. **Automated Generation**: QC images created automatically during Steps 2 and 3
2. **Expert Review**: Manual inspection using neuroimaging software
3. **Issue Detection**: Identify registration or combination problems
4. **Iteration**: Re-run processing with adjusted parameters if needed
5. **Final Approval**: Expert sign-off on atlas quality before use

## File Organization

```
qc_validation/
├── overlap_visualization.nii.gz      # Basic overlap map (Step 2)
├── levinson_mask.nii.gz             # Brainstem coverage (Step 2)
├── tian_mask.nii.gz                 # Subcortical coverage (Step 2)
├── destrieux_mask.nii.gz            # Cortical coverage (Step 2)
├── registration_qc/                 # Registration validation (Step 3)
├── qc_overlays/                     # Detailed overlap analysis (Step 3)
├── centroid_validation/             # Accuracy metrics (Step 3)
└── expert_qc_report.md              # Comprehensive QC report (Step 3)
```