# Levtiades Atlas Analysis Report

## Overview
The Levtiades atlas combines three complementary brain atlases:
- **Levinson**: Brainstem/midbrain nuclei (5 regions)
- **Tian**: Subcortical structures (54 regions)
- **Destrieux**: Cortical parcellation (148 regions)

## Spatial Hierarchy
Priority order: Midbrain > Subcortical > Cortical
This reflects neuroanatomical organization from core to periphery.

## Overlap Analysis (Before Hierarchical Resolution)
- **levinson_tian**: 0 voxels
- **levinson_destrieux**: 0 voxels
- **tian_destrieux**: 315 voxels
- **all_three**: 0 voxels

## Hierarchical Resolution Impact
### Voxel Replacements
- Tian voxels replaced by Levinson: 0
- Destrieux voxels replaced by Tian: 315
- Destrieux voxels replaced by Levinson: 0

### Destrieux Regions Affected by Tian Priority
- Region 23: 137 voxels
- Region 32: 15 voxels
- Region 35: 12 voxels
- Region 98: 147 voxels
- Region 110: 4 voxels

## Final Atlas Composition
- **Levinson regions**: 1336 voxels (1.28%)
- **Tian regions**: 7984 voxels (7.65%)
- **Destrieux regions**: 95013 voxels (91.07%)
- **Total brain coverage**: 104333 voxels

## Scientific Rationale
The hierarchical resolution strategy reflects:
1. **Anatomical precision**: Smaller, well-defined structures take precedence
2. **Functional importance**: Core brainstem nuclei are preserved intact
3. **Clinical relevance**: Critical for understanding psychiatric/neurological conditions
