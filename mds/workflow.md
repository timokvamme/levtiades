# levtiades atlas workflow

## pipeline overview

the levtiades atlas creation follows a three-step workflow:

```
Step 0: Download Atlases → Step 1: Setup Project → Step 2: Create Atlas
```

## detailed workflow

### step 0: download source atlases
**location**: `downloaded_atlases/0_downloading_destriux.py`

**purpose**: download and prepare original atlas data
- downloads destrieux cortical atlas instructions
- verifies levinson-bari atlas components
- ensures tian atlas availability

**output**: organized source atlases in `downloaded_atlases/`

### step 1: setup levtiades project
**location**: `levtiades_atlas/1_setup_levtiades_project.py`

**purpose**: copy atlases and prepare project structure
- copies source atlases from `downloaded_atlases/` to `raw_atlases/`
- downloads destrieux atlas via nilearn
- creates directory structure for processing
- verifies atlas properties and spatial compatibility

**key functions**:
- `setup_levtiades_project()`: main setup routine
- `verify_atlas_properties()`: spatial compatibility checks

**output**:
- `raw_atlases/`: local copies of source atlases
- project directory structure
- `atlas_info.txt`: comprehensive project documentation

### step 2: create levtiades atlas
**location**: `levtiades_atlas/2_levtiades_to_mni2009c.py`

**purpose**: create final combined atlas in mni2009c space
- template-to-template registration using ants
- hierarchical atlas combination (levinson > tian > destrieux)
- generate multiple output formats
- create labels, lookup tables, and qc files

**key functions**:
- `load_and_combine_levinson()`: combine brainstem components
- `align_all_to_target()`: register all atlases to target space
- `create_hierarchical()`: combine with priority hierarchy
- `create_label_files()`: generate region labels and colors

**configuration**: all parameters embedded as defaults:
```python
DEFAULT_CONFIG = {
    "target_space": "MNI152NLin2009cAsym",
    "target_res": 2,
    "levinson_dir": "../downloaded_atlases/Levinson-Bari...",
    # ... other paths
}
```

## processing details

### registration strategy
- **levinson**: mni152nlin2009basym → mni152nlin2009casym
- **tian**: mni152nlin6asym → mni152nlin2009casym
- **destrieux**: mni152nlin2009aasym → mni152nlin2009casym

all using ants `antsRegistrationSyNQuick.sh` for robust template-to-template transforms.

### hierarchical combination
1. **layer 3**: destrieux cortical (base layer)
2. **layer 2**: tian subcortical (overwrites cortical where present)
3. **layer 1**: levinson brainstem (highest priority)

### label indexing
- **levinson**: 1-5 (original indices)
- **tian**: 101-154 (original + 100 offset)
- **destrieux**: 201-348 (original + 200 offset)

## output structure

```
levtiades_atlas/
├── final/
│   ├── no_overlaps/
│   │   └── levtiades_hierarchical.nii.gz     # Main atlas
│   ├── with_overlaps/
│   │   ├── levtiades_multichannel.nii.gz     # 4D with overlaps
│   │   └── levtiades_flat_with_overlaps.nii.gz
│   ├── levtiades_labels.txt                  # Region names
│   └── levtiades_lookup_table.txt            # Colors
├── reports/
│   └── levtiades_analysis_report.md          # Processing summary
├── qc/
│   ├── overlap_visualization.nii.gz          # QC overlays
│   └── *_mask.nii.gz                         # Individual masks
└── work/                                     # Intermediate files
```

## quality control

the pipeline includes automatic qc:
- overlap analysis between source atlases
- individual atlas masks for verification
- processing statistics and region counts
- spatial alignment verification

## error handling

common issues and solutions:
- **ants not found**: ensure ants tools are on path
- **template download fails**: check internet connection and templateflow cache
- **atlas files missing**: verify downloaded_atlases structure
- **memory issues**: large atlases may require sufficient ram (8gb+ recommended)

## runtime expectations

typical processing times:
- **step 1**: 1-2 minutes (download and setup)
- **step 2**: 10-30 minutes (depending on ants registration)

total: ~15-35 minutes for complete atlas creation.