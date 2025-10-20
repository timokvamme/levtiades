# quality control images - levtiades atlas

## overview

the levtiades atlas pipeline generates multiple quality control (qc) images to validate registration accuracy and atlas combination. all qc images are stored in the `qc_validation/` folder.

## qc images from step 2 (atlas creation)

the step 2 script (`2_levtiades_to_mni2009c.py`) generates basic qc overlays:

### basic overlap visualization
- **file**: `qc_validation/overlap_visualization.nii.gz`
- **purpose**: shows spatial overlaps between component atlases
- **values**:
  - 0 = no atlas coverage
  - 1 = levinson-tian overlap
  - 2 = levinson-destrieux overlap
  - 3 = tian-destrieux overlap
  - 4 = all three atlases overlap

### individual atlas masks
- **levinson_mask.nii.gz** (value=100): brainstem nuclei coverage
- **tian_mask.nii.gz** (value=150): subcortical structure coverage
- **destrieux_mask.nii.gz** (value=200): cortical area coverage

## qc images from step 3 (enhanced validation)

the step 3 script (`3_enhanced_qc_validation.py`) generates comprehensive validation:

### registration quality control
- **location**: `qc_validation/registration_qc/`
- **files**: png images showing template-to-template alignment quality
- **purpose**: visual inspection of anatomical registration accuracy

### overlap analysis
- **location**: `qc_validation/qc_overlays/`
- **files**: detailed overlap visualizations and statistics
- **purpose**: quantitative analysis of atlas boundary interactions

### centroid validation
- **location**: `qc_validation/centroid_validation/`
- **files**: analysis of region centroid displacement during processing
- **purpose**: measure registration accuracy (<2mm acceptable)

## expert review process

### visual inspection checklist
1. **registration quality**: check anatomical plausibility in registration_qc images
2. **overlap patterns**: verify expected boundary overlaps in qc_overlays
3. **centroid accuracy**: confirm <95% of regions show <2mm displacement
4. **template alignment**: verify proper mni2009c space alignment
5. **hierarchical priority**: ensure brainstem nuclei take precedence

### quality thresholds
- **registration**: smooth, anatomically plausible transformations
- **centroid displacement**: <2mm acceptable, <1mm excellent
- **overlap areas**: minimal overlaps at anatomical boundaries only
- **coverage**: complete brain coverage without gaps

## technical implementation

### step 2 qc function
```python
def create_qc_overlays(lev_path, tian_path, des_path, out_dir, ref_tpl):
    # Creates basic overlap visualization and individual masks
    # Outputs to qc_validation/ folder
```

### output format
- **file format**: nifti (.nii.gz) for 3d visualization
- **coordinate system**: mni152nlin2009casym (2mm isotropic)
- **visualization**: compatible with fslview, mricrogl, and other neuroimaging viewers

### quality assurance
- all qc images use same spatial template as final atlas
- consistent coordinate system across all outputs
- integer values for clear region identification
- expert-reviewable format for validation workflow

## usage in validation workflow

1. **automated generation**: qc images created automatically during steps 2 and 3
2. **expert review**: manual inspection using neuroimaging software
3. **issue detection**: identify registration or combination problems
4. **iteration**: re-run processing with adjusted parameters if needed
5. **final approval**: expert sign-off on atlas quality before use

## file organization

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