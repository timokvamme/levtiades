#!/usr/bin/env python3
"""
Create Individual ROIs from Original Source Atlases

This script extracts individual ROI binary masks directly from the original source
atlases (Levinson, Tian, Destrieux) before they were combined into the final
Levtiades atlas.

Key Difference from individual_rois/:
- individual_rois/ contains ROIs from the FINAL combined Levtiades atlas
  (sequential 1-207 indexing after reindexing and hemisphere correction)
- individual_rois_from_original_atlases/ contains ROIs extracted directly from
  each original source atlas with their ORIGINAL indexing schemes

Source Atlases:
1. Levinson-Bari Brainstem Atlas (5 regions, indices 1-5)
2. Tian Melbourne Subcortical Atlas Scale IV (54 regions, indices 1-54)
3. Destrieux Cortical Parcellation (148 regions, various original indices)

Author: Levtiades Atlas Project
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import csv


def get_levinson_labels():
    """Return Levinson brainstem region labels"""
    return {
        1: 'Locus_Coeruleus_LC',
        2: 'Nucleus_Tractus_Solitarius_NTS',
        3: 'Ventral_Tegmental_Area_VTA',
        4: 'Periaqueductal_Gray_PAG',
        5: 'Dorsal_Raphe_Nucleus_DRN'
    }


def get_tian_s4_labels():
    """Return Tian Scale IV subcortical labels (original ordering)"""
    # Original Tian S4 ordering: 1-27 RH, 28-54 LH
    return {
        1: 'HIP-head-m1-rh', 2: 'HIP-head-m2-rh', 3: 'THA-VAip-rh', 4: 'THA-VAia-rh',
        5: 'HIP-head-l-rh', 6: 'HIP-body-rh', 7: 'HIP-tail-rh', 8: 'THA-VPm-rh',
        9: 'THA-VPl-rh', 10: 'THA-VAs-rh', 11: 'THA-DAm-rh', 12: 'THA-DAl-rh',
        13: 'PUT-VA-rh', 14: 'PUT-DA-rh', 15: 'PUT-VP-rh', 16: 'PUT-DP-rh',
        17: 'CAU-VA-rh', 18: 'CAU-DA-rh', 19: 'CAU-body-rh', 20: 'CAU-tail-rh',
        21: 'lAMY-rh', 22: 'mAMY-rh', 23: 'THA-DP-rh', 24: 'NAc-shell-rh',
        25: 'NAc-core-rh', 26: 'pGP-rh', 27: 'aGP-rh',
        28: 'HIP-head-m1-lh', 29: 'HIP-head-m2-lh', 30: 'THA-VAip-lh', 31: 'THA-VAia-lh',
        32: 'HIP-head-l-lh', 33: 'HIP-body-lh', 34: 'HIP-tail-lh', 35: 'THA-VPm-lh',
        36: 'THA-VPl-lh', 37: 'THA-VAs-lh', 38: 'THA-DAm-lh', 39: 'THA-DAl-lh',
        40: 'PUT-VA-lh', 41: 'PUT-DA-lh', 42: 'PUT-VP-lh', 43: 'PUT-DP-lh',
        44: 'CAU-VA-lh', 45: 'CAU-DA-lh', 46: 'CAU-body-lh', 47: 'CAU-tail-lh',
        48: 'lAMY-lh', 49: 'mAMY-lh', 50: 'THA-DP-lh', 51: 'NAc-shell-lh',
        52: 'NAc-core-lh', 53: 'pGP-lh', 54: 'aGP-lh'
    }


def get_destrieux_labels():
    """Return Destrieux cortical labels (FreeSurfer convention)"""
    # Labels from Destrieux parcellation (excluding medial wall regions)
    labels = {
        1: 'L_G_and_S_frontomargin', 2: 'L_G_and_S_occipital_inf', 3: 'L_G_and_S_paracentral',
        4: 'L_G_and_S_subcentral', 5: 'L_G_and_S_transv_frontopol', 6: 'L_G_and_S_cingul-Ant',
        7: 'L_G_and_S_cingul-Mid-Ant', 8: 'L_G_and_S_cingul-Mid-Post', 9: 'L_G_cingul-Post-dorsal',
        10: 'L_G_cingul-Post-ventral', 11: 'L_G_cuneus', 12: 'L_G_front_inf-Opercular',
        13: 'L_G_front_inf-Orbital', 14: 'L_G_front_inf-Triangul', 15: 'L_G_front_middle',
        16: 'L_G_front_sup', 17: 'L_G_Ins_lg_and_S_cent_ins', 18: 'L_G_insular_short',
        19: 'L_G_occipital_middle', 20: 'L_G_occipital_sup', 21: 'L_G_oc-temp_lat-fusifor',
        22: 'L_G_oc-temp_med-Lingual', 23: 'L_G_oc-temp_med-Parahip', 24: 'L_G_orbital',
        25: 'L_G_pariet_inf-Angular', 26: 'L_G_pariet_inf-Supramar', 27: 'L_G_parietal_sup',
        28: 'L_G_postcentral', 29: 'L_G_precentral', 30: 'L_G_precuneus', 31: 'L_G_rectus',
        32: 'L_G_subcallosal', 33: 'L_G_temp_sup-G_T_transv', 34: 'L_G_temp_sup-Lateral',
        35: 'L_G_temp_sup-Plan_polar', 36: 'L_G_temp_sup-Plan_tempo', 37: 'L_G_temporal_inf',
        38: 'L_G_temporal_middle', 39: 'L_Lat_Fis-ant-Horizont', 40: 'L_Lat_Fis-ant-Vertical',
        41: 'L_Lat_Fis-post', 43: 'L_Pole_occipital', 44: 'L_Pole_temporal',
        45: 'L_S_calcarine', 46: 'L_S_central', 47: 'L_S_cingul-Marginalis',
        48: 'L_S_circular_insula_ant', 49: 'L_S_circular_insula_inf', 50: 'L_S_circular_insula_sup',
        51: 'L_S_collat_transv_ant', 52: 'L_S_collat_transv_post', 53: 'L_S_front_inf',
        54: 'L_S_front_middle', 55: 'L_S_front_sup', 56: 'L_S_interm_prim-Jensen',
        57: 'L_S_intrapariet_and_P_trans', 58: 'L_S_oc_middle_and_Lunatus', 59: 'L_S_oc_sup_and_transversal',
        60: 'L_S_occipital_ant', 61: 'L_S_oc-temp_lat', 62: 'L_S_oc-temp_med_and_Lingual',
        63: 'L_S_orbital_lateral', 64: 'L_S_orbital_med-olfact', 65: 'L_S_orbital-H_Shaped',
        66: 'L_S_parieto_occipital', 67: 'L_S_pericallosal', 68: 'L_S_postcentral',
        69: 'L_S_precentral-inf-part', 70: 'L_S_precentral-sup-part', 71: 'L_S_suborbital',
        72: 'L_S_subparietal', 73: 'L_S_temporal_inf', 74: 'L_S_temporal_sup',
        75: 'L_S_temporal_transverse',
        # Right hemisphere (indices 76-150)
        76: 'R_G_and_S_frontomargin', 77: 'R_G_and_S_occipital_inf', 78: 'R_G_and_S_paracentral',
        79: 'R_G_and_S_subcentral', 80: 'R_G_and_S_transv_frontopol', 81: 'R_G_and_S_cingul-Ant',
        82: 'R_G_and_S_cingul-Mid-Ant', 83: 'R_G_and_S_cingul-Mid-Post', 84: 'R_G_cingul-Post-dorsal',
        85: 'R_G_cingul-Post-ventral', 86: 'R_G_cuneus', 87: 'R_G_front_inf-Opercular',
        88: 'R_G_front_inf-Orbital', 89: 'R_G_front_inf-Triangul', 90: 'R_G_front_middle',
        91: 'R_G_front_sup', 92: 'R_G_Ins_lg_and_S_cent_ins', 93: 'R_G_insular_short',
        94: 'R_G_occipital_middle', 95: 'R_G_occipital_sup', 96: 'R_G_oc-temp_lat-fusifor',
        97: 'R_G_oc-temp_med-Lingual', 98: 'R_G_oc-temp_med-Parahip', 99: 'R_G_orbital',
        100: 'R_G_pariet_inf-Angular', 101: 'R_G_pariet_inf-Supramar', 102: 'R_G_parietal_sup',
        103: 'R_G_postcentral', 104: 'R_G_precentral', 105: 'R_G_precuneus', 106: 'R_G_rectus',
        107: 'R_G_subcallosal', 108: 'R_G_temp_sup-G_T_transv', 109: 'R_G_temp_sup-Lateral',
        110: 'R_G_temp_sup-Plan_polar', 111: 'R_G_temp_sup-Plan_tempo', 112: 'R_G_temporal_inf',
        113: 'R_G_temporal_middle', 114: 'R_Lat_Fis-ant-Horizont', 115: 'R_Lat_Fis-ant-Vertical',
        116: 'R_Lat_Fis-post', 118: 'R_Pole_occipital', 119: 'R_Pole_temporal',
        120: 'R_S_calcarine', 121: 'R_S_central', 122: 'R_S_cingul-Marginalis',
        123: 'R_S_circular_insula_ant', 124: 'R_S_circular_insula_inf', 125: 'R_S_circular_insula_sup',
        126: 'R_S_collat_transv_ant', 127: 'R_S_collat_transv_post', 128: 'R_S_front_inf',
        129: 'R_S_front_middle', 130: 'R_S_front_sup', 131: 'R_S_interm_prim-Jensen',
        132: 'R_S_intrapariet_and_P_trans', 133: 'R_S_oc_middle_and_Lunatus', 134: 'R_S_oc_sup_and_transversal',
        135: 'R_S_occipital_ant', 136: 'R_S_oc-temp_lat', 137: 'R_S_oc-temp_med_and_Lingual',
        138: 'R_S_orbital_lateral', 139: 'R_S_orbital_med-olfact', 140: 'R_S_orbital-H_Shaped',
        141: 'R_S_parieto_occipital', 142: 'R_S_pericallosal', 143: 'R_S_postcentral',
        144: 'R_S_precentral-inf-part', 145: 'R_S_precentral-sup-part', 146: 'R_S_suborbital',
        147: 'R_S_subparietal', 148: 'R_S_temporal_inf', 149: 'R_S_temporal_sup',
        150: 'R_S_temporal_transverse'
    }
    return labels


def extract_rois_from_atlas(atlas_path, output_dir, source_name, labels_dict):
    """
    Extract individual ROI masks from a source atlas.

    Args:
        atlas_path: Path to the aligned atlas NIfTI file
        output_dir: Output directory for ROI files
        source_name: Name of the source atlas (levinson, tian, destrieux)
        labels_dict: Dictionary mapping indices to region names

    Returns:
        List of tuples: (original_index, filename, voxel_count, region_name)
    """
    print(f"\n[*] Processing {source_name.upper()} atlas...")

    # Load atlas
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)

    # Get unique labels (excluding 0/background)
    unique_labels = np.unique(atlas_data[atlas_data > 0])
    print(f"   Found {len(unique_labels)} unique regions")

    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    extracted_rois = []

    for label in unique_labels:
        # Create binary mask
        roi_mask = (atlas_data == label).astype(np.uint8)
        voxel_count = np.sum(roi_mask)

        # Get region name
        region_name = labels_dict.get(int(label), f'{source_name}_{int(label):03d}')

        # Create filename
        filename = f"{source_name}_{int(label):03d}_{region_name}.nii.gz"
        output_path = output_dir / filename

        # Save ROI
        roi_img = nib.Nifti1Image(roi_mask, atlas_img.affine, atlas_img.header)
        nib.save(roi_img, output_path)

        extracted_rois.append((int(label), filename, voxel_count, region_name))

    print(f"   [OK] Extracted {len(extracted_rois)} ROIs to {output_dir}")
    return extracted_rois


def create_mapping_csv(levinson_rois, tian_rois, destrieux_rois, output_path):
    """Create a CSV mapping original atlas indices to Levtiades indices"""

    print("\n[*] Creating mapping reference...")

    # Build the mapping based on the known Levtiades structure:
    # Levtiades 1-5: Levinson 1-5 (unchanged)
    # Levtiades 6-32: Tian LEFT (original 28-54)
    # Levtiades 33-59: Tian RIGHT (original 1-27)
    # Levtiades 60-207: Destrieux (reindexed)

    rows = []

    # Levinson mapping (1:1)
    for orig_idx, filename, voxels, name in levinson_rois:
        rows.append({
            'levtiades_index': orig_idx,
            'source_atlas': 'Levinson',
            'original_index': orig_idx,
            'region_name': name,
            'voxel_count': voxels,
            'original_roi_file': filename
        })

    # Tian mapping (LEFT hemisphere first in Levtiades)
    # Levtiades 6-32 = Tian 28-54 (Left)
    # Levtiades 33-59 = Tian 1-27 (Right)
    tian_left = [(idx, fn, v, n) for idx, fn, v, n in tian_rois if idx >= 28]
    tian_right = [(idx, fn, v, n) for idx, fn, v, n in tian_rois if idx <= 27]

    lev_idx = 6
    for orig_idx, filename, voxels, name in sorted(tian_left, key=lambda x: x[0]):
        rows.append({
            'levtiades_index': lev_idx,
            'source_atlas': 'Tian',
            'original_index': orig_idx,
            'region_name': name,
            'voxel_count': voxels,
            'original_roi_file': filename
        })
        lev_idx += 1

    for orig_idx, filename, voxels, name in sorted(tian_right, key=lambda x: x[0]):
        rows.append({
            'levtiades_index': lev_idx,
            'source_atlas': 'Tian',
            'original_index': orig_idx,
            'region_name': name,
            'voxel_count': voxels,
            'original_roi_file': filename
        })
        lev_idx += 1

    # Destrieux mapping (sequential)
    lev_idx = 60
    for orig_idx, filename, voxels, name in sorted(destrieux_rois, key=lambda x: x[0]):
        rows.append({
            'levtiades_index': lev_idx,
            'source_atlas': 'Destrieux',
            'original_index': orig_idx,
            'region_name': name,
            'voxel_count': voxels,
            'original_roi_file': filename
        })
        lev_idx += 1

    # Sort by Levtiades index
    rows.sort(key=lambda x: x['levtiades_index'])

    # Write CSV
    with open(output_path, 'w', newline='') as f:
        fieldnames = ['levtiades_index', 'source_atlas', 'original_index',
                      'region_name', 'voxel_count', 'original_roi_file']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"   [OK] Mapping saved to {output_path}")
    return rows


def create_readme(output_base, levinson_count, tian_count, destrieux_count):
    """Create README documentation"""

    readme_path = output_base / "README.md"
    content = f"""# Individual ROIs from Original Source Atlases

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
├── levinson/           # {levinson_count} brainstem ROIs (indices 1-5)
├── tian/               # {tian_count} subcortical ROIs (indices 1-54)
├── destrieux/          # {destrieux_count} cortical ROIs (original indices)
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
"""

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"   [OK] README created at {readme_path}")


def main():
    """Main extraction routine"""

    print("=" * 60)
    print("EXTRACTING INDIVIDUAL ROIs FROM ORIGINAL SOURCE ATLASES")
    print("=" * 60)

    # Paths
    base_dir = Path(__file__).parent
    aligned_dir = base_dir / "aligned_atlases"
    output_base = base_dir / "individual_rois_from_original_atlases"

    # Source atlas paths
    levinson_path = aligned_dir / "levinson_aligned.nii.gz"
    tian_path = aligned_dir / "tian_aligned.nii.gz"
    destrieux_path = aligned_dir / "destrieux_aligned.nii.gz"

    # Verify source files exist
    print("\n[*] Verifying source atlases...")
    missing = []
    for name, path in [("Levinson", levinson_path), ("Tian", tian_path), ("Destrieux", destrieux_path)]:
        if path.exists():
            print(f"   [OK] {name}: {path}")
        else:
            print(f"   [ERROR] {name}: NOT FOUND at {path}")
            missing.append(name)

    if missing:
        print(f"\n[ERROR] Missing source atlases: {missing}")
        print("   Please ensure aligned atlases exist in: aligned_atlases/")
        return

    # Create output directories
    print("\n[*] Creating output directories...")
    output_base.mkdir(exist_ok=True)

    # Extract ROIs from each atlas
    levinson_rois = extract_rois_from_atlas(
        levinson_path,
        output_base / "levinson",
        "levinson",
        get_levinson_labels()
    )

    tian_rois = extract_rois_from_atlas(
        tian_path,
        output_base / "tian",
        "tian",
        get_tian_s4_labels()
    )

    destrieux_rois = extract_rois_from_atlas(
        destrieux_path,
        output_base / "destrieux",
        "destrieux",
        get_destrieux_labels()
    )

    # Create mapping CSV
    mapping = create_mapping_csv(
        levinson_rois, tian_rois, destrieux_rois,
        output_base / "original_to_levtiades_mapping.csv"
    )

    # Create README
    create_readme(output_base, len(levinson_rois), len(tian_rois), len(destrieux_rois))

    # Summary
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"   Levinson brainstem:    {len(levinson_rois):3d} ROIs")
    print(f"   Tian subcortical:      {len(tian_rois):3d} ROIs")
    print(f"   Destrieux cortical:    {len(destrieux_rois):3d} ROIs")
    print(f"   ------------------------------")
    print(f"   TOTAL:                 {len(levinson_rois) + len(tian_rois) + len(destrieux_rois):3d} ROIs")
    print(f"\nOutput: {output_base}")
    print(f"\n[OK] All ROIs extracted with original atlas indexing!")


if __name__ == "__main__":
    main()
