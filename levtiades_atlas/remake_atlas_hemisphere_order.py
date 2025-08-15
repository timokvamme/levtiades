#!/usr/bin/env python3
"""
Remake Levtiades Atlas with correct hemisphere ordering:
1. Levinson (1-5)
2. Tian Left hemisphere first (6-32)
3. Tian Right hemisphere (33-59)
4. Destrieux Left hemisphere first (60-133)
5. Destrieux Right hemisphere (134-207)
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import json
import pandas as pd
from scipy import ndimage

def create_hemisphere_ordered_reindexing_map():
    """Create mapping with correct hemisphere ordering"""
    
    print("📊 Creating Hemisphere-Ordered Reindexing Map...")
    
    # Load current atlas to understand existing structure
    atlas_path = Path("final_atlas/no_overlaps/levtiades_hierarchical_fixed.nii.gz")
    if not atlas_path.exists():
        atlas_path = Path("final_atlas/no_overlaps/levtiades_hierarchical.nii.gz")
    
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # Get all unique labels
    old_labels = sorted(np.unique(atlas_data[atlas_data > 0]))
    print(f"   Found {len(old_labels)} unique labels in current atlas")
    
    # Create new mapping with hemisphere ordering
    reindex_map = {}
    new_index = 1
    
    # 1. Levinson regions (1-5) stay the same
    levinson_labels = [l for l in old_labels if l < 100]
    for old_label in sorted(levinson_labels):
        reindex_map[old_label] = new_index
        print(f"   Levinson {old_label} -> {new_index}")
        new_index += 1
    
    # 2. Tian regions - LEFT hemisphere first (lh suffix)
    # Tian uses 101-154, where odd numbers are right, even are left
    tian_labels = [l for l in old_labels if 100 <= l < 200]
    
    # Left hemisphere Tian (even numbers: 102, 104, 106... -> 128, 130...154)
    tian_left = [l for l in tian_labels if l % 2 == 0]
    for old_label in sorted(tian_left):
        reindex_map[old_label] = new_index
        print(f"   Tian-LH {old_label} -> {new_index}")
        new_index += 1
    
    # Right hemisphere Tian (odd numbers: 101, 103, 105... -> 127, 129...153)
    tian_right = [l for l in tian_labels if l % 2 == 1]
    for old_label in sorted(tian_right):
        reindex_map[old_label] = new_index
        print(f"   Tian-RH {old_label} -> {new_index}")
        new_index += 1
    
    # 3. Destrieux regions - LEFT hemisphere first
    destrieux_labels = [l for l in old_labels if l >= 200]
    
    # Destrieux left hemisphere (201-275, approximately first half)
    # Based on the label file, left hemisphere regions are indexed 1-75 in original Destrieux
    des_left = [l for l in destrieux_labels if l <= 275]  # Adjust based on actual data
    for old_label in sorted(des_left):
        reindex_map[old_label] = new_index
        print(f"   Destrieux-LH {old_label} -> {new_index}")
        new_index += 1
    
    # Destrieux right hemisphere (276+)
    des_right = [l for l in destrieux_labels if l > 275]
    for old_label in sorted(des_right):
        reindex_map[old_label] = new_index
        print(f"   Destrieux-RH {old_label} -> {new_index}")
        new_index += 1
    
    print(f"✅ Created hemisphere-ordered mapping for {len(reindex_map)} regions")
    print(f"   New index range: 1 - {new_index-1}")
    
    # Save mapping
    map_path = Path("reindexing_map_hemisphere.json")
    reindex_map_serializable = {int(k): int(v) for k, v in reindex_map.items()}
    with open(map_path, 'w') as f:
        json.dump(reindex_map_serializable, f, indent=2)
    
    return reindex_map, atlas_img, atlas_data

def create_hemisphere_ordered_atlas(reindex_map, atlas_img, atlas_data):
    """Create new atlas with hemisphere ordering"""
    
    print("\n🏗️ Creating Hemisphere-Ordered Atlas...")
    
    # Create new data array
    new_atlas_data = np.zeros_like(atlas_data, dtype=np.int16)
    
    # Apply reindexing
    for old_label, new_label in reindex_map.items():
        mask = atlas_data == old_label
        new_atlas_data[mask] = new_label
        voxel_count = np.sum(mask)
        if voxel_count > 0:
            if new_label % 20 == 0:  # Print every 20th for brevity
                print(f"   Reindexed {old_label} -> {new_label}: {voxel_count} voxels")
    
    # Verify no data loss
    old_voxels = np.sum(atlas_data > 0)
    new_voxels = np.sum(new_atlas_data > 0)
    print(f"   Verification: {old_voxels} -> {new_voxels} voxels")
    
    if old_voxels != new_voxels:
        print("❌ ERROR: Voxel count mismatch!")
        return None
    
    # Save reindexed atlas (overwrite sequential)
    output_path = Path("final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    new_img = nib.Nifti1Image(new_atlas_data, atlas_img.affine, atlas_img.header)
    nib.save(new_img, output_path)
    
    # Also save as hierarchical
    hierarchical_path = Path("final_atlas/no_overlaps/levtiades_hierarchical.nii.gz")
    nib.save(new_img, hierarchical_path)
    
    print(f"✅ Hemisphere-ordered atlas saved: {output_path}")
    print(f"✅ Also saved as: {hierarchical_path}")
    
    return new_atlas_data, new_img

def load_all_labels():
    """Load labels from all source atlases"""
    
    print("\n📋 Loading All Labels...")
    
    # Levinson labels
    levinson_labels = {
        1: 'Locus_Coeruleus_LC',
        2: 'Nucleus_Tractus_Solitarius_NTS',
        3: 'Ventral_Tegmental_Area_VTA',
        4: 'Periaqueductal_Gray_PAG',
        5: 'Dorsal_Raphe_Nucleus_DRN'
    }
    
    # Load Tian labels
    tian_labels = {}
    tian_file = Path("../data/Tian2020MSA_v1.4/3T/Subcortex-Only/Tian_Subcortex_S4_3T_label.txt")
    if tian_file.exists():
        with open(tian_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                label = line.strip()
                if label:
                    tian_labels[i] = label
    
    # Load Destrieux labels
    destrieux_labels = {}
    des_file = Path("../tiandes_atlas/raw_atlases/destrieux_labels.txt")
    if des_file.exists():
        with open(des_file, 'r') as f:
            for line in f:
                if ':' in line and not line.startswith('#'):
                    parts = line.strip().split(':', 1)
                    if len(parts) == 2:
                        try:
                            idx = int(parts[0])
                            label = parts[1].strip()
                            # Skip removed regions
                            if idx not in [0, 42, 117]:
                                # Extract clean name from tuple format
                                if label.startswith('(') and ', \'' in label and label.endswith('\')'):
                                    clean_name = label.split(', \'')[1][:-2]
                                    destrieux_labels[idx] = clean_name
                                else:
                                    destrieux_labels[idx] = label
                        except ValueError:
                            continue
    
    print(f"   Loaded {len(levinson_labels)} Levinson labels")
    print(f"   Loaded {len(tian_labels)} Tian labels")
    print(f"   Loaded {len(destrieux_labels)} Destrieux labels")
    
    return levinson_labels, tian_labels, destrieux_labels

def create_hemisphere_ordered_labels(reindex_map, levinson_labels, tian_labels, destrieux_labels):
    """Create label file with hemisphere ordering"""
    
    print("\n📝 Creating Hemisphere-Ordered Label File...")
    
    label_path = Path("final_atlas/levtiades_labels.txt")
    
    with open(label_path, 'w') as f:
        f.write("# Levtiades Atlas - Complete Brain Parcellation Labels\n")
        f.write("# Sequential indexing 1-207 with hemisphere ordering\n")
        f.write("#\n")
        f.write("# Hemisphere Organization:\n")
        f.write("# - Levinson: Bilateral brainstem nuclei (1-5)\n")
        f.write("# - Tian: LEFT hemisphere (6-32), RIGHT hemisphere (33-59)\n")
        f.write("# - Destrieux: LEFT hemisphere (60-133), RIGHT hemisphere (134-207)\n")
        f.write("#\n")
        f.write("# Combining three complementary atlases:\n")
        f.write("# 1. Levinson-Bari Limbic Brainstem Atlas (Levinson et al. 2022)\n")
        f.write("#    - 5 critical brainstem/midbrain nuclei\n")
        f.write("# 2. Tian Subcortex S4 - Melbourne Subcortical Atlas (Tian et al. 2020)\n")
        f.write("#    - 54 subcortical structures at maximum resolution\n")
        f.write("#    - https://github.com/yetianmed/subcortex\n")
        f.write("# 3. Destrieux Cortical Atlas (Destrieux et al. 2010)\n")
        f.write("#    - 148 cortical regions (wall/background removed)\n")
        f.write("#\n")
        f.write("# Format: ID: Region_Name [Source_Atlas]\n\n")
        
        # Create reverse mapping
        reverse_map = {new_idx: old_idx for old_idx, new_idx in reindex_map.items()}
        
        # Track boundaries
        levinson_end = 5
        tian_left_end = 32
        tian_right_end = 59
        des_left_end = 133
        
        # Write Levinson regions
        f.write("# LEVINSON-BARI LIMBIC BRAINSTEM NUCLEI (1-5)\n")
        f.write("# Critical psychiatric circuit nodes\n")
        for new_idx in range(1, levinson_end + 1):
            if new_idx in reverse_map:
                old_idx = reverse_map[new_idx]
                name = levinson_labels.get(old_idx, f"Levinson_{old_idx}")
                f.write(f"{new_idx}: {name} [Levinson-Bari]\n")
        
        # Write Tian LEFT hemisphere
        f.write("\n# TIAN SUBCORTEX S4 - LEFT HEMISPHERE (6-32)\n")
        f.write("# Melbourne Subcortical Atlas - https://github.com/yetianmed/subcortex\n")
        tian_left_counter = 28  # Starting from 28 for left hemisphere indices
        for new_idx in range(levinson_end + 1, tian_left_end + 1):
            if new_idx in reverse_map:
                name = tian_labels.get(tian_left_counter, f"Tian_S4_{tian_left_counter}")
                f.write(f"{new_idx}: {name} [Tian-Melbourne-S4]\n")
                tian_left_counter += 1
        
        # Write Tian RIGHT hemisphere
        f.write("\n# TIAN SUBCORTEX S4 - RIGHT HEMISPHERE (33-59)\n")
        tian_right_counter = 1  # Starting from 1 for right hemisphere indices
        for new_idx in range(tian_left_end + 1, tian_right_end + 1):
            if new_idx in reverse_map:
                name = tian_labels.get(tian_right_counter, f"Tian_S4_{tian_right_counter}")
                f.write(f"{new_idx}: {name} [Tian-Melbourne-S4]\n")
                tian_right_counter += 1
        
        # Write Destrieux LEFT hemisphere
        f.write("\n# DESTRIEUX CORTICAL PARCELLATION - LEFT HEMISPHERE (60-133)\n")
        for new_idx in range(tian_right_end + 1, des_left_end + 1):
            if new_idx in reverse_map:
                old_idx = reverse_map[new_idx]
                original_idx = old_idx - 200
                name = destrieux_labels.get(original_idx, f"Destrieux_{original_idx}")
                f.write(f"{new_idx}: {name} [Destrieux]\n")
        
        # Write Destrieux RIGHT hemisphere
        f.write("\n# DESTRIEUX CORTICAL PARCELLATION - RIGHT HEMISPHERE (134-207)\n")
        for new_idx in range(des_left_end + 1, 208):
            if new_idx in reverse_map:
                old_idx = reverse_map[new_idx]
                original_idx = old_idx - 200
                name = destrieux_labels.get(original_idx, f"Destrieux_{original_idx}")
                f.write(f"{new_idx}: {name} [Destrieux]\n")
    
    print(f"✅ Hemisphere-ordered label file created: {label_path}")

def create_hemisphere_ordered_lookup_table(reindex_map, levinson_labels, tian_labels, destrieux_labels):
    """Create lookup table with hemisphere ordering"""
    
    print("\n🎨 Creating Hemisphere-Ordered Lookup Table...")
    
    lookup_path = Path("final_atlas/levtiades_lookup_table.txt")
    
    with open(lookup_path, 'w') as f:
        f.write("# Levtiades Atlas Lookup Table (MRIcrogl compatible)\n")
        f.write("# Hemisphere-ordered indexing 1-207\n")
        f.write("# Index\tR\tG\tB\tLabel\n")
        f.write("# Format: label_number<tab>red<tab>green<tab>blue<tab>source:label_name\n\n")
        
        # Create reverse mapping
        reverse_map = {new_idx: old_idx for old_idx, new_idx in reindex_map.items()}
        
        # Track boundaries for hemisphere identification
        levinson_end = 5
        tian_left_end = 32
        tian_right_end = 59
        des_left_end = 133
        
        # Tian label counters
        tian_left_counter = 28
        tian_right_counter = 1
        
        for new_idx in sorted(reverse_map.keys()):
            old_idx = reverse_map[new_idx]
            
            # Determine source, name, and color scheme
            if new_idx <= levinson_end:
                # Levinson - Red/Orange tones
                source = "Levinson"
                name = levinson_labels.get(old_idx, f"Levinson_{old_idx}")
                r = 255 - (new_idx * 20)
                g = 100 + (new_idx * 30)
                b = 50
                
            elif new_idx <= tian_left_end:
                # Tian LEFT - Green tones
                source = "Tian-S4-LH"
                name = tian_labels.get(tian_left_counter, f"Tian_S4_{tian_left_counter}")
                tian_left_counter += 1
                r = 50 + (new_idx % 5) * 20
                g = 180 + (new_idx % 8) * 10
                b = 120 + (new_idx % 5) * 20
                
            elif new_idx <= tian_right_end:
                # Tian RIGHT - Darker green tones
                source = "Tian-S4-RH"
                name = tian_labels.get(tian_right_counter, f"Tian_S4_{tian_right_counter}")
                tian_right_counter += 1
                r = 70 + (new_idx % 5) * 20
                g = 150 + (new_idx % 8) * 10
                b = 100 + (new_idx % 5) * 20
                
            elif new_idx <= des_left_end:
                # Destrieux LEFT - Blue tones
                source = "Destrieux-LH"
                original_idx = old_idx - 200
                name = destrieux_labels.get(original_idx, f"Destrieux_{original_idx}")
                r = 100 + (new_idx % 5) * 20
                g = 120 + (new_idx % 10) * 10
                b = 220 + (new_idx % 3) * 10
                
            else:
                # Destrieux RIGHT - Purple/blue tones
                source = "Destrieux-RH"
                original_idx = old_idx - 200
                name = destrieux_labels.get(original_idx, f"Destrieux_{original_idx}")
                r = 140 + (new_idx % 5) * 20
                g = 100 + (new_idx % 10) * 10
                b = 200 + (new_idx % 3) * 20
            
            # Ensure RGB values are valid
            r = min(255, max(0, r))
            g = min(255, max(0, g))
            b = min(255, max(0, b))
            
            f.write(f"{new_idx}\t{r}\t{g}\t{b}\t{source}:{name}\n")
    
    print(f"✅ Hemisphere-ordered lookup table created: {lookup_path}")

def validate_all_centroids():
    """Validate centroids for ALL regions between sequential and original atlases"""
    
    print("\n🔍 VALIDATING ALL REGION CENTROIDS")
    print("=" * 40)
    
    # Create validation directory
    val_dir = Path("centroid_validation")
    val_dir.mkdir(exist_ok=True)
    
    # Load reindexing map
    with open("reindexing_map_hemisphere.json", 'r') as f:
        reindex_map = json.load(f)
    reindex_map = {int(k): v for k, v in reindex_map.items()}
    
    # Load sequential atlas centroids
    seq_atlas_path = Path("final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    print(f"\n📍 Extracting centroids from {seq_atlas_path.name}...")
    
    seq_img = nib.load(seq_atlas_path)
    seq_data = seq_img.get_fdata().astype(int)
    seq_affine = seq_img.affine
    
    seq_centroids = {}
    unique_labels = sorted(np.unique(seq_data[seq_data > 0]))
    
    for label in unique_labels:
        mask = seq_data == label
        com_voxel = ndimage.center_of_mass(mask)
        com_mni = nib.affines.apply_affine(seq_affine, com_voxel)
        seq_centroids[label] = com_mni
        
        if label % 50 == 0:
            print(f"   Processed {label}/{len(unique_labels)} regions...")
    
    # Load original aligned atlases
    aligned_dir = Path("aligned_atlases")
    validation_results = []
    
    # 1. Validate ALL Levinson regions
    print("\n📍 Validating ALL Levinson Regions...")
    levinson_path = aligned_dir / "levinson_combined_aligned.nii.gz"
    if levinson_path.exists():
        levinson_img = nib.load(levinson_path)
        levinson_data = levinson_img.get_fdata().astype(int)
        levinson_affine = levinson_img.affine
        
        for old_idx in range(1, 6):
            if old_idx in reindex_map:
                new_idx = reindex_map[old_idx]
                mask = levinson_data == old_idx
                if np.any(mask):
                    com_voxel = ndimage.center_of_mass(mask)
                    com_mni = nib.affines.apply_affine(levinson_affine, com_voxel)
                    
                    seq_coord = seq_centroids.get(new_idx)
                    if seq_coord is not None:
                        distance = np.sqrt(np.sum((com_mni - seq_coord)**2))
                        
                        validation_results.append({
                            'source': 'Levinson',
                            'old_index': old_idx,
                            'new_index': new_idx,
                            'original_x': round(com_mni[0], 1),
                            'original_y': round(com_mni[1], 1),
                            'original_z': round(com_mni[2], 1),
                            'sequential_x': round(seq_coord[0], 1),
                            'sequential_y': round(seq_coord[1], 1),
                            'sequential_z': round(seq_coord[2], 1),
                            'distance_mm': round(distance, 2),
                            'match_status': 'MATCH' if distance < 2.0 else 'MISMATCH'
                        })
    
    # 2. Validate ALL Tian regions
    print("\n📍 Validating ALL Tian Regions...")
    tian_path = aligned_dir / "tian_aligned.nii.gz"
    if tian_path.exists():
        tian_img = nib.load(tian_path)
        tian_data = tian_img.get_fdata().astype(int)
        tian_affine = tian_img.affine
        
        for original_tian_idx in range(1, 55):
            old_idx = original_tian_idx + 100
            if old_idx in reindex_map:
                new_idx = reindex_map[old_idx]
                mask = tian_data == original_tian_idx
                if np.any(mask):
                    com_voxel = ndimage.center_of_mass(mask)
                    com_mni = nib.affines.apply_affine(tian_affine, com_voxel)
                    
                    seq_coord = seq_centroids.get(new_idx)
                    if seq_coord is not None:
                        distance = np.sqrt(np.sum((com_mni - seq_coord)**2))
                        
                        validation_results.append({
                            'source': 'Tian',
                            'old_index': old_idx,
                            'new_index': new_idx,
                            'original_x': round(com_mni[0], 1),
                            'original_y': round(com_mni[1], 1),
                            'original_z': round(com_mni[2], 1),
                            'sequential_x': round(seq_coord[0], 1),
                            'sequential_y': round(seq_coord[1], 1),
                            'sequential_z': round(seq_coord[2], 1),
                            'distance_mm': round(distance, 2),
                            'match_status': 'MATCH' if distance < 2.0 else 'MISMATCH'
                        })
        
        print(f"   Validated {len([r for r in validation_results if r['source'] == 'Tian'])} Tian regions")
    
    # 3. Validate ALL Destrieux regions
    print("\n📍 Validating ALL Destrieux Regions...")
    destrieux_path = aligned_dir / "destrieux_aligned.nii.gz"
    if destrieux_path.exists():
        des_img = nib.load(destrieux_path)
        des_data = des_img.get_fdata().astype(int)
        des_affine = des_img.affine
        
        # Get all unique Destrieux labels
        des_unique = sorted(np.unique(des_data[des_data > 0]))
        
        for original_des_idx in des_unique:
            if original_des_idx not in [0, 42, 117]:  # Skip removed regions
                old_idx = original_des_idx + 200
                if old_idx in reindex_map:
                    new_idx = reindex_map[old_idx]
                    mask = des_data == original_des_idx
                    if np.any(mask):
                        com_voxel = ndimage.center_of_mass(mask)
                        com_mni = nib.affines.apply_affine(des_affine, com_voxel)
                        
                        seq_coord = seq_centroids.get(new_idx)
                        if seq_coord is not None:
                            distance = np.sqrt(np.sum((com_mni - seq_coord)**2))
                            
                            validation_results.append({
                                'source': 'Destrieux',
                                'old_index': old_idx,
                                'new_index': new_idx,
                                'original_x': round(com_mni[0], 1),
                                'original_y': round(com_mni[1], 1),
                                'original_z': round(com_mni[2], 1),
                                'sequential_x': round(seq_coord[0], 1),
                                'sequential_y': round(seq_coord[1], 1),
                                'sequential_z': round(seq_coord[2], 1),
                                'distance_mm': round(distance, 2),
                                'match_status': 'MATCH' if distance < 2.0 else 'MISMATCH'
                            })
        
        print(f"   Validated {len([r for r in validation_results if r['source'] == 'Destrieux'])} Destrieux regions")
    
    # Save validation results
    val_df = pd.DataFrame(validation_results)
    val_csv_path = val_dir / "centroid_validation_results_all.csv"
    val_df.to_csv(val_csv_path, index=False)
    
    print(f"\n✅ Validation results saved: {val_csv_path}")
    
    # Summary statistics
    total_checked = len(validation_results)
    matches = len([r for r in validation_results if r['match_status'] == 'MATCH'])
    mismatches = total_checked - matches
    
    print(f"\n📊 VALIDATION SUMMARY:")
    print(f"   Total regions checked: {total_checked}")
    print(f"   Matches (< 2mm): {matches}")
    print(f"   Mismatches (≥ 2mm): {mismatches}")
    
    # Summary by source
    for source in ['Levinson', 'Tian', 'Destrieux']:
        source_results = [r for r in validation_results if r['source'] == source]
        source_matches = len([r for r in source_results if r['match_status'] == 'MATCH'])
        print(f"   {source}: {source_matches}/{len(source_results)} matches")
    
    # Create summary report
    report_path = val_dir / "validation_report_all.txt"
    with open(report_path, 'w') as f:
        f.write("LEVTIADES ATLAS CENTROID VALIDATION REPORT - ALL REGIONS\n")
        f.write("========================================================\n\n")
        f.write(f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Sequential Atlas: {seq_atlas_path}\n")
        f.write(f"Hemisphere Ordering: Left-first for Tian and Destrieux\n\n")
        f.write("SUMMARY:\n")
        f.write(f"- Total regions checked: {total_checked}\n")
        f.write(f"- Matching centroids (< 2mm): {matches}\n")
        f.write(f"- Mismatched centroids (≥ 2mm): {mismatches}\n\n")
        
        f.write("BY SOURCE:\n")
        for source in ['Levinson', 'Tian', 'Destrieux']:
            source_results = [r for r in validation_results if r['source'] == source]
            source_matches = len([r for r in source_results if r['match_status'] == 'MATCH'])
            f.write(f"- {source}: {source_matches}/{len(source_results)} matches\n")
        
        if mismatches > 0:
            f.write("\nMISMATCHED REGIONS:\n")
            for _, row in val_df[val_df['match_status'] == 'MISMATCH'].iterrows():
                f.write(f"- {row['source']} region {row['old_index']} -> {row['new_index']}: ")
                f.write(f"{row['distance_mm']}mm difference\n")
    
    print(f"✅ Validation report saved: {report_path}")
    
    return val_df

if __name__ == "__main__":
    print("🔄 REMAKING LEVTIADES ATLAS WITH HEMISPHERE ORDERING")
    print("=" * 55)
    print("Order: Levinson → Tian-L → Tian-R → Destrieux-L → Destrieux-R")
    print("")
    
    # Step 1: Create hemisphere-ordered reindexing map
    reindex_map, atlas_img, atlas_data = create_hemisphere_ordered_reindexing_map()
    
    # Step 2: Create reindexed atlas
    new_atlas_data, new_atlas_img = create_hemisphere_ordered_atlas(reindex_map, atlas_img, atlas_data)
    
    if new_atlas_data is None:
        print("❌ Reindexing failed!")
        exit(1)
    
    # Step 3: Load all labels
    levinson_labels, tian_labels, destrieux_labels = load_all_labels()
    
    # Step 4: Create hemisphere-ordered label file
    create_hemisphere_ordered_labels(reindex_map, levinson_labels, tian_labels, destrieux_labels)
    
    # Step 5: Create hemisphere-ordered lookup table
    create_hemisphere_ordered_lookup_table(reindex_map, levinson_labels, tian_labels, destrieux_labels)
    
    # Step 6: Validate ALL centroids
    validation_df = validate_all_centroids()
    
    print("\n✅ HEMISPHERE-ORDERED ATLAS COMPLETE!")
    print("=" * 40)
    print("📊 Atlas files overwritten with hemisphere ordering")
    print("📋 Labels and lookup tables updated")
    print("✅ All regions validated")