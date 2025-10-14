# Levtiades Atlas Project

**A comprehensive brain atlas combining psychiatric circuit-critical brainstem nuclei with detailed subcortical and cortical parcellations.**

## Overview

The Levtiades Atlas is a 207-region brain parcellation designed specifically for psychiatric circuit analysis and neuroscience research. It combines three complementary atlases:

- **5 Brainstem Nuclei** (Levinson-Bari): Critical psychiatric circuit nodes
- **54 Subcortical Regions** (Tian Melbourne S4): Fine-grained limbic structures
- **148 Cortical Areas** (Destrieux): Complete sulco-gyral parcellation

## Quick Start

### Prerequisites
- Python 3.8+ with nibabel, nilearn, numpy, pandas, templateflow, scipy
- ANTs registration tools (`antsRegistrationSyNQuick.sh`, `antsApplyTransforms`)

### Running the Pipeline

1. **Download atlases**:
   ```bash
   cd downloaded_atlases
   python 0_downloading_destriux.py
   ```

2. **Setup project** (copies atlases from downloaded_atlases/):
   ```bash
   cd levtiades_atlas
   python 1_setup_levtiades_project.py
   ```

3. **Create final atlas**:
   ```bash
   python 2_levtiades_to_mni2009c.py
   ```

## Repository Structure

```
levtiades/
├── downloaded_atlases/           # Original atlas data
│   ├── 0_downloading_destriux.py
│   ├── Levinson-Bari Limbic Brainstem Atlas (Levinson 2022)/
│   └── Tian2020MSA_v1.4/
├── levtiades_atlas/             # Main processing folder
│   ├── 1_setup_levtiades_project.py
│   ├── 2_levtiades_to_mni2009c.py
│   ├── final/                   # Output atlases
│   ├── raw_atlases/            # Copied source atlases
│   ├── reports/                # Analysis reports
│   └── qc/                     # Quality control files
├── mds/                        # Documentation
│   ├── README.md               # This file
│   └── old/                    # Original documentation
├── tiandes_atlas/              # Predecessor atlas (foundation)
└── legacy_scripts/             # Historical development scripts
```

## Atlas Components

### Levinson-Bari Brainstem Atlas (Regions 1-5)
Critical psychiatric circuit nodes:
- **LC (1)**: Locus Coeruleus (noradrenergic system)
- **NTS (2)**: Nucleus Tractus Solitarius (autonomic integration)
- **VTA (3)**: Ventral Tegmental Area (dopaminergic reward)
- **PAG (4)**: Periaqueductal Gray (pain/defense)
- **DRN (5)**: Dorsal Raphe Nucleus (serotonergic mood)

### Tian Subcortical Atlas S4 (Regions 101-154)
54 fine-grained subcortical structures including detailed parcellations of:
- Striatum, Thalamus, Hippocampus, Amygdala, Globus Pallidus

### Destrieux Cortical Atlas (Regions 201-348)
148 sulco-gyral cortical regions providing complete cortical coverage.

## Target Applications

### Psychiatric Circuit Analysis
- **Depression**: LC-DRN-VTA connectivity mapping
- **Anxiety**: PAG-amygdala-prefrontal circuits
- **PTSD**: Brainstem arousal system analysis
- **Addiction**: VTA-striatal reward pathways

### Technical Specifications
- **Target Space**: MNI152NLin2009cAsym
- **Resolution**: 2×2×2mm isotropic
- **Registration**: ANTs template-to-template (not simple resampling)
- **Hierarchy**: Brainstem > Subcortical > Cortical priority
- **Total Regions**: 207 (5 + 54 + 148)

## Output Files

After running the pipeline, key outputs include:

- `final/no_overlaps/levtiades_hierarchical.nii.gz` - Main atlas file
- `final/levtiades_labels.txt` - Region names and source attribution
- `final/levtiades_lookup_table.txt` - MRIcroGL color table
- `reports/levtiades_analysis_report.md` - Processing summary
- `qc/` - Quality control overlays and masks

## Citation

When using the Levtiades Atlas, please cite all source atlases:

1. **Levinson, A.J., et al. (2022)**. Limbic Brainstem Atlas for Depression Research
2. **Tian, Y., et al. (2020)**. Melbourne Subcortical Atlas. *Nature Neuroscience*, 23(11), 1421-1432.
3. **Destrieux, C., et al. (2010)**. Cortical Parcellation. *NeuroImage*, 53(1), 1-15.

## Development Notes

This repository has been streamlined from a complex development history. Original documentation and development scripts are preserved in `mds/old/` and `legacy_scripts/` respectively.

The current pipeline represents the production-ready workflow distilled from extensive validation and iteration documented in the archived materials.