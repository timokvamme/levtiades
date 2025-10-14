# Levtiades Atlas Workflow

## Pipeline Overview

The Levtiades Atlas creation follows a three-step workflow:

```
Step 0: Download Atlases → Step 1: Setup Project → Step 2: Create Atlas
```

## Detailed Workflow

### Step 0: Download Source Atlases
**Location**: `downloaded_atlases/0_downloading_destriux.py`

**Purpose**: Download and prepare original atlas data
- Downloads Destrieux cortical atlas instructions
- Verifies Levinson-Bari atlas components
- Ensures Tian atlas availability

**Output**: Organized source atlases in `downloaded_atlases/`

### Step 1: Setup Levtiades Project
**Location**: `levtiades_atlas/1_setup_levtiades_project.py`

**Purpose**: Copy atlases and prepare project structure
- Copies source atlases from `downloaded_atlases/` to `raw_atlases/`
- Downloads Destrieux atlas via nilearn
- Creates directory structure for processing
- Verifies atlas properties and spatial compatibility

**Key Functions**:
- `setup_levtiades_project()`: Main setup routine
- `verify_atlas_properties()`: Spatial compatibility checks

**Output**:
- `raw_atlases/`: Local copies of source atlases
- Project directory structure
- `atlas_info.txt`: Comprehensive project documentation

### Step 2: Create Levtiades Atlas
**Location**: `levtiades_atlas/2_levtiades_to_mni2009c.py`

**Purpose**: Create final combined atlas in MNI2009c space
- Template-to-template registration using ANTs
- Hierarchical atlas combination (Levinson > Tian > Destrieux)
- Generate multiple output formats
- Create labels, lookup tables, and QC files

**Key Functions**:
- `load_and_combine_levinson()`: Combine brainstem components
- `align_all_to_target()`: Register all atlases to target space
- `create_hierarchical()`: Combine with priority hierarchy
- `create_label_files()`: Generate region labels and colors

**Configuration**: All parameters embedded as defaults:
```python
DEFAULT_CONFIG = {
    "target_space": "MNI152NLin2009cAsym",
    "target_res": 2,
    "levinson_dir": "../downloaded_atlases/Levinson-Bari...",
    # ... other paths
}
```

## Processing Details

### Registration Strategy
- **Levinson**: MNI152NLin2009bAsym → MNI152NLin2009cAsym
- **Tian**: MNI152NLin6Asym → MNI152NLin2009cAsym
- **Destrieux**: MNI152NLin2009aAsym → MNI152NLin2009cAsym

All using ANTs `antsRegistrationSyNQuick.sh` for robust template-to-template transforms.

### Hierarchical Combination
1. **Layer 3**: Destrieux cortical (base layer)
2. **Layer 2**: Tian subcortical (overwrites cortical where present)
3. **Layer 1**: Levinson brainstem (highest priority)

### Label Indexing
- **Levinson**: 1-5 (original indices)
- **Tian**: 101-154 (original + 100 offset)
- **Destrieux**: 201-348 (original + 200 offset)

## Output Structure

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

## Quality Control

The pipeline includes automatic QC:
- Overlap analysis between source atlases
- Individual atlas masks for verification
- Processing statistics and region counts
- Spatial alignment verification

## Error Handling

Common issues and solutions:
- **ANTs not found**: Ensure ANTs tools are on PATH
- **Template download fails**: Check internet connection and templateflow cache
- **Atlas files missing**: Verify downloaded_atlases structure
- **Memory issues**: Large atlases may require sufficient RAM (8GB+ recommended)

## Runtime Expectations

Typical processing times:
- **Step 1**: 1-2 minutes (download and setup)
- **Step 2**: 10-30 minutes (depending on ANTs registration)

Total: ~15-35 minutes for complete atlas creation.