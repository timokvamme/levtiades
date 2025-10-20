# levtiades atlas project

**a comprehensive brain atlas combining psychiatric circuit-critical brainstem nuclei with detailed subcortical and cortical parcellations.**

## overview

the levtiades atlas is a 207-region brain parcellation designed specifically for psychiatric circuit analysis and neuroscience research. it combines three complementary atlases:

- **5 brainstem nuclei** (levinson-bari): critical psychiatric circuit nodes
- **54 subcortical regions** (tian melbourne s4): fine-grained limbic structures
- **148 cortical areas** (destrieux): complete sulco-gyral parcellation

## quick start

### prerequisites
- python 3.8+ with nibabel, nilearn, numpy, pandas, templateflow, scipy
- ants registration tools (`antsRegistrationSyNQuick.sh`, `antsApplyTransforms`)

### running the pipeline

1. **download atlases**:
   ```bash
   cd downloaded_atlases
   python 0_downloading_destriux.py
   ```

2. **setup project** (copies atlases from downloaded_atlases/):
   ```bash
   cd levtiades_atlas
   python 1_setup_levtiades_project.py
   ```

3. **create final atlas**:
   ```bash
   python 2_levtiades_to_mni2009c.py
   ```

## repository structure

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

## atlas components

### levinson-bari brainstem atlas (regions 1-5)
critical psychiatric circuit nodes:
- **lc (1)**: locus coeruleus (noradrenergic system)
- **nts (2)**: nucleus tractus solitarius (autonomic integration)
- **vta (3)**: ventral tegmental area (dopaminergic reward)
- **pag (4)**: periaqueductal gray (pain/defense)
- **drn (5)**: dorsal raphe nucleus (serotonergic mood)

### tian subcortical atlas s4 (regions 6-59)
54 fine-grained subcortical structures including detailed parcellations of:
- striatum, thalamus, hippocampus, amygdala, globus pallidus

### destrieux cortical atlas (regions 60-207)
148 sulco-gyral cortical regions providing complete cortical coverage.
- **note**: medial wall regions (original labels 42, 117) excluded before processing
- see `levtiades_atlas/medial_wall_removal_documentation.md` for details

## target applications

### psychiatric circuit analysis
- **depression**: lc-drn-vta connectivity mapping
- **anxiety**: pag-amygdala-prefrontal circuits
- **ptsd**: brainstem arousal system analysis
- **addiction**: vta-striatal reward pathways

### technical specifications
- **target space**: mni152nlin2009casym
- **resolution**: 2×2×2mm isotropic
- **registration**: ants template-to-template (not simple resampling)
- **hierarchy**: brainstem > subcortical > cortical priority
- **total regions**: 207 (5 + 54 + 148)

## output files

after running the pipeline, key outputs include:

- `final/no_overlaps/levtiades_hierarchical.nii.gz` - main atlas file
- `final/levtiades_labels.txt` - region names and source attribution
- `final/levtiades_lookup_table.txt` - mricrogl color table
- `reports/levtiades_analysis_report.md` - processing summary
- `qc/` - quality control overlays and masks

## citation

when using the levtiades atlas, please cite all source atlases:

1. **levinson, a.j., et al. (2022)**. limbic brainstem atlas for depression research
2. **tian, y., et al. (2020)**. melbourne subcortical atlas. *nature neuroscience*, 23(11), 1421-1432.
3. **destrieux, c., et al. (2010)**. cortical parcellation. *neuroimage*, 53(1), 1-15.

## development notes

this repository has been streamlined from a complex development history. original documentation and development scripts are preserved in `mds/old/` and `legacy_scripts/` respectively.

the current pipeline represents the production-ready workflow distilled from extensive validation and iteration documented in the archived materials.