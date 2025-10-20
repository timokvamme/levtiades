# levtiades atlas processing workflow

## overview

the levtiades atlas combines three neuroimaging atlases into a unified brain parcellation optimized for psychiatric circuit analysis. each component atlas undergoes specific processing to align to a common target space (mni152nlin2009casym at 2.0mm resolution).

## component atlases & processing

### 1. levinson-bari limbic brainstem atlas
- **purpose**: critical brainstem nuclei for psychiatric disorders
- **regions**: 5 nuclei (lc, nts, vta, pag, drn)
- **original space**: mni152nlin2009basym (0.5mm high resolution)
- **processing method**: same-space resampling via nilearn
- **final labels**: 1-5
- **why same-space**: templateflow template corruption required fallback to resampling approach

### 2. tian subcortical atlas (scale iv)
- **purpose**: fine-grained subcortical structures
- **regions**: 54 subcortical areas (striatum, thalamus, hippocampus, amygdala, globus pallidus)
- **original space**: mni152nlin2009casym (2mm)
- **processing method**: same-space resampling via nilearn
- **label transformation**: original 1-54 → final 6-59 (+5 offset)
- **registration quality**: smooth anatomical transformations verified

### 3. destrieux cortical atlas
- **purpose**: comprehensive cortical parcellation
- **regions**: 148 sulco-gyral areas (74 per hemisphere, excluding medial wall)
- **original regions**: 150 (includes 2 medial wall regions that are excluded)
- **medial wall exclusion**: labels 42 (l medial_wall) and 117 (r medial_wall) removed before processing
- **original space**: mni152nlin2009aasym (2mm) via nilearn
- **processing method**: same-space resampling via nilearn (after medial wall removal)
- **label transformation**:
  - step 1: remove medial wall voxels (labels 42, 117)
  - step 2: renumber remaining labels continuously (1-148)
  - step 3: apply offset → final 60-207 (+59 offset)
- **coverage**: complete cortical gray matter (medial wall excluded)

## target space standardization

all atlases are aligned to:
- **template**: mni152nlin2009casym
- **resolution**: 2.0mm isotropic voxels
- **coordinate system**: ras+ orientation
- **interpolation**: nearest neighbor (preserves integer labels)

## hierarchical combination strategy

### priority order
1. **levinson** (highest priority) - brainstem nuclei
2. **tian** (medium priority) - subcortical structures
3. **destrieux** (lowest priority) - cortical areas

### overlap resolution
- higher priority atlas overwrites lower priority in overlapping voxels
- ensures psychiatric circuit nuclei (brainstem) are preserved
- maintains anatomical hierarchy (deep → superficial structures)

## output files

### individual aligned atlases
located in `final_atlas/aligned/` for mricrogl visualization:
- `levinson_aligned.nii.gz` - brainstem nuclei in target space
- `tian_aligned.nii.gz` - subcortical regions in target space
- `destrieux_aligned.nii.gz` - cortical areas in target space

### combined atlases
located in `final_atlas/`:
- `with_overlaps/levtiades_final.nii.gz` - **main output atlas** with all 207 regions
- `with_overlaps/levtiades_multichannel.nii.gz` - multi-channel atlas format
- `no_overlaps/levtiades_hierarchical.nii.gz` - hierarchical atlas (priority-based, no overlaps)

### label files
located in `final_atlas/`:
- `levtiades_labels.txt` - complete region labels and names
- `levtiades_lookup_table.txt` - label lookup table for visualization
- `levtiades_labels.csv` - detailed region information with coordinates

## quality control

### registration validation
- visual inspection of template-to-template alignments
- anatomical plausibility checking
- centroid displacement analysis (<2mm acceptable)

### overlap analysis
- statistical overlap quantification
- boundary region identification
- hierarchical priority verification

### expert review
- qc images in `qc_validation/registration_qc/`
- overlap visualizations in `qc_validation/qc_overlays/`
- comprehensive report in `qc_validation/expert_qc_report.md`

## psychiatric circuit applications

### target disorders
- **depression**: lc-drn-vta connectivity analysis
- **anxiety**: pag-amygdala-prefrontal circuit mapping
- **ptsd**: brainstem arousal system investigation
- **addiction**: vta-striatal reward pathway studies

### research advantages
- unified coordinate system for cross-study comparisons
- hierarchical labeling preserves critical small nuclei
- comprehensive coverage from brainstem to cortex
- optimized for psychiatric neurocircuit research

## technical implementation

the processing pipeline is implemented in:
- `2_levtiades_to_mni2009c.py` - main atlas creation script
- uses ants for robust template-to-template registration
- incorporates nilearn for same-space resampling fallback
- implements comprehensive error handling and validation