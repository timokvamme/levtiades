#!/usr/bin/env python3
"""
Create final Levtiades Atlas with proper hemisphere ordering
Overwrite existing files - no new naming conventions
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import pandas as pd
from scipy import ndimage
import json

def create_final_atlas():
    """Create final atlas with hemisphere ordering, overwriting existing files"""
    
    print("🔄 CREATING FINAL LEVTIADES ATLAS")
    print("=" * 40)
    print("Order: Levinson → Tian-L → Tian-R → Destrieux-L → Destrieux-R")
    print("Overwriting existing atlas files")
    print("")
    
    # Load current atlas and create hemisphere-ordered version
    atlas_path = Path("final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # Load original mapping to understand structure
    mapping_df = pd.read_csv("index_mapping_reference.csv")
    
    # Create hemisphere reordering based on original sequential mapping
    hemisphere_map = {}
    new_index = 1
    
    # 1. Levinson regions (already in correct order 1-5)
    levinson_rows = mapping_df[mapping_df['source'] == 'Levinson'].sort_values('new_index')
    for _, row in levinson_rows.iterrows():
        hemisphere_map[row['new_index']] = new_index
        print(f"   Levinson {row['new_index']} -> {new_index}")
        new_index += 1
    
    # 2. Tian LEFT hemisphere (even old indices: 102,104,106...)
    tian_rows = mapping_df[mapping_df['source'] == 'Tian'].sort_values('old_index')
    tian_left = tian_rows[tian_rows['old_index'] % 2 == 0]  # Even = left
    for _, row in tian_left.iterrows():
        hemisphere_map[row['new_index']] = new_index
        new_index += 1
    print(f"   Tian LEFT: {len(tian_left)} regions -> {new_index-len(tian_left)}-{new_index-1}")
    
    # 3. Tian RIGHT hemisphere (odd old indices: 101,103,105...)
    tian_right = tian_rows[tian_rows['old_index'] % 2 == 1]  # Odd = right
    for _, row in tian_right.iterrows():
        hemisphere_map[row['new_index']] = new_index
        new_index += 1
    print(f"   Tian RIGHT: {len(tian_right)} regions -> {new_index-len(tian_right)}-{new_index-1}")
    
    # 4. Destrieux LEFT hemisphere (L prefix)
    des_rows = mapping_df[mapping_df['source'] == 'Destrieux'].sort_values('new_index')
    des_left = des_rows[des_rows['region_name'].str.contains("'L ", na=False)]
    for _, row in des_left.iterrows():
        hemisphere_map[row['new_index']] = new_index
        new_index += 1
    print(f"   Destrieux LEFT: {len(des_left)} regions -> {new_index-len(des_left)}-{new_index-1}")
    
    # 5. Destrieux RIGHT hemisphere (R prefix)
    des_right = des_rows[des_rows['region_name'].str.contains("'R ", na=False)]
    for _, row in des_right.iterrows():
        hemisphere_map[row['new_index']] = new_index
        new_index += 1
    print(f"   Destrieux RIGHT: {len(des_right)} regions -> {new_index-len(des_right)}-{new_index-1}")
    
    print(f"✅ Created hemisphere mapping for {len(hemisphere_map)} regions")
    
    # Apply hemisphere reordering
    print("\n🏗️ Applying Hemisphere Reordering...")
    new_atlas_data = np.zeros_like(atlas_data, dtype=np.int16)
    
    for old_idx, new_idx in hemisphere_map.items():
        mask = atlas_data == old_idx
        new_atlas_data[mask] = new_idx
        if new_idx % 50 == 0:
            print(f"   Reordered {old_idx} -> {new_idx}")
    
    # Verify no data loss
    old_voxels = np.sum(atlas_data > 0)
    new_voxels = np.sum(new_atlas_data > 0)
    print(f"   Verification: {old_voxels} -> {new_voxels} voxels")
    
    if old_voxels != new_voxels:
        print("❌ ERROR: Voxel count mismatch!")
        return None, None
    
    # Save atlas (overwrite existing)
    new_img = nib.Nifti1Image(new_atlas_data, atlas_img.affine, atlas_img.header)
    nib.save(new_img, atlas_path)
    print(f"✅ Overwritten: {atlas_path}")
    
    # Save hemisphere mapping for validation
    with open("hemisphere_reorder_map.json", 'w') as f:
        json.dump(hemisphere_map, f, indent=2)
    
    return new_atlas_data, new_img, hemisphere_map

def validate_all_centroids(hemisphere_map):
    """Validate ALL regions match exactly with aligned atlases"""
    
    print("\n🔍 VALIDATING ALL REGION CENTROIDS")
    print("=" * 40)
    
    # Load atlas
    atlas_path = Path("final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    affine = atlas_img.affine
    
    # Get centroids from final atlas
    print("📍 Extracting centroids from final atlas...")
    final_centroids = {}
    unique_labels = sorted(np.unique(atlas_data[atlas_data > 0]))
    
    for label in unique_labels:
        mask = atlas_data == label
        com_voxel = ndimage.center_of_mass(mask)
        com_mni = nib.affines.apply_affine(affine, com_voxel)
        final_centroids[label] = com_mni
    
    print(f"✅ Extracted {len(final_centroids)} centroids")
    
    # Load original mapping
    mapping_df = pd.read_csv("index_mapping_reference.csv")
    reverse_hemisphere = {v: k for k, v in hemisphere_map.items()}
    
    validation_results = []
    aligned_dir = Path("aligned_atlases")
    
    # Validate Levinson (1-5)
    print("\n📍 Validating Levinson regions...")
    levinson_path = aligned_dir / "levinson_combined_aligned.nii.gz"
    if levinson_path.exists():
        lev_img = nib.load(levinson_path)
        lev_data = lev_img.get_fdata().astype(int)
        lev_affine = lev_img.affine
        
        for new_idx in range(1, 6):
            old_seq_idx = reverse_hemisphere[new_idx]
            orig_row = mapping_df[mapping_df['new_index'] == old_seq_idx].iloc[0]
            orig_idx = orig_row['old_index']
            
            # Get centroid from aligned Levinson
            mask = lev_data == orig_idx
            if np.any(mask):
                com_voxel = ndimage.center_of_mass(mask)
                com_mni = nib.affines.apply_affine(lev_affine, com_voxel)
                
                # Compare with final atlas
                final_coord = final_centroids[new_idx]
                distance = np.sqrt(np.sum((com_mni - final_coord)**2))
                
                validation_results.append({
                    'final_index': new_idx,
                    'source': 'Levinson',
                    'aligned_x': round(com_mni[0], 1),
                    'aligned_y': round(com_mni[1], 1),
                    'aligned_z': round(com_mni[2], 1),
                    'final_x': round(final_coord[0], 1),
                    'final_y': round(final_coord[1], 1),
                    'final_z': round(final_coord[2], 1),
                    'distance_mm': round(distance, 2),
                    'match': 'MATCH' if distance < 1.0 else 'MISMATCH'
                })
    
    # Validate Tian (6-59)
    print("📍 Validating Tian regions...")
    tian_path = aligned_dir / "tian_aligned.nii.gz"
    if tian_path.exists():
        tian_img = nib.load(tian_path)
        tian_data = tian_img.get_fdata().astype(int)
        tian_affine = tian_img.affine
        
        for new_idx in range(6, 60):
            old_seq_idx = reverse_hemisphere[new_idx]
            orig_row = mapping_df[mapping_df['new_index'] == old_seq_idx].iloc[0]
            orig_tian_idx = orig_row['old_index'] - 100  # Convert to 1-54
            
            # Get centroid from aligned Tian
            mask = tian_data == orig_tian_idx
            if np.any(mask):
                com_voxel = ndimage.center_of_mass(mask)
                com_mni = nib.affines.apply_affine(tian_affine, com_voxel)
                
                # Compare with final atlas
                final_coord = final_centroids[new_idx]
                distance = np.sqrt(np.sum((com_mni - final_coord)**2))
                
                validation_results.append({
                    'final_index': new_idx,
                    'source': 'Tian',
                    'aligned_x': round(com_mni[0], 1),
                    'aligned_y': round(com_mni[1], 1),
                    'aligned_z': round(com_mni[2], 1),
                    'final_x': round(final_coord[0], 1),
                    'final_y': round(final_coord[1], 1),
                    'final_z': round(final_coord[2], 1),
                    'distance_mm': round(distance, 2),
                    'match': 'MATCH' if distance < 1.0 else 'MISMATCH'
                })
    
    # Validate Destrieux (60-207)
    print("📍 Validating Destrieux regions...")
    des_path = aligned_dir / "destrieux_aligned.nii.gz"
    if des_path.exists():
        des_img = nib.load(des_path)
        des_data = des_img.get_fdata().astype(int)
        des_affine = des_img.affine
        
        for new_idx in range(60, 208):
            if new_idx in reverse_hemisphere:
                old_seq_idx = reverse_hemisphere[new_idx]
                orig_row = mapping_df[mapping_df['new_index'] == old_seq_idx]
                if not orig_row.empty:
                    orig_des_idx = orig_row.iloc[0]['old_index'] - 200
                    
                    # Get centroid from aligned Destrieux
                    mask = des_data == orig_des_idx
                    if np.any(mask):
                        com_voxel = ndimage.center_of_mass(mask)
                        com_mni = nib.affines.apply_affine(des_affine, com_voxel)
                        
                        # Compare with final atlas
                        final_coord = final_centroids[new_idx]
                        distance = np.sqrt(np.sum((com_mni - final_coord)**2))
                        
                        validation_results.append({
                            'final_index': new_idx,
                            'source': 'Destrieux',
                            'aligned_x': round(com_mni[0], 1),
                            'aligned_y': round(com_mni[1], 1),
                            'aligned_z': round(com_mni[2], 1),
                            'final_x': round(final_coord[0], 1),
                            'final_y': round(final_coord[1], 1),
                            'final_z': round(final_coord[2], 1),
                            'distance_mm': round(distance, 2),
                            'match': 'MATCH' if distance < 1.0 else 'MISMATCH'
                        })
    
    # Save validation results (overwrite existing)
    val_df = pd.DataFrame(validation_results)
    val_csv_path = Path("centroid_validation/centroid_validation_results.csv")
    val_csv_path.parent.mkdir(exist_ok=True)
    val_df.to_csv(val_csv_path, index=False)
    
    # Summary
    total = len(validation_results)
    matches = len([r for r in validation_results if r['match'] == 'MATCH'])
    
    print(f"\n📊 VALIDATION SUMMARY:")
    print(f"   Total regions: {total}")
    print(f"   Perfect matches: {matches}")
    print(f"   Mismatches: {total - matches}")
    
    for source in ['Levinson', 'Tian', 'Destrieux']:
        source_results = [r for r in validation_results if r['source'] == source]
        source_matches = len([r for r in source_results if r['match'] == 'MATCH'])
        if source_results:
            print(f"   {source}: {source_matches}/{len(source_results)} matches")
    
    # Save report (overwrite existing)
    report_path = Path("centroid_validation/validation_report.txt")
    with open(report_path, 'w') as f:
        f.write("LEVTIADES ATLAS CENTROID VALIDATION REPORT\n")
        f.write("==========================================\n\n")
        f.write(f"Total regions validated: {total}\n")
        f.write(f"Perfect matches (< 1mm): {matches}\n")
        f.write(f"Mismatches (≥ 1mm): {total - matches}\n\n")
        
        for source in ['Levinson', 'Tian', 'Destrieux']:
            source_results = [r for r in validation_results if r['source'] == source]
            source_matches = len([r for r in source_results if r['match'] == 'MATCH'])
            if source_results:
                f.write(f"{source}: {source_matches}/{len(source_results)} matches\n")
    
    print(f"✅ Validation saved: {val_csv_path}")
    print(f"✅ Report saved: {report_path}")
    
    return val_df

def update_all_files(hemisphere_map):
    """Update all label files and CSVs (overwrite existing)"""
    
    print("\n📋 UPDATING ALL FILES...")
    
    # Load atlas for coordinates
    atlas_path = Path("final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    affine = atlas_img.affine
    
    # Load original mapping and Tian labels
    mapping_df = pd.read_csv("index_mapping_reference.csv")
    
    # Load Tian labels
    tian_labels = {}
    tian_file = Path("../data/Tian2020MSA_v1.4/3T/Subcortex-Only/Tian_Subcortex_S4_3T_label.txt")
    if tian_file.exists():
        with open(tian_file, 'r') as f:
            for i, line in enumerate(f, 1):
                label = line.strip()
                if label:
                    tian_labels[i] = label
    
    # Create final data
    reverse_hemisphere = {v: k for k, v in hemisphere_map.items()}
    final_data = []
    
    for new_idx in range(1, 208):
        if new_idx in reverse_hemisphere:
            old_seq_idx = reverse_hemisphere[new_idx]
            orig_row = mapping_df[mapping_df['new_index'] == old_seq_idx].iloc[0]
            
            # Get coordinates
            mask = atlas_data == new_idx
            if np.any(mask):
                com_voxel = ndimage.center_of_mass(mask)
                com_mni = nib.affines.apply_affine(affine, com_voxel)
                
                # Get proper name
                source = orig_row['source']
                if source == 'Levinson':
                    name = orig_row['region_name']
                elif source == 'Tian':
                    tian_idx = orig_row['old_index'] - 100
                    name = tian_labels.get(tian_idx, f"Tian_{tian_idx}")
                else:  # Destrieux
                    name = orig_row['region_name']
                    if isinstance(name, str) and "')" in name:
                        name = name.split("'")[1]  # Extract from tuple
                
                final_data.append({
                    'index': new_idx,
                    'region_name': name,
                    'source_atlas': source,
                    'mni_x': round(com_mni[0], 1),
                    'mni_y': round(com_mni[1], 1),
                    'mni_z': round(com_mni[2], 1),
                    'volume_voxels': int(np.sum(mask)),
                    'volume_mm3': int(np.sum(mask)) * 8
                })
    
    # Update CSV files (overwrite existing)
    final_df = pd.DataFrame(final_data)
    
    # Labels CSV
    labels_df = final_df[['index', 'region_name', 'source_atlas']].copy()
    labels_df.to_csv("final_atlas/levtiades_labels.csv", index=False)
    
    # Coordinates CSV
    final_df.to_csv("final_atlas/levtiades_regions_with_coordinates.csv", index=False)
    
    # Lookup table CSV
    lookup_data = []
    for _, row in final_df.iterrows():
        idx = row['index']
        source = row['source_atlas']
        name = row['region_name']
        
        # Color by source and hemisphere
        if source == 'Levinson':
            r, g, b = 255 - (idx * 20), 100 + (idx * 30), 50
        elif source == 'Tian':
            if idx <= 32:  # Left
                r, g, b = 50 + (idx % 5) * 20, 180 + (idx % 8) * 10, 120 + (idx % 5) * 20
            else:  # Right
                r, g, b = 70 + (idx % 5) * 20, 150 + (idx % 8) * 10, 100 + (idx % 5) * 20
        else:  # Destrieux
            if idx <= 133:  # Left
                r, g, b = 100 + (idx % 5) * 20, 120 + (idx % 10) * 10, 220 + (idx % 3) * 10
            else:  # Right
                r, g, b = 140 + (idx % 5) * 20, 100 + (idx % 10) * 10, 200 + (idx % 3) * 20
        
        r, g, b = min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b))
        
        lookup_data.append({
            'index': idx,
            'R': r,
            'G': g,
            'B': b,
            'label': f"{source}:{name}"
        })
    
    lookup_df = pd.DataFrame(lookup_data)
    lookup_df.to_csv("final_atlas/levtiades_lookup_table.csv", index=False)
    
    # Text files (overwrite existing)
    # Labels
    with open("final_atlas/levtiades_labels.txt", 'w') as f:
        f.write("# Levtiades Atlas - Brain Parcellation Labels\n")
        f.write("# Hemisphere ordering: Levinson → Tian-L → Tian-R → Destrieux-L → Destrieux-R\n")
        f.write("# Format: ID: Region_Name [Source_Atlas]\n\n")
        
        for _, row in final_df.iterrows():
            f.write(f"{row['index']}: {row['region_name']} [{row['source_atlas']}]\n")
    
    # Lookup table
    with open("final_atlas/levtiades_lookup_table.txt", 'w') as f:
        f.write("# Levtiades Atlas Lookup Table (MRIcrogl compatible)\n")
        f.write("# Index\tR\tG\tB\tLabel\n\n")
        
        for _, row in lookup_df.iterrows():
            f.write(f"{row['index']}\t{row['R']}\t{row['G']}\t{row['B']}\t{row['label']}\n")
    
    print("✅ Overwritten all CSV and text files")

def create_individual_rois():
    """Create individual ROI files (overwrite existing)"""
    
    print("\n🎯 Creating Individual ROI Files...")
    
    atlas_path = Path("final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # Create main ROI directory (overwrite existing)
    roi_dir = Path("individual_rois_sequential")
    if roi_dir.exists():
        import shutil
        shutil.rmtree(roi_dir)
    roi_dir.mkdir()
    
    unique_labels = sorted(np.unique(atlas_data[atlas_data > 0]))
    
    for label in unique_labels:
        roi_mask = (atlas_data == label).astype(np.uint8)
        if np.sum(roi_mask) > 0:
            roi_img = nib.Nifti1Image(roi_mask, atlas_img.affine, atlas_img.header)
            filename = f"levtiades_roi_{label:03d}.nii.gz"
            nib.save(roi_img, roi_dir / filename)
    
    print(f"✅ Created {len(unique_labels)} ROI files in {roi_dir}")

if __name__ == "__main__":
    # Step 1: Create final atlas with hemisphere ordering
    new_atlas_data, new_atlas_img, hemisphere_map = create_final_atlas()
    
    if new_atlas_data is None:
        print("❌ Failed to create atlas!")
        exit(1)
    
    # Step 2: Validate all centroids
    validation_df = validate_all_centroids(hemisphere_map)
    
    # Step 3: Update all files
    update_all_files(hemisphere_map)
    
    # Step 4: Create individual ROIs
    create_individual_rois()
    
    print("\n✅ FINAL LEVTIADES ATLAS COMPLETE!")
    print("=" * 35)
    print("📊 Single atlas file with hemisphere ordering")
    print("📋 All files overwritten with correct data")
    print("✅ All regions validated against aligned atlases")