#!/usr/bin/env python3
"""
Complete validation and ROI creation for hemisphere-ordered Levtiades Atlas
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import pandas as pd
from scipy import ndimage

def validate_all_centroids():
    """Validate ALL 207 region centroids against original atlases"""
    
    print("🔍 VALIDATING ALL 207 REGION CENTROIDS")
    print("=" * 45)
    
    # Create validation directory
    val_dir = Path("levtiades_atlas/centroid_validation")
    val_dir.mkdir(exist_ok=True)
    
    # Load hemisphere reordering map
    reorder_map_path = Path("levtiades_atlas/hemisphere_reorder_map.json")
    if reorder_map_path.exists():
        import json
        with open(reorder_map_path, 'r') as f:
            reorder_map = json.load(f)
        reorder_map = {int(k): int(v) for k, v in reorder_map.items()}
        print(f"   Using hemisphere reordering map: {len(reorder_map)} regions")
        # Create reverse map: new_idx -> old_idx
        reverse_reorder = {v: k for k, v in reorder_map.items()}
    else:
        # If no reorder map, assume identity mapping
        print("   No reorder map found, using sequential mapping")
        reverse_reorder = {i: i for i in range(1, 208)}
    
    # Load original index mapping
    original_mapping = pd.read_csv("levtiades_atlas/index_mapping_reference.csv")
    
    # Load current hemisphere-ordered atlas
    seq_atlas_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    seq_img = nib.load(seq_atlas_path)
    seq_data = seq_img.get_fdata().astype(int)
    seq_affine = seq_img.affine
    
    # Get centroids from current atlas
    print("\n📍 Extracting centroids from hemisphere-ordered atlas...")
    seq_centroids = {}
    unique_labels = sorted(np.unique(seq_data[seq_data > 0]))
    
    for label in unique_labels:
        mask = seq_data == label
        com_voxel = ndimage.center_of_mass(mask)
        com_mni = nib.affines.apply_affine(seq_affine, com_voxel)
        seq_centroids[label] = com_mni
        
        if label % 50 == 0:
            print(f"   Processed {label}/{len(unique_labels)} regions...")
    
    print(f"✅ Extracted centroids for {len(seq_centroids)} regions")
    
    # Validation results
    validation_results = []
    
    # Load original aligned atlases
    aligned_dir = Path("levtiades_atlas/aligned_atlases")
    
    # Validate Levinson (1-5)
    print("\n📍 Validating ALL Levinson Regions...")
    levinson_path = aligned_dir / "levinson_combined_aligned.nii.gz"
    if levinson_path.exists():
        levinson_img = nib.load(levinson_path)
        levinson_data = levinson_img.get_fdata().astype(int)
        levinson_affine = levinson_img.affine
        
        for new_idx in range(1, 6):  # Levinson regions are 1-5
            if new_idx in reverse_reorder:
                old_sequential_idx = reverse_reorder[new_idx]
                
                # Find original index
                orig_row = original_mapping[original_mapping['new_index'] == old_sequential_idx]
                if not orig_row.empty:
                    orig_old_idx = orig_row.iloc[0]['old_index']
                    
                    mask = levinson_data == orig_old_idx
                    if np.any(mask):
                        com_voxel = ndimage.center_of_mass(mask)
                        com_mni = nib.affines.apply_affine(levinson_affine, com_voxel)
                        
                        seq_coord = seq_centroids.get(new_idx)
                        if seq_coord is not None:
                            distance = np.sqrt(np.sum((com_mni - seq_coord)**2))
                            
                            validation_results.append({
                                'source': 'Levinson',
                                'original_index': orig_old_idx,
                                'old_sequential_index': old_sequential_idx,
                                'new_hemisphere_index': new_idx,
                                'original_x': round(com_mni[0], 1),
                                'original_y': round(com_mni[1], 1),
                                'original_z': round(com_mni[2], 1),
                                'sequential_x': round(seq_coord[0], 1),
                                'sequential_y': round(seq_coord[1], 1),
                                'sequential_z': round(seq_coord[2], 1),
                                'distance_mm': round(distance, 2),
                                'match_status': 'MATCH' if distance < 2.0 else 'MISMATCH'
                            })
    
    # Validate ALL Tian (6-59)
    print("\n📍 Validating ALL Tian Regions...")
    tian_path = aligned_dir / "tian_aligned.nii.gz"
    if tian_path.exists():
        tian_img = nib.load(tian_path)
        tian_data = tian_img.get_fdata().astype(int)
        tian_affine = tian_img.affine
        
        for new_idx in range(6, 60):  # Tian regions are 6-59
            if new_idx in reverse_reorder:
                old_sequential_idx = reverse_reorder[new_idx]
                
                # Find original index
                orig_row = original_mapping[original_mapping['new_index'] == old_sequential_idx]
                if not orig_row.empty:
                    orig_old_idx = orig_row.iloc[0]['old_index']
                    original_tian_idx = orig_old_idx - 100  # Convert back to 1-54
                    
                    mask = tian_data == original_tian_idx
                    if np.any(mask):
                        com_voxel = ndimage.center_of_mass(mask)
                        com_mni = nib.affines.apply_affine(tian_affine, com_voxel)
                        
                        seq_coord = seq_centroids.get(new_idx)
                        if seq_coord is not None:
                            distance = np.sqrt(np.sum((com_mni - seq_coord)**2))
                            
                            validation_results.append({
                                'source': 'Tian',
                                'original_index': original_tian_idx,
                                'old_sequential_index': old_sequential_idx,
                                'new_hemisphere_index': new_idx,
                                'original_x': round(com_mni[0], 1),
                                'original_y': round(com_mni[1], 1),
                                'original_z': round(com_mni[2], 1),
                                'sequential_x': round(seq_coord[0], 1),
                                'sequential_y': round(seq_coord[1], 1),
                                'sequential_z': round(seq_coord[2], 1),
                                'distance_mm': round(distance, 2),
                                'match_status': 'MATCH' if distance < 2.0 else 'MISMATCH'
                            })
    
    # Validate ALL Destrieux (60-207)
    print("\n📍 Validating ALL Destrieux Regions...")
    destrieux_path = aligned_dir / "destrieux_aligned.nii.gz"
    if destrieux_path.exists():
        des_img = nib.load(destrieux_path)
        des_data = des_img.get_fdata().astype(int)
        des_affine = des_img.affine
        
        for new_idx in range(60, 208):  # Destrieux regions are 60-207
            if new_idx in reverse_reorder:
                old_sequential_idx = reverse_reorder[new_idx]
                
                # Find original index
                orig_row = original_mapping[original_mapping['new_index'] == old_sequential_idx]
                if not orig_row.empty:
                    orig_old_idx = orig_row.iloc[0]['old_index']
                    original_des_idx = orig_old_idx - 200  # Convert back to original Destrieux index
                    
                    mask = des_data == original_des_idx
                    if np.any(mask):
                        com_voxel = ndimage.center_of_mass(mask)
                        com_mni = nib.affines.apply_affine(des_affine, com_voxel)
                        
                        seq_coord = seq_centroids.get(new_idx)
                        if seq_coord is not None:
                            distance = np.sqrt(np.sum((com_mni - seq_coord)**2))
                            
                            validation_results.append({
                                'source': 'Destrieux',
                                'original_index': original_des_idx,
                                'old_sequential_index': old_sequential_idx,
                                'new_hemisphere_index': new_idx,
                                'original_x': round(com_mni[0], 1),
                                'original_y': round(com_mni[1], 1),
                                'original_z': round(com_mni[2], 1),
                                'sequential_x': round(seq_coord[0], 1),
                                'sequential_y': round(seq_coord[1], 1),
                                'sequential_z': round(seq_coord[2], 1),
                                'distance_mm': round(distance, 2),
                                'match_status': 'MATCH' if distance < 2.0 else 'MISMATCH'
                            })
    
    # Save validation results
    val_df = pd.DataFrame(validation_results)
    val_csv_path = val_dir / "hemisphere_centroid_validation_all.csv"
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
        if len(source_results) > 0:
            print(f"   {source}: {source_matches}/{len(source_results)} matches")
    
    # Create summary report
    report_path = val_dir / "hemisphere_validation_report_all.txt"
    with open(report_path, 'w') as f:
        f.write("LEVTIADES ATLAS HEMISPHERE VALIDATION REPORT - ALL REGIONS\n")
        f.write("=========================================================\n\n")
        f.write(f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Atlas: {seq_atlas_path}\n")
        f.write(f"Hemisphere Ordering: Levinson → Tian-LH → Tian-RH → Destrieux-LH → Destrieux-RH\n\n")
        f.write("SUMMARY:\n")
        f.write(f"- Total regions checked: {total_checked}\n")
        f.write(f"- Matching centroids (< 2mm): {matches}\n")
        f.write(f"- Mismatched centroids (≥ 2mm): {mismatches}\n\n")
        
        f.write("BY SOURCE:\n")
        for source in ['Levinson', 'Tian', 'Destrieux']:
            source_results = [r for r in validation_results if r['source'] == source]
            source_matches = len([r for r in source_results if r['match_status'] == 'MATCH'])
            if len(source_results) > 0:
                f.write(f"- {source}: {source_matches}/{len(source_results)} matches\n")
        
        if mismatches > 0:
            f.write("\nMISMATCHED REGIONS:\n")
            for _, row in val_df[val_df['match_status'] == 'MISMATCH'].iterrows():
                f.write(f"- {row['source']} region {row['new_hemisphere_index']}: ")
                f.write(f"{row['distance_mm']}mm difference\n")
    
    print(f"✅ Validation report saved: {report_path}")
    
    return val_df

def create_hemisphere_individual_rois():
    """Create individual ROI files with hemisphere ordering"""
    
    print("\n🎯 Creating Individual ROI Files with Hemisphere Ordering...")
    
    # Load the hemisphere-ordered atlas
    atlas_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # Create output directory
    roi_dir = Path("levtiades_atlas/individual_rois_hemisphere_ordered")
    roi_dir.mkdir(exist_ok=True)
    
    # Remove existing files
    for existing_file in roi_dir.glob("*.nii.gz"):
        existing_file.unlink()
    
    # Get unique labels
    unique_labels = sorted(np.unique(atlas_data[atlas_data > 0]))
    print(f"   Creating {len(unique_labels)} ROI files...")
    
    # Create ROI files
    created_count = 0
    for label in unique_labels:
        # Create binary mask
        roi_mask = (atlas_data == label).astype(np.uint8)
        voxel_count = np.sum(roi_mask)
        
        if voxel_count > 0:
            roi_img = nib.Nifti1Image(roi_mask, atlas_img.affine, atlas_img.header)
            
            # Determine category for filename
            if label <= 5:
                category = "midbrain"
                name = f"levinson_{label:03d}"
            elif label <= 32:
                category = "subcortical_left"
                name = f"tian_left_{label:03d}"
            elif label <= 59:
                category = "subcortical_right"
                name = f"tian_right_{label:03d}"
            elif label <= 133:
                category = "cortical_left"
                name = f"destrieux_left_{label:03d}"
            else:
                category = "cortical_right"
                name = f"destrieux_right_{label:03d}"
            
            # Create category subdirectory
            category_dir = roi_dir / category
            category_dir.mkdir(exist_ok=True)
            
            # Save ROI file
            filename = f"{name}.nii.gz"
            output_path = category_dir / filename
            nib.save(roi_img, output_path)
            created_count += 1
            
            if label % 50 == 0:
                print(f"   Created {created_count} ROI files... (current: {label})")
    
    print(f"✅ Created {created_count} hemisphere-ordered ROI files")
    
    # Create summary of categories
    categories = ["midbrain", "subcortical_left", "subcortical_right", "cortical_left", "cortical_right"]
    for category in categories:
        category_dir = roi_dir / category
        if category_dir.exists():
            file_count = len(list(category_dir.glob("*.nii.gz")))
            print(f"   {category}: {file_count} files")

if __name__ == "__main__":
    print("🚀 COMPLETE VALIDATION AND ROI CREATION")
    print("=" * 40)
    
    # Step 1: Validate all centroids
    validation_df = validate_all_centroids()
    
    # Step 2: Create individual ROI files
    create_hemisphere_individual_rois()
    
    print("\n✅ VALIDATION AND ROI CREATION COMPLETE!")
    print("=" * 40)
    print("📊 All regions validated against original atlases")
    print("🎯 Individual ROI files created with hemisphere ordering")