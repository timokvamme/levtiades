# Individual ROIs from Original Source Atlases

This directory contains individual ROI binary masks extracted **directly from the
original source atlases** before they were combined into the final Levtiades atlas.

## Key Difference from `individual_rois/`

| Directory | Source | Indexing |
|-----------|--------|----------|
| `individual_rois/` | Final combined Levtiades atlas | Sequential 1-207 |
| `individual_rois_from_original_atlases/` | Original source atlases | Original indices |

## Directory Structure

```
individual_rois_from_original_atlases/
├── levinson/           # 5 brainstem ROIs (indices 1-5)
├── tian/               # 54 subcortical ROIs (indices 1-54)
├── destrieux/          # 148 cortical ROIs (original indices)
├── original_to_levtiades_mapping.csv
└── README.md
```

## Source Atlases

### 1. Levinson-Bari Limbic Brainstem Atlas (2022)
- **Regions:** 5 (LC, NTS, VTA, PAG, DRN)
- **Original indices:** 1-5
- **Reference:** Levinson et al. (2022) - Limbic Brainstem Atlas for Depression Research

### 2. Tian Melbourne Subcortical Atlas Scale IV (2020)
- **Regions:** 54 (HIP, THA, PUT, CAU, AMY, NAc, GP subdivisions)
- **Original indices:** 1-27 (Right), 28-54 (Left)
- **Reference:** Tian et al. (2020) Nature Neuroscience 23(11), 1421-1432
- **Note:** Original Tian ordering is RIGHT-before-LEFT; Levtiades reorders to LEFT-first

### 3. Destrieux Cortical Parcellation (2010)
- **Regions:** 148 (sulco-gyral cortical parcellation)
- **Original indices:** 1-75 (Left), 76-150 (Right), with gaps for medial wall
- **Reference:** Destrieux et al. (2010) NeuroImage 53(1), 1-15

## File Naming Convention

```
<source>_<original_index>_<region_name>.nii.gz
```

Examples:
- `levinson_001_Locus_Coeruleus_LC.nii.gz`
- `tian_028_HIP-head-m1-lh.nii.gz`
- `destrieux_076_R_G_and_S_frontomargin.nii.gz`

## Mapping to Levtiades Atlas

The `original_to_levtiades_mapping.csv` file provides the correspondence between:
- Original atlas indices
- Final Levtiades sequential indices (1-207)
- Region names and voxel counts

## Usage

These ROIs are useful when you need:
1. Comparison with original atlas publications
2. Analysis using original atlas conventions
3. Cross-validation between original and combined atlas
4. Debugging or quality assurance of the atlas combination process
