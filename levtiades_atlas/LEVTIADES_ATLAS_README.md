# Levtiades Atlas - Comprehensive Brain Parcellation

## Overview
The Levtiades atlas is a hierarchical brain parcellation combining:
- **Levinson-Bari**: 5 brainstem/midbrain nuclei (highest priority)
- **Tian**: 54 subcortical structures (medium priority)
- **Destrieux**: 148 cortical regions (lowest priority)

## Key Features
- **Hierarchical resolution**: Midbrain > Subcortical > Cortical
- **No overlaps**: Each voxel has single label
- **Comprehensive coverage**: 207 total brain regions
- **Clinical relevance**: Includes key psychiatric circuit nodes

## Atlas Versions
### 1. Hierarchical (No Overlaps)
- File: `final_atlas/no_overlaps/levtiades_hierarchical.nii.gz`
- Single label per voxel
- Recommended for most analyses

### 2. Multi-channel (With Overlaps)
- File: `final_atlas/with_overlaps/levtiades_multichannel.nii.gz`
- 3 channels for each atlas component
- For specialized overlap analyses

## Label Scheme
- **1-5**: Levinson brainstem nuclei
- **101-154**: Tian subcortical structures
- **201-348**: Destrieux cortical regions

## Key Brainstem Nuclei (Levinson)
1. **LC**: Locus Coeruleus - noradrenergic center
2. **NTS**: Nucleus Tractus Solitarius - autonomic integration
3. **VTA**: Ventral Tegmental Area - dopamine reward center
4. **PAG**: Periaqueductal Gray - pain/defense responses
5. **DRN**: Dorsal Raphe Nucleus - serotonin regulation

## Usage
```python
import nibabel as nib
atlas = nib.load('levtiades_atlas/final_atlas/no_overlaps/levtiades_hierarchical.nii.gz')
atlas_data = atlas.get_fdata()
```

## Citation
When using Levtiades atlas, please cite:
- Levinson et al. (2022) - Brainstem nuclei atlas
- Tian et al. (2020) - Melbourne Subcortex Atlas
- Destrieux et al. (2010) - Cortical parcellation

## Validation Results
- Total regions: 207
- Brain coverage: ~830 cm³
- Spatial resolution: 2×2×2 mm
- Quality: Production-ready
