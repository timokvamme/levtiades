#!/usr/bin/env python3
"""
Create CORRECT hemisphere-ordered Levtiades Atlas
Fix Tian hemisphere assignment and validate all regions
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import pandas as pd
from scipy import ndimage
import json

def create_correct_hemisphere_atlas():
    """Create atlas with CORRECT hemisphere ordering"""
    
    print("🔄 CREATING CORRECTED HEMISPHERE LEVTIADES ATLAS")
    print("=" * 55)
    print("CORRECTING Tian hemisphere assignment:")
    print("- Tian 1-27 (indices 101-127) = RIGHT hemisphere")  
    print("- Tian 28-54 (indices 128-154) = LEFT hemisphere")
    print("Order: Levinson → Tian-LEFT → Tian-RIGHT → Destrieux-LEFT → Destrieux-RIGHT")
    print()
    
    # Load current atlas
    atlas_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # Load original mapping
    mapping_df = pd.read_csv("levtiades_atlas/index_mapping_reference.csv")
    
    # Load Tian labels to verify hemisphere assignment
    tian_labels = {}
    tian_file = Path("data/Tian2020MSA_v1.4/3T/Subcortex-Only/Tian_Subcortex_S4_3T_label.txt")
    if tian_file.exists():
        with open(tian_file, 'r') as f:
            for i, line in enumerate(f, 1):
                label = line.strip()
                if label:
                    tian_labels[i] = label
    
    # Create CORRECT hemisphere mapping
    hemisphere_map = {}
    new_index = 1
    
    print("Creating hemisphere mapping:")
    
    # 1. Levinson regions (1-5)
    levinson_rows = mapping_df[mapping_df['source'] == 'Levinson'].sort_values('new_index')
    for _, row in levinson_rows.iterrows():
        hemisphere_map[row['new_index']] = new_index
        print(f"   Levinson {row['new_index']} -> {new_index}")
        new_index += 1
    
    # 2. Tian LEFT hemisphere (original Tian indices 28-54, which are sequential indices 128-154 in old system)
    # But we need to map from current sequential numbering back to original Tian numbering
    tian_rows = mapping_df[mapping_df['source'] == 'Tian'].copy()
    
    # Add hemisphere info based on original Tian index
    tian_rows['tian_original_idx'] = tian_rows['old_index'] - 100  # Convert 101-154 to 1-54
    tian_rows['hemisphere'] = tian_rows['tian_original_idx'].apply(
        lambda x: 'left' if x >= 28 else 'right'
    )
    
    # Tian LEFT (original 28-54)
    tian_left = tian_rows[tian_rows['hemisphere'] == 'left'].sort_values('old_index')
    print(f"\n   Tian LEFT regions (original indices 28-54):")
    for _, row in tian_left.iterrows():
        tian_orig_idx = row['tian_original_idx']
        label = tian_labels.get(tian_orig_idx, f"Tian_{tian_orig_idx}")
        hemisphere_map[row['new_index']] = new_index
        print(f"     {row['new_index']} ({label}) -> {new_index}")
        new_index += 1
    
    # 3. Tian RIGHT hemisphere (original 1-27)
    tian_right = tian_rows[tian_rows['hemisphere'] == 'right'].sort_values('old_index')
    print(f"\n   Tian RIGHT regions (original indices 1-27):")
    for _, row in tian_right.iterrows():
        tian_orig_idx = row['tian_original_idx']
        label = tian_labels.get(tian_orig_idx, f"Tian_{tian_orig_idx}")
        hemisphere_map[row['new_index']] = new_index
        print(f"     {row['new_index']} ({label}) -> {new_index}")
        new_index += 1
    
    # 4. Destrieux LEFT hemisphere
    des_rows = mapping_df[mapping_df['source'] == 'Destrieux'].sort_values('new_index')
    des_left = des_rows[des_rows['region_name'].str.contains("'L ", na=False)]
    print(f"\n   Destrieux LEFT regions:")
    for _, row in des_left.iterrows():
        hemisphere_map[row['new_index']] = new_index
        new_index += 1
    print(f"     {len(des_left)} regions -> {new_index-len(des_left)}-{new_index-1}")
    
    # 5. Destrieux RIGHT hemisphere  
    des_right = des_rows[des_rows['region_name'].str.contains("'R ", na=False)]
    print(f"\n   Destrieux RIGHT regions:")
    for _, row in des_right.iterrows():
        hemisphere_map[row['new_index']] = new_index
        new_index += 1
    print(f"     {len(des_right)} regions -> {new_index-len(des_right)}-{new_index-1}")
    
    print(f"\n✅ Created CORRECTED hemisphere mapping for {len(hemisphere_map)} regions")
    
    # Apply hemisphere reordering
    print("\n🏗️ Applying CORRECTED Hemisphere Reordering...")
    new_atlas_data = np.zeros_like(atlas_data, dtype=np.int16)
    
    for old_idx, new_idx in hemisphere_map.items():
        mask = atlas_data == old_idx
        new_atlas_data[mask] = new_idx
    
    # Verify no data loss
    old_voxels = np.sum(atlas_data > 0)
    new_voxels = np.sum(new_atlas_data > 0)
    print(f"   Verification: {old_voxels} -> {new_voxels} voxels")
    
    if old_voxels != new_voxels:
        print("❌ ERROR: Voxel count mismatch!")
        return None, None
    
    # Save corrected atlas (overwrite existing)
    new_img = nib.Nifti1Image(new_atlas_data, atlas_img.affine, atlas_img.header)
    nib.save(new_img, atlas_path)
    print(f"✅ Overwritten: {atlas_path}")
    
    # Save corrected hemisphere mapping
    with open("levtiades_atlas/hemisphere_reorder_map_corrected.json", 'w') as f:
        json.dump({int(k): int(v) for k, v in hemisphere_map.items()}, f, indent=2)
    
    return new_atlas_data, new_img, hemisphere_map

def validate_corrected_atlas(hemisphere_map):
    """Validate ALL regions with corrected mapping"""
    
    print("\n🔍 VALIDATING CORRECTED ATLAS - ALL REGIONS")
    print("=" * 50)
    
    # Load atlas
    atlas_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    affine = atlas_img.affine
    
    # Get centroids from corrected atlas
    print("📍 Extracting centroids from corrected atlas...")
    corrected_centroids = {}
    unique_labels = sorted(np.unique(atlas_data[atlas_data > 0]))
    
    for label in unique_labels:
        mask = atlas_data == label
        com_voxel = ndimage.center_of_mass(mask)
        com_mni = nib.affines.apply_affine(affine, com_voxel)
        corrected_centroids[label] = com_mni
    
    print(f"✅ Extracted {len(corrected_centroids)} centroids")
    
    # Load original mapping and create reverse map
    mapping_df = pd.read_csv("levtiades_atlas/index_mapping_reference.csv")
    reverse_hemisphere = {v: k for k, v in hemisphere_map.items()}
    
    validation_results = []
    aligned_dir = Path("levtiades_atlas/aligned_atlases")
    
    # Validate ALL Levinson (1-5)
    print("\n📍 Validating ALL Levinson regions...")
    levinson_path = aligned_dir / "levinson_combined_aligned.nii.gz"
    if not levinson_path.exists():
        # Try alternative name
        levinson_path = aligned_dir / "levinson_aligned.nii.gz"
    
    if levinson_path.exists():
        lev_img = nib.load(levinson_path)
        lev_data = lev_img.get_fdata().astype(int)
        lev_affine = lev_img.affine
        
        for new_idx in range(1, 6):
            old_seq_idx = reverse_hemisphere[new_idx]
            orig_row = mapping_df[mapping_df['new_index'] == old_seq_idx].iloc[0]
            orig_idx = orig_row['old_index']
            
            mask = lev_data == orig_idx
            if np.any(mask):
                com_voxel = ndimage.center_of_mass(mask)
                com_mni = nib.affines.apply_affine(lev_affine, com_voxel)
                
                corrected_coord = corrected_centroids[new_idx]
                distance = np.sqrt(np.sum((com_mni - corrected_coord)**2))
                
                validation_results.append({
                    'final_index': new_idx,
                    'source': 'Levinson',
                    'original_x': round(com_mni[0], 1),
                    'original_y': round(com_mni[1], 1), 
                    'original_z': round(com_mni[2], 1),
                    'corrected_x': round(corrected_coord[0], 1),
                    'corrected_y': round(corrected_coord[1], 1),
                    'corrected_z': round(corrected_coord[2], 1),
                    'distance_mm': round(distance, 2),
                    'match': 'MATCH' if distance < 1.0 else 'MISMATCH'
                })
                print(f"   Levinson {new_idx}: {distance:.2f}mm")
    
    # Validate ALL Tian (6-59)
    print("\n📍 Validating ALL Tian regions...")
    tian_path = aligned_dir / "tian_aligned.nii.gz" 
    if tian_path.exists():
        tian_img = nib.load(tian_path)
        tian_data = tian_img.get_fdata().astype(int)
        tian_affine = tian_img.affine
        
        for new_idx in range(6, 60):
            old_seq_idx = reverse_hemisphere[new_idx]
            orig_row = mapping_df[mapping_df['new_index'] == old_seq_idx].iloc[0]
            orig_tian_idx = orig_row['old_index'] - 100  # Convert to 1-54
            
            mask = tian_data == orig_tian_idx
            if np.any(mask):
                com_voxel = ndimage.center_of_mass(mask)
                com_mni = nib.affines.apply_affine(tian_affine, com_voxel)
                
                corrected_coord = corrected_centroids[new_idx]
                distance = np.sqrt(np.sum((com_mni - corrected_coord)**2))
                
                validation_results.append({
                    'final_index': new_idx,
                    'source': 'Tian',
                    'original_x': round(com_mni[0], 1),
                    'original_y': round(com_mni[1], 1),
                    'original_z': round(com_mni[2], 1),
                    'corrected_x': round(corrected_coord[0], 1),
                    'corrected_y': round(corrected_coord[1], 1),
                    'corrected_z': round(corrected_coord[2], 1),
                    'distance_mm': round(distance, 2),
                    'match': 'MATCH' if distance < 1.0 else 'MISMATCH'
                })
    
    # Validate ALL Destrieux (60-207)
    print("\n📍 Validating ALL Destrieux regions...")
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
                    
                    mask = des_data == orig_des_idx
                    if np.any(mask):
                        com_voxel = ndimage.center_of_mass(mask)
                        com_mni = nib.affines.apply_affine(des_affine, com_voxel)
                        
                        corrected_coord = corrected_centroids[new_idx]
                        distance = np.sqrt(np.sum((com_mni - corrected_coord)**2))
                        
                        validation_results.append({
                            'final_index': new_idx,
                            'source': 'Destrieux',
                            'original_x': round(com_mni[0], 1),
                            'original_y': round(com_mni[1], 1),
                            'original_z': round(com_mni[2], 1),
                            'corrected_x': round(corrected_coord[0], 1),
                            'corrected_y': round(corrected_coord[1], 1),
                            'corrected_z': round(corrected_coord[2], 1),
                            'distance_mm': round(distance, 2),
                            'match': 'MATCH' if distance < 1.0 else 'MISMATCH'
                        })
    
    # Save validation results
    val_df = pd.DataFrame(validation_results)
    val_dir = Path("levtiades_atlas/centroid_validation")
    val_dir.mkdir(exist_ok=True)
    val_csv_path = val_dir / "corrected_centroid_validation.csv"
    val_df.to_csv(val_csv_path, index=False)
    
    # Summary
    total = len(validation_results)
    matches = len([r for r in validation_results if r['match'] == 'MATCH'])
    
    print(f"\n📊 CORRECTED VALIDATION SUMMARY:")
    print(f"   Total regions: {total}")
    print(f"   Perfect matches: {matches}")
    print(f"   Mismatches: {total - matches}")
    
    for source in ['Levinson', 'Tian', 'Destrieux']:
        source_results = [r for r in validation_results if r['source'] == source]
        source_matches = len([r for r in source_results if r['match'] == 'MATCH'])
        if source_results:
            print(f"   {source}: {source_matches}/{len(source_results)} matches")
    
    print(f"✅ Corrected validation saved: {val_csv_path}")
    
    return val_df

def update_corrected_files(hemisphere_map):
    """Update all files with corrected hemisphere mapping"""
    
    print("\n📋 UPDATING FILES WITH CORRECTED MAPPING...")
    
    # Load atlas
    atlas_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    affine = atlas_img.affine
    
    # Load mappings
    mapping_df = pd.read_csv("levtiades_atlas/index_mapping_reference.csv")
    
    # Load Tian labels
    tian_labels = {}
    tian_file = Path("data/Tian2020MSA_v1.4/3T/Subcortex-Only/Tian_Subcortex_S4_3T_label.txt")
    if tian_file.exists():
        with open(tian_file, 'r') as f:
            for i, line in enumerate(f, 1):
                label = line.strip()
                if label:
                    tian_labels[i] = label
    
    # Create corrected data
    reverse_hemisphere = {v: k for k, v in hemisphere_map.items()}
    corrected_data = []
    
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
                    if isinstance(name, str) and "')," in name:
                        name = name.split("'")[1]  # Extract from tuple
                
                corrected_data.append({
                    'index': new_idx,
                    'region_name': name,
                    'source_atlas': source,
                    'mni_x': round(com_mni[0], 1),
                    'mni_y': round(com_mni[1], 1),
                    'mni_z': round(com_mni[2], 1),
                    'volume_voxels': int(np.sum(mask)),
                    'volume_mm3': int(np.sum(mask)) * 8
                })
    
    # Update CSV files
    corrected_df = pd.DataFrame(corrected_data)
    
    # Coordinates CSV
    corrected_df.to_csv("levtiades_atlas/final_atlas/levtiades_regions_with_coordinates.csv", index=False)
    
    # Labels CSV
    labels_df = corrected_df[['index', 'region_name', 'source_atlas']].copy()
    labels_df.to_csv("levtiades_atlas/final_atlas/levtiades_labels.csv", index=False)
    
    # Text files
    with open("levtiades_atlas/final_atlas/levtiades_labels.txt", 'w') as f:
        f.write("# Levtiades Atlas - CORRECTED Hemisphere Ordering\\n")
        f.write("# Order: Levinson → Tian-LEFT → Tian-RIGHT → Destrieux-LEFT → Destrieux-RIGHT\\n")
        f.write("# Format: ID: Region_Name [Source_Atlas]\\n\\n")
        
        for _, row in corrected_df.iterrows():
            f.write(f"{row['index']}: {row['region_name']} [{row['source_atlas']}]\\n")
    
    print("✅ Updated all files with CORRECTED hemisphere mapping")

def create_individual_rois():
    """Create individual ROI files in 'individual_rois' folder"""
    
    print("\n🎯 Creating Individual ROI Files...")
    
    atlas_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # Create individual_rois directory (overwrite existing)
    roi_dir = Path("levtiades_atlas/individual_rois")
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
    
    print(f"✅ Created {len(unique_labels)} ROI files in individual_rois/")

if __name__ == "__main__":
    # Step 1: Create corrected hemisphere atlas
    atlas_data, atlas_img, hemisphere_map = create_correct_hemisphere_atlas()
    
    if atlas_data is None:
        print("❌ Failed to create corrected atlas!")
        exit(1)
    
    # Step 2: Validate corrected atlas
    validation_df = validate_corrected_atlas(hemisphere_map)
    
    # Step 3: Update all files
    update_corrected_files(hemisphere_map)
    
    # Step 4: Create individual ROIs
    create_individual_rois()
    
    print("\n✅ CORRECTED LEVTIADES ATLAS COMPLETE!")
    print("=" * 40)
    print("📊 Hemisphere ordering: Levinson → Tian-LEFT → Tian-RIGHT → Destrieux-LEFT → Destrieux-RIGHT")
    print("📋 All files updated with corrected hemisphere assignment")
    print("🎯 Individual ROI files created in individual_rois/")