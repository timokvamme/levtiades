# Claude Code Guidelines for Levtiades Atlas Project

## writing style

**use lowercase for everything**

do not use capital letters in documentation, console output, or file contents except:
- code blocks and inline code (preserve original casing)
- proper technical names (e.g., MNI, NIfTI, Python)
- file paths that must match actual casing

why? lowercase is easier to read, less formal, and matches the project's relaxed tone.

**examples:**
```markdown
# wrong - unnecessary capitals
The Levtiades Atlas combines Three atlases.
THIS IS IMPORTANT!

# right - lowercase throughout
the levtiades atlas combines three atlases.
this is important.
```

## file naming philosophy

**no suffixes on final files**

do not use suffixes like `_renumbered`, `_clean`, `_corrected`, `_final`, etc. on production files.

why? suffixes create confusion about which file is actually final. if you have `file_clean.nii.gz`, then someone creates `file_cleaner.nii.gz`, then `file_final.nii.gz`, then `file_final_v2.nii.gz` - the meaning is lost.

**correct approach:**
- final files should have clean names: `levtiades_with_overlaps.nii.gz`, `levtiades_atlas.csv`
- intermediate/temporary files can have suffixes: `temp_processing.nii.gz`
- when updating files, overwrite the original directly or use temp files that get renamed
- the ONLY exception: `levtiades_no_overlaps_hierarchical_final.nii.gz` gets "final" because it's the true final where no voxel is occupied by multiple regions

**example:**
```python
# wrong - creates proliferation of suffixes
output_file = "levtiades_final_renumbered.nii.gz"
output_file_v2 = "levtiades_final_renumbered_clean.nii.gz"

# right - keep final name clean
temp_file = "temp_processing.nii.gz"
process(input_file, temp_file)
temp_file.rename("levtiades_with_overlaps.nii.gz")  # overwrite final
```

## atlas processing rules

### excluded regions

**medial wall regions must be excluded**

the destrieux atlas includes "L Medial_wall" and "R Medial_wall" regions (original labels 42 and 117). these should NOT be included in the final atlas.

**why exclude medial wall:**
- not true cortical gray matter
- artifact of surface-based parcellation
- no functional or structural interpretation
- excluding maintains atlas anatomical validity

**implementation:**
- remove voxels during initial processing (before alignment)
- set medial wall voxels to 0 (background)
- renumber remaining destrieux regions continuously 1-148
- do not include in label files or CSV files
- document the exclusion and mapping

**processing flow:**
1. load original destrieux atlas (150 regions)
2. identify medial wall voxels (labels 42, 117)
3. set these voxels to 0
4. renumber remaining 148 regions to 1-148
5. save label mapping for documentation
6. proceed with alignment/combination

the final atlas should have continuous numbering 1-N without gaps for excluded regions.

**verification:**
- console should show: "removing medial wall label 42: [N] voxels"
- console should show: "removing medial wall label 117: [N] voxels"
- console should show: "destrieux regions after medial wall removal: 148 (renumbered 1-148)"
- final atlas should have exactly 207 regions (5+54+148)

### label numbering scheme

after excluding medial wall, final numbering is:
- **levinson**: 1-5 (5 brainstem nuclei)
- **tian**: 6-59 (54 subcortical regions, offset +5)
- **destrieux**: 60-207 (148 cortical regions, offset +59, medial wall excluded)
- **total**: 207 regions

labels must be continuous with no gaps.

**label file format issues and solutions:**

the tian labels file has a different format than destrieux:
- **destrieux format**: "1: L G_and_S_frontomargin" (index: name)
- **tian format**: "HIP-head-m1-rh" (name only, no index)

the `read_simple_label_file()` function handles both:
- detects format by checking for colons
- if has colons: parse as "index: name"
- if no colons: assign sequential indices starting from 1
- this allows proper reading of all label files

## project structure

### final output files

located in `levtiades_atlas/final_atlas/`:

**main files:**
- `levtiades_atlas.csv` - complete region information with coordinates
- `levtiades_labels.txt` - label reference file with MNI coordinates
- `levtiades_lookup_table.txt` - color lookup table for visualization

**atlas versions:**
- `with_overlaps/levtiades_with_overlaps.nii.gz` - flat atlas with all regions (overlaps allowed)
- `with_overlaps/levtiades_multichannel.nii.gz` - multi-channel format (each source atlas in separate channel)
- `no_overlaps/levtiades_no_overlaps_hierarchical_final.nii.gz` - hierarchical priority (brainstem > subcortical > cortical, no overlaps)

**individual aligned atlases:**
- `levinson_aligned.nii.gz`
- `tian_aligned.nii.gz`
- `destrieux_aligned.nii.gz`

note: only the hierarchical version has "_final" in the name because it's the true final where no voxel is occupied by multiple regions.

### csv file structure

the `levtiades_atlas.csv` file should contain:
- `index` - region label number (1-207)
- `region_name` - full region name
- `source_atlas` - levinson/tian/destrieux
- `hemisphere` - left/right/bilateral
- `anatomical_category` - detailed classification (brainstem, hippocampus, thalamus, cortical_gyrus, etc.)
- `r, g, b` - RGB color values for visualization
- `centroid_i, j, k` - voxel coordinates of region center
- `centroid_x, y, z` - MNI coordinates (mm)
- `voxel_count` - number of voxels in region

### label file format

the `levtiades_labels.txt` file includes MNI coordinates for each region:

format: `ID: Region_Name [Source_Atlas] x=XX.XX y=YY.YY z=ZZ.ZZ`

example:
```
1: Locus_Coeruleus_LC [Levinson] x=0.78 y=-39.17 z=-27.63
6: HIP-head-m1-rh [Tian] x=19.55 y=-11.84 z=-21.56
60: L G_and_S_frontomargin [Destrieux] x=-23.85 y=57.20 z=-8.66
```

## code style

- use lowercase for console output and print statements
- no emojis unless explicitly requested by user
- prefer simple, descriptive function names
- include docstrings for all functions
- use type hints where helpful
- all scripts should be integrated into main 1-2-3 pipeline
- do not create standalone helper scripts

## processing pipeline

the complete pipeline consists of three scripts that should be run in order:

### script 1: `1_setup_levtiades_project.py`
- downloads and prepares source atlases
- sets up directory structure

### script 2: `2_levtiades_to_mni2009c.py` (main atlas creation)

processing steps:
1. loads component atlases (levinson, tian, destrieux)
2. **filters out medial wall regions from destrieux** (BEFORE any spatial processing)
   - removes labels 42 and 117
   - sets voxels to background (0)
   - renumbers remaining 148 regions to 1-148
3. aligns all to MNI152NLin2009cAsym (2mm)
4. combines with hierarchical priority (levinson > tian > destrieux)
5. generates label files with continuous numbering and MNI coordinates
6. creates CSV with comprehensive region info
7. outputs visualization files for QC

key points:
- medial wall removal happens during initial processing, not post-processing
- all functionality is integrated (no separate helper scripts)
- CSV creation and coordinate calculation are built-in
- generates both overlap and hierarchical versions

### script 3: `3_enhanced_qc_validation.py`
- validates registration quality
- analyzes overlaps
- generates expert QC report

## common tasks

### updating atlas files

when making changes to the atlas:
1. modify the main processing script (`2_levtiades_to_mni2009c.py`)
2. run the script to regenerate all outputs
3. verify the output with QC checks (script 3)
4. update documentation if needed

do NOT create separate "fix" scripts that create new file versions with suffixes.

### adding new regions

if adding regions to the atlas:
1. update the source atlas files in `raw_atlases/`
2. modify the processing script to include new regions
3. update label offset calculations if needed
4. regenerate all outputs
5. update documentation

### excluding regions

if excluding regions (like medial wall):
1. filter during initial loading in processing script
2. ensure label numbering remains continuous
3. update all output files (NIfTI, txt, csv)
4. document the exclusion in this file

## testing and qc

quality control files are in `qc_validation/`:
- registration overlays
- overlap statistics
- expert review reports

always regenerate QC files after atlas modifications by running script 3.

## integrated functionality

all functionality is built into the main 1-2-3 pipeline scripts. do not create:
- standalone helper scripts
- fix scripts with output file suffixes
- temporary documentation files

everything should be integrated and documented in:
- main scripts (1-2-3)
- this file (CLAUDE.md)
- final reports (reports/ and qc_validation/)
