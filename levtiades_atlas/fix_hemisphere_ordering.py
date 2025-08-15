#!/usr/bin/env python3
"""
Fix hemisphere ordering for Levtiades Atlas
Starting from the current sequential atlas (1-207)
Reorder to: Levinson → Tian-LH → Tian-RH → Destrieux-LH → Destrieux-RH
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import json
import pandas as pd
from scipy import ndimage

def create_hemisphere_reordering_map():
    """Create mapping for hemisphere reordering from current sequential atlas"""
    
    print("📊 Creating Hemisphere Reordering Map...")
    
    # Load the current sequential atlas
    atlas_path = Path("final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # Get current unique labels (should be 1-207)
    current_labels = sorted(np.unique(atlas_data[atlas_data > 0]))
    print(f"   Found {len(current_labels)} labels in current atlas")
    print(f"   Current range: {current_labels[0]} to {current_labels[-1]}")
    
    # Load the original mapping to understand which regions are left/right
    mapping_df = pd.read_csv("index_mapping_reference.csv")
    
    # Create lists for each category
    levinson_indices = []
    tian_left_indices = []
    tian_right_indices = []
    destrieux_left_indices = []
    destrieux_right_indices = []
    
    for _, row in mapping_df.iterrows():
        new_idx = row['new_index']
        old_idx = row['old_index']
        source = row['source']
        name = row['region_name']
        
        if source == 'Levinson':
            levinson_indices.append(new_idx)
        elif source == 'Tian':
            # Tian: odd old indices (101,103,105...) are right, even (102,104,106...) are left
            if old_idx % 2 == 0:  # Even = left
                tian_left_indices.append(new_idx)
            else:  # Odd = right
                tian_right_indices.append(new_idx)
        elif source == 'Destrieux':
            # Check if the name contains 'L ' or 'R ' prefix
            if isinstance(name, str):
                if name.startswith('L ') or 'L ' in name[:10]:
                    destrieux_left_indices.append(new_idx)
                elif name.startswith('R ') or 'R ' in name[:10]:
                    destrieux_right_indices.append(new_idx)
    
    print(f"   Levinson: {len(levinson_indices)} regions")
    print(f"   Tian Left: {len(tian_left_indices)} regions")
    print(f"   Tian Right: {len(tian_right_indices)} regions")
    print(f"   Destrieux Left: {len(destrieux_left_indices)} regions")
    print(f"   Destrieux Right: {len(destrieux_right_indices)} regions")
    
    # Create reordering map
    reorder_map = {}
    new_index = 1
    
    # 1. Levinson (1-5)
    for old_idx in sorted(levinson_indices):
        reorder_map[old_idx] = new_index
        print(f"   Levinson {old_idx} -> {new_index}")
        new_index += 1
    
    # 2. Tian Left hemisphere
    for old_idx in sorted(tian_left_indices):
        reorder_map[old_idx] = new_index
        new_index += 1
    print(f"   Tian-LH: mapped {len(tian_left_indices)} regions to {new_index-len(tian_left_indices)}-{new_index-1}")
    
    # 3. Tian Right hemisphere
    for old_idx in sorted(tian_right_indices):
        reorder_map[old_idx] = new_index
        new_index += 1
    print(f"   Tian-RH: mapped {len(tian_right_indices)} regions to {new_index-len(tian_right_indices)}-{new_index-1}")
    
    # 4. Destrieux Left hemisphere
    for old_idx in sorted(destrieux_left_indices):
        reorder_map[old_idx] = new_index
        new_index += 1
    print(f"   Destrieux-LH: mapped {len(destrieux_left_indices)} regions to {new_index-len(destrieux_left_indices)}-{new_index-1}")
    
    # 5. Destrieux Right hemisphere
    for old_idx in sorted(destrieux_right_indices):
        reorder_map[old_idx] = new_index
        new_index += 1
    print(f"   Destrieux-RH: mapped {len(destrieux_right_indices)} regions to {new_index-len(destrieux_right_indices)}-{new_index-1}")
    
    print(f"✅ Created reordering map for {len(reorder_map)} regions")
    
    # Save mapping
    map_path = Path("hemisphere_reorder_map.json")
    with open(map_path, 'w') as f:
        json.dump(reorder_map, f, indent=2)
    
    return reorder_map, atlas_img, atlas_data

def apply_hemisphere_reordering(reorder_map, atlas_img, atlas_data):
    """Apply the hemisphere reordering to create new atlas"""
    
    print("\n🏗️ Applying Hemisphere Reordering...")
    
    # Create new data array
    new_atlas_data = np.zeros_like(atlas_data, dtype=np.int16)
    
    # Apply reordering
    for old_label, new_label in reorder_map.items():
        mask = atlas_data == old_label
        new_atlas_data[mask] = new_label
        voxel_count = np.sum(mask)
        if voxel_count > 0 and new_label % 50 == 0:
            print(f"   Reordered {old_label} -> {new_label}: {voxel_count} voxels")
    
    # Verify no data loss
    old_voxels = np.sum(atlas_data > 0)
    new_voxels = np.sum(new_atlas_data > 0)
    print(f"   Verification: {old_voxels} -> {new_voxels} voxels")
    
    if old_voxels != new_voxels:
        print("❌ ERROR: Voxel count mismatch!")
        return None
    
    # Save reordered atlas (overwrite sequential and hierarchical)
    output_path = Path("final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    new_img = nib.Nifti1Image(new_atlas_data, atlas_img.affine, atlas_img.header)
    nib.save(new_img, output_path)
    
    hierarchical_path = Path("final_atlas/no_overlaps/levtiades_hierarchical.nii.gz")
    nib.save(new_img, hierarchical_path)
    
    print(f"✅ Hemisphere-ordered atlas saved: {output_path}")
    print(f"✅ Also saved as: {hierarchical_path}")
    
    return new_atlas_data, new_img

def create_hemisphere_ordered_csvs(reorder_map):
    """Update CSV files with hemisphere ordering"""
    
    print("\n📋 Updating CSV Files...")
    
    # Load original data
    mapping_df = pd.read_csv("index_mapping_reference.csv")
    
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
    
    # Create new labels data
    labels_data = []
    
    for old_idx, new_idx in sorted(reorder_map.items(), key=lambda x: x[1]):
        # Find the original info
        row = mapping_df[mapping_df['new_index'] == old_idx].iloc[0]
        source = row['source']
        old_old_idx = row['old_index']
        
        if source == 'Levinson':
            name = row['region_name']
        elif source == 'Tian':
            # Get proper Tian label
            tian_idx = old_old_idx - 100  # Convert back to 1-54
            name = tian_labels.get(tian_idx, f"Tian_{tian_idx}")
        else:  # Destrieux
            # Clean up the name
            name = row['region_name']
            if isinstance(name, str) and name.startswith("(") and "')" in name:
                # Extract from tuple format
                name = name.split("'")[1]
        
        labels_data.append({
            'index': new_idx,
            'region_name': name,
            'source_atlas': f"{source}-Melbourne-S4" if source == 'Tian' else source
        })
    
    # Save labels CSV
    labels_df = pd.DataFrame(labels_data)
    labels_df.to_csv("final_atlas/levtiades_labels.csv", index=False)
    print("✅ Updated levtiades_labels.csv")
    
    # Extract centroids for coordinates CSV
    print("\n📍 Extracting Centroids...")
    atlas_path = Path("final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    affine = atlas_img.affine
    
    regions_data = []
    for _, row in labels_df.iterrows():
        label = row['index']
        mask = atlas_data == label
        if np.any(mask):
            com_voxel = ndimage.center_of_mass(mask)
            com_mni = nib.affines.apply_affine(affine, com_voxel)
            
            regions_data.append({
                'index': label,
                'region_name': row['region_name'],
                'source_atlas': row['source_atlas'],
                'mni_x': round(com_mni[0], 1),
                'mni_y': round(com_mni[1], 1),
                'mni_z': round(com_mni[2], 1),
                'volume_voxels': int(np.sum(mask)),
                'volume_mm3': int(np.sum(mask)) * 8
            })
    
    regions_df = pd.DataFrame(regions_data)
    regions_df.to_csv("final_atlas/levtiades_regions_with_coordinates.csv", index=False)
    print("✅ Updated levtiades_regions_with_coordinates.csv")

def create_hemisphere_ordered_labels_txt(reorder_map):
    """Create properly formatted label text file"""
    
    print("\n📝 Creating Label Text File...")
    
    # Load data
    mapping_df = pd.read_csv("index_mapping_reference.csv")
    
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
        
        # Track boundaries
        levinson_end = 5
        tian_left_end = 32
        tian_right_end = 59
        des_left_end = 133
        
        # Write regions in order
        for old_idx, new_idx in sorted(reorder_map.items(), key=lambda x: x[1]):
            row = mapping_df[mapping_df['new_index'] == old_idx].iloc[0]
            source = row['source']
            old_old_idx = row['old_index']
            
            # Add section headers
            if new_idx == 1:
                f.write("# LEVINSON-BARI LIMBIC BRAINSTEM NUCLEI (1-5)\n")
                f.write("# Critical psychiatric circuit nodes\n")
            elif new_idx == 6:
                f.write("\n# TIAN SUBCORTEX S4 - LEFT HEMISPHERE (6-32)\n")
                f.write("# Melbourne Subcortical Atlas - https://github.com/yetianmed/subcortex\n")
            elif new_idx == 33:
                f.write("\n# TIAN SUBCORTEX S4 - RIGHT HEMISPHERE (33-59)\n")
            elif new_idx == 60:
                f.write("\n# DESTRIEUX CORTICAL PARCELLATION - LEFT HEMISPHERE (60-133)\n")
            elif new_idx == 134:
                f.write("\n# DESTRIEUX CORTICAL PARCELLATION - RIGHT HEMISPHERE (134-207)\n")
            
            # Get proper name
            if source == 'Levinson':
                name = row['region_name']
                atlas_name = "Levinson-Bari"
            elif source == 'Tian':
                tian_idx = old_old_idx - 100
                name = tian_labels.get(tian_idx, f"Tian_{tian_idx}")
                atlas_name = "Tian-Melbourne-S4"
            else:  # Destrieux
                name = row['region_name']
                if isinstance(name, str) and name.startswith("(") and "')" in name:
                    name = name.split("'")[1]
                atlas_name = "Destrieux"
            
            f.write(f"{new_idx}: {name} [{atlas_name}]\n")
    
    print(f"✅ Label file created: {label_path}")

def create_hemisphere_ordered_lookup_table(reorder_map):
    """Create MRIcrogl lookup table"""
    
    print("\n🎨 Creating Lookup Table...")
    
    # Load data
    mapping_df = pd.read_csv("index_mapping_reference.csv")
    
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
    
    lookup_path = Path("final_atlas/levtiades_lookup_table.txt")
    
    with open(lookup_path, 'w') as f:
        f.write("# Levtiades Atlas Lookup Table (MRIcrogl compatible)\n")
        f.write("# Hemisphere-ordered indexing 1-207\n")
        f.write("# Index\tR\tG\tB\tLabel\n")
        f.write("# Format: label_number<tab>red<tab>green<tab>blue<tab>source:label_name\n\n")
        
        for old_idx, new_idx in sorted(reorder_map.items(), key=lambda x: x[1]):
            row = mapping_df[mapping_df['new_index'] == old_idx].iloc[0]
            source = row['source']
            old_old_idx = row['old_index']
            
            # Get proper name
            if source == 'Levinson':
                name = row['region_name']
                # Red/Orange tones
                r = 255 - (new_idx * 20)
                g = 100 + (new_idx * 30)
                b = 50
            elif source == 'Tian':
                tian_idx = old_old_idx - 100
                name = tian_labels.get(tian_idx, f"Tian_{tian_idx}")
                # Green tones, slightly different for L/R
                if new_idx <= 32:  # Left
                    r = 50 + (new_idx % 5) * 20
                    g = 180 + (new_idx % 8) * 10
                    b = 120 + (new_idx % 5) * 20
                else:  # Right
                    r = 70 + (new_idx % 5) * 20
                    g = 150 + (new_idx % 8) * 10
                    b = 100 + (new_idx % 5) * 20
            else:  # Destrieux
                name = row['region_name']
                if isinstance(name, str) and name.startswith("(") and "')" in name:
                    name = name.split("'")[1]
                # Blue tones, slightly different for L/R
                if new_idx <= 133:  # Left
                    r = 100 + (new_idx % 5) * 20
                    g = 120 + (new_idx % 10) * 10
                    b = 220 + (new_idx % 3) * 10
                else:  # Right
                    r = 140 + (new_idx % 5) * 20
                    g = 100 + (new_idx % 10) * 10
                    b = 200 + (new_idx % 3) * 20
            
            # Ensure valid RGB
            r = min(255, max(0, r))
            g = min(255, max(0, g))
            b = min(255, max(0, b))
            
            f.write(f"{new_idx}\t{r}\t{g}\t{b}\t{source}:{name}\n")
    
    # Also create CSV version
    lookup_df = []
    for old_idx, new_idx in sorted(reorder_map.items(), key=lambda x: x[1]):
        row = mapping_df[mapping_df['new_index'] == old_idx].iloc[0]
        source = row['source']
        old_old_idx = row['old_index']
        
        if source == 'Levinson':
            name = row['region_name']
            r = 255 - (new_idx * 20)
            g = 100 + (new_idx * 30)
            b = 50
        elif source == 'Tian':
            tian_idx = old_old_idx - 100
            name = tian_labels.get(tian_idx, f"Tian_{tian_idx}")
            if new_idx <= 32:
                r = 50 + (new_idx % 5) * 20
                g = 180 + (new_idx % 8) * 10
                b = 120 + (new_idx % 5) * 20
            else:
                r = 70 + (new_idx % 5) * 20
                g = 150 + (new_idx % 8) * 10
                b = 100 + (new_idx % 5) * 20
        else:
            name = row['region_name']
            if isinstance(name, str) and name.startswith("(") and "')" in name:
                name = name.split("'")[1]
            if new_idx <= 133:
                r = 100 + (new_idx % 5) * 20
                g = 120 + (new_idx % 10) * 10
                b = 220 + (new_idx % 3) * 10
            else:
                r = 140 + (new_idx % 5) * 20
                g = 100 + (new_idx % 10) * 10
                b = 200 + (new_idx % 3) * 20
        
        r = min(255, max(0, r))
        g = min(255, max(0, g))
        b = min(255, max(0, b))
        
        lookup_df.append({
            'index': new_idx,
            'R': r,
            'G': g,
            'B': b,
            'label': f"{source}:{name}"
        })
    
    pd.DataFrame(lookup_df).to_csv("final_atlas/levtiades_lookup_table.csv", index=False)
    
    print(f"✅ Lookup table created: {lookup_path}")
    print("✅ Also created levtiades_lookup_table.csv")

if __name__ == "__main__":
    print("🔄 FIXING HEMISPHERE ORDERING FOR LEVTIADES ATLAS")
    print("=" * 55)
    print("Target order: Levinson → Tian-LH → Tian-RH → Destrieux-LH → Destrieux-RH")
    print("")
    
    # Step 1: Create reordering map
    reorder_map, atlas_img, atlas_data = create_hemisphere_reordering_map()
    
    # Step 2: Apply reordering to atlas
    new_atlas_data, new_atlas_img = apply_hemisphere_reordering(reorder_map, atlas_img, atlas_data)
    
    if new_atlas_data is None:
        print("❌ Reordering failed!")
        exit(1)
    
    # Step 3: Update CSV files
    create_hemisphere_ordered_csvs(reorder_map)
    
    # Step 4: Create label text file
    create_hemisphere_ordered_labels_txt(reorder_map)
    
    # Step 5: Create lookup table
    create_hemisphere_ordered_lookup_table(reorder_map)
    
    print("\n✅ HEMISPHERE ORDERING COMPLETE!")
    print("=" * 35)
    print("📊 Atlas files updated with correct hemisphere ordering")
    print("📋 All label files and CSVs updated")
    print("🎨 Lookup table created")