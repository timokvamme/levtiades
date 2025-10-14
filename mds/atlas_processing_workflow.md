# Levtiades Atlas Processing Workflow

## Overview

The Levtiades Atlas combines three neuroimaging atlases into a unified brain parcellation optimized for psychiatric circuit analysis. Each component atlas undergoes specific processing to align to a common target space (MNI152NLin2009cAsym at 2.0mm resolution).

## Component Atlases & Processing

### 1. Levinson-Bari Limbic Brainstem Atlas
- **Purpose**: Critical brainstem nuclei for psychiatric disorders
- **Regions**: 5 nuclei (LC, NTS, VTA, PAG, DRN)
- **Original Space**: MNI152NLin2009bAsym (0.5mm high resolution)
- **Processing Method**: Same-space resampling via nilearn
- **Final Labels**: 1-5
- **Why Same-Space**: TemplateFlow template corruption required fallback to resampling approach

### 2. Tian Subcortical Atlas (Scale IV)
- **Purpose**: Fine-grained subcortical structures
- **Regions**: 54 subcortical areas (striatum, thalamus, hippocampus, amygdala, globus pallidus)
- **Original Space**: MNI152NLin6Asym (2mm)
- **Processing Method**: ANTs SyN template-to-template registration
- **Label Transformation**: Original 1-54 → Final 101-154 (+100 offset)
- **Registration Quality**: Smooth anatomical transformations verified

### 3. Destrieux Cortical Atlas
- **Purpose**: Comprehensive cortical parcellation
- **Regions**: 148 sulco-gyral areas (74 per hemisphere)
- **Original Space**: MNI152NLin2009aAsym (2mm) via nilearn
- **Processing Method**: ANTs SyN template-to-template registration
- **Label Transformation**: Original 1-148 → Final 201-348 (+200 offset)
- **Coverage**: Complete cortical gray matter

## Target Space Standardization

All atlases are aligned to:
- **Template**: MNI152NLin2009cAsym
- **Resolution**: 2.0mm isotropic voxels
- **Coordinate System**: RAS+ orientation
- **Interpolation**: Nearest neighbor (preserves integer labels)

## Hierarchical Combination Strategy

### Priority Order
1. **Levinson** (highest priority) - Brainstem nuclei
2. **Tian** (medium priority) - Subcortical structures
3. **Destrieux** (lowest priority) - Cortical areas

### Overlap Resolution
- Higher priority atlas overwrites lower priority in overlapping voxels
- Ensures psychiatric circuit nuclei (brainstem) are preserved
- Maintains anatomical hierarchy (deep → superficial structures)

## Output Files

### Individual Aligned Atlases
Located in `final_atlas/aligned/` for MRIcroGL visualization:
- `levinson_aligned.nii.gz` - Brainstem nuclei in target space
- `tian_aligned.nii.gz` - Subcortical regions in target space
- `destrieux_aligned.nii.gz` - Cortical areas in target space

### Combined Atlases
Located in `final_atlas/`:
- `with_overlaps/levtiades_final.nii.gz` - **Main output atlas** with all 207 regions
- `with_overlaps/levtiades_multichannel.nii.gz` - Multi-channel atlas format
- `no_overlaps/levtiades_hierarchical.nii.gz` - Hierarchical atlas (priority-based, no overlaps)

### Label Files
Located in `final_atlas/`:
- `levtiades_labels.txt` - Complete region labels and names
- `levtiades_lookup_table.txt` - Label lookup table for visualization
- `levtiades_labels.csv` - Detailed region information with coordinates

## Quality Control

### Registration Validation
- Visual inspection of template-to-template alignments
- Anatomical plausibility checking
- Centroid displacement analysis (<2mm acceptable)

### Overlap Analysis
- Statistical overlap quantification
- Boundary region identification
- Hierarchical priority verification

### Expert Review
- QC images in `qc_validation/registration_qc/`
- Overlap visualizations in `qc_validation/qc_overlays/`
- Comprehensive report in `qc_validation/expert_qc_report.md`

## Psychiatric Circuit Applications

### Target Disorders
- **Depression**: LC-DRN-VTA connectivity analysis
- **Anxiety**: PAG-amygdala-prefrontal circuit mapping
- **PTSD**: Brainstem arousal system investigation
- **Addiction**: VTA-striatal reward pathway studies

### Research Advantages
- Unified coordinate system for cross-study comparisons
- Hierarchical labeling preserves critical small nuclei
- Comprehensive coverage from brainstem to cortex
- Optimized for psychiatric neurocircuit research

## Technical Implementation

The processing pipeline is implemented in:
- `2_levtiades_to_mni2009c.py` - Main atlas creation script
- Uses ANTs for robust template-to-template registration
- Incorporates nilearn for same-space resampling fallback
- Implements comprehensive error handling and validation