# TianDes Limbic-Cortical Atlas

## Overview
Combined brain atlas integrating:
- **Tian Subcortical Atlas (Scale IV)**: 54 fine-grained subcortical regions
- **Destrieux Cortical Atlas**: 148 sulco-gyral cortical regions

## Technical Specifications
- **Space**: MNI152NLin6Asym
- **Resolution**: 2×2×2 mm voxels
- **Dimensions**: 91×109×91 voxels
- **Format**: NIfTI-1 (.nii.gz)

## Label Scheme
- **Subcortical (Tian)**: Labels 1-54
- **Cortical (Destrieux)**: Labels 101-250
- **Total Regions**: ~200 brain regions

## Overlap Resolution
- **Strategy**: Tian priority in subcortical zones
- **Principle**: Preserve detailed subcortical parcellation
- **Boundary**: Natural limbic-cortical interface

## Files
- `tiandes_combined.nii.gz` - Main atlas file
- `tiandes_labels.txt` - Region labels
- `tiandes_lookup_table.txt` - Color lookup table
- `tiandes_region_stats.csv` - Volume statistics

## Citation
Please cite both source atlases:
- Tian et al. (2020) Nature Neuroscience - Melbourne Subcortex Atlas
- Destrieux et al. (2010) NeuroImage - Cortical parcellation

## Usage
Compatible with:
- FSL
- FreeSurfer
- AFNI
- MRIcrogl
- Python (nibabel, nilearn)
- R (oro.nifti, ANTsR)
