#!/usr/bin/env python3
"""
Create CSV files with proper formatting and validate region centroids
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import pandas as pd
import json
from scipy import ndimage

def fix_label_file_formatting():
    """Fix the label file formatting - replace \\n with actual newlines"""
    
    print("🔧 Fixing Label File Formatting...")
    
    # Read the problematic file
    label_path = Path("final_atlas/levtiades_labels.txt")
    with open(label_path, 'r') as f:
        content = f.read()
    
    # Replace literal \\n with actual newlines
    fixed_content = content.replace('\\n', '\n')
    
    # Write back with proper newlines
    with open(label_path, 'w') as f:
        f.write(fixed_content)
    
    print("✅ Fixed label file formatting")
    
    # Do the same for lookup table
    lookup_path = Path("levtiades_atlas/final_atlas/levtiades_lookup_table.txt")
    with open(lookup_path, 'r') as f:
        content = f.read()
    
    fixed_content = content.replace('\\n', '\n').replace('\\t', '\t')
    
    with open(lookup_path, 'w') as f:
        f.write(fixed_content)
    
    print("✅ Fixed lookup table formatting")

def rename_atlas_files():
    """Rename fixed to hierarchical"""
    
    print("\n📁 Renaming Atlas Files...")
    
    atlas_dir = Path("levtiades_atlas/final_atlas/no_overlaps")
    
    # Check what files exist
    fixed_path = atlas_dir / "levtiades_hierarchical_fixed.nii.gz"
    hierarchical_path = atlas_dir / "levtiades_hierarchical.nii.gz"
    
    if fixed_path.exists():
        # Rename fixed to hierarchical (overwrite if exists)
        if hierarchical_path.exists():
            hierarchical_path.unlink()
        fixed_path.rename(hierarchical_path)
        print(f"✅ Renamed {fixed_path.name} to {hierarchical_path.name}")

def extract_region_centroids(atlas_path):
    """Extract centroid coordinates for each region"""
    
    print(f"\n📍 Extracting Region Centroids from {atlas_path.name}...")
    
    # Load atlas
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    affine = atlas_img.affine
    
    # Get unique labels
    unique_labels = sorted(np.unique(atlas_data[atlas_data > 0]))
    
    centroids = {}
    
    for label in unique_labels:
        # Get mask for this region
        mask = atlas_data == label
        
        # Calculate center of mass in voxel coordinates
        com_voxel = ndimage.center_of_mass(mask)
        
        # Convert to MNI coordinates
        com_mni = nib.affines.apply_affine(affine, com_voxel)
        
        centroids[label] = {
            'voxel_x': com_voxel[0],
            'voxel_y': com_voxel[1],
            'voxel_z': com_voxel[2],
            'mni_x': com_mni[0],
            'mni_y': com_mni[1],
            'mni_z': com_mni[2],
            'volume_voxels': int(np.sum(mask))
        }
        
        if label % 50 == 0:
            print(f"   Processed {label}/{len(unique_labels)} regions...")
    
    print(f"✅ Extracted centroids for {len(centroids)} regions")
    return centroids

def create_labels_csv():
    """Create CSV version of labels with proper formatting"""
    
    print("\n📋 Creating Labels CSV...")
    
    # Read the fixed label file
    label_path = Path("levtiades_atlas/final_atlas/levtiades_labels.txt")
    
    labels_data = []
    
    with open(label_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and ':' in line:
                # Parse format: "1: Locus_Coeruleus_LC [Levinson-Bari]"
                parts = line.split(':', 1)
                index = int(parts[0])
                
                # Extract name and source
                name_part = parts[1].strip()
                if '[' in name_part and ']' in name_part:
                    name = name_part[:name_part.rfind('[')].strip()
                    source = name_part[name_part.rfind('[')+1:-1]
                else:
                    name = name_part
                    source = "Unknown"
                
                labels_data.append({
                    'index': index,
                    'region_name': name,
                    'source_atlas': source
                })
    
    # Create DataFrame
    labels_df = pd.DataFrame(labels_data)
    
    # Save CSV
    csv_path = Path("levtiades_atlas/final_atlas/levtiades_labels.csv")
    labels_df.to_csv(csv_path, index=False)
    
    print(f"✅ Created labels CSV: {csv_path}")
    return labels_df

def create_lookup_table_csv():
    """Create CSV version of lookup table"""
    
    print("\n🎨 Creating Lookup Table CSV...")
    
    # Read the fixed lookup table
    lookup_path = Path("levtiades_atlas/final_atlas/levtiades_lookup_table.txt")
    
    lookup_data = []
    
    with open(lookup_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '\t' in line:
                # Parse format: "1\t235\t130\t50\tLevinson:Locus_Coeruleus_LC"
                parts = line.split('\t')
                if len(parts) >= 5:
                    lookup_data.append({
                        'index': int(parts[0]),
                        'R': int(parts[1]),
                        'G': int(parts[2]),
                        'B': int(parts[3]),
                        'label': parts[4]
                    })
    
    # Create DataFrame
    lookup_df = pd.DataFrame(lookup_data)
    
    # Save CSV
    csv_path = Path("levtiades_atlas/final_atlas/levtiades_lookup_table.csv")
    lookup_df.to_csv(csv_path, index=False)
    
    print(f"✅ Created lookup table CSV: {csv_path}")
    return lookup_df

def create_regions_with_coordinates_csv(labels_df, centroids):
    """Create comprehensive CSV with labels and coordinates"""
    
    print("\n🌍 Creating Regions with Coordinates CSV...")
    
    # Merge labels with centroids
    regions_data = []
    
    for _, row in labels_df.iterrows():
        index = row['index']
        if index in centroids:
            region_info = {
                'index': index,
                'region_name': row['region_name'],
                'source_atlas': row['source_atlas'],
                'mni_x': round(centroids[index]['mni_x'], 1),
                'mni_y': round(centroids[index]['mni_y'], 1),
                'mni_z': round(centroids[index]['mni_z'], 1),
                'volume_voxels': centroids[index]['volume_voxels'],
                'volume_mm3': centroids[index]['volume_voxels'] * 8  # 2x2x2mm voxels
            }
            regions_data.append(region_info)
    
    # Create DataFrame
    regions_df = pd.DataFrame(regions_data)
    
    # Save CSV
    csv_path = Path("levtiades_atlas/final_atlas/levtiades_regions_with_coordinates.csv")
    regions_df.to_csv(csv_path, index=False)
    
    print(f"✅ Created regions with coordinates CSV: {csv_path}")
    return regions_df

def validate_centroids_across_atlases():
    """Validate that centroids match between sequential and original atlases"""
    
    print("\n🔍 VALIDATING REGION CENTROIDS ACROSS ATLASES")
    print("=" * 50)
    
    # Create validation directory
    val_dir = Path("levtiades_atlas/centroid_validation")
    val_dir.mkdir(exist_ok=True)
    
    # Load reindexing map
    with open("levtiades_atlas/reindexing_map.json", 'r') as f:
        reindex_map = json.load(f)
    reindex_map = {int(k): v for k, v in reindex_map.items()}
    
    # Load sequential atlas centroids
    seq_atlas_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    seq_centroids = extract_region_centroids(seq_atlas_path)
    
    # Load original aligned atlases
    aligned_dir = Path("levtiades_atlas/aligned_atlases")
    
    validation_results = []
    
    # 1. Validate Levinson regions (1-5)
    print("\n📍 Validating Levinson Regions...")
    levinson_path = aligned_dir / "levinson_combined_aligned.nii.gz"
    if levinson_path.exists():
        levinson_img = nib.load(levinson_path)
        levinson_data = levinson_img.get_fdata().astype(int)
        levinson_affine = levinson_img.affine
        
        for old_idx in range(1, 6):
            if old_idx in reindex_map:
                new_idx = reindex_map[old_idx]
                
                # Get centroid from original Levinson
                mask = levinson_data == old_idx
                if np.any(mask):
                    com_voxel = ndimage.center_of_mass(mask)
                    com_mni = nib.affines.apply_affine(levinson_affine, com_voxel)
                    
                    # Compare with sequential atlas
                    seq_coord = seq_centroids.get(new_idx, {})
                    
                    if seq_coord:
                        distance = np.sqrt(
                            (com_mni[0] - seq_coord['mni_x'])**2 +
                            (com_mni[1] - seq_coord['mni_y'])**2 +
                            (com_mni[2] - seq_coord['mni_z'])**2
                        )
                        
                        validation_results.append({
                            'source': 'Levinson',
                            'old_index': old_idx,
                            'new_index': new_idx,
                            'original_x': round(com_mni[0], 1),
                            'original_y': round(com_mni[1], 1),
                            'original_z': round(com_mni[2], 1),
                            'sequential_x': round(seq_coord['mni_x'], 1),
                            'sequential_y': round(seq_coord['mni_y'], 1),
                            'sequential_z': round(seq_coord['mni_z'], 1),
                            'distance_mm': round(distance, 2),
                            'match_status': 'MATCH' if distance < 2.0 else 'MISMATCH'
                        })
    
    # 2. Validate Tian regions (101-154 -> 6-59)
    print("\n📍 Validating Tian Regions...")
    tian_path = aligned_dir / "tian_aligned.nii.gz"
    if tian_path.exists():
        tian_img = nib.load(tian_path)
        tian_data = tian_img.get_fdata().astype(int)
        tian_affine = tian_img.affine
        
        for original_tian_idx in range(1, 55):  # Tian uses 1-54
            old_idx = original_tian_idx + 100  # Our mapping uses 101-154
            if old_idx in reindex_map:
                new_idx = reindex_map[old_idx]
                
                # Get centroid from original Tian
                mask = tian_data == original_tian_idx
                if np.any(mask):
                    com_voxel = ndimage.center_of_mass(mask)
                    com_mni = nib.affines.apply_affine(tian_affine, com_voxel)
                    
                    # Compare with sequential atlas
                    seq_coord = seq_centroids.get(new_idx, {})
                    
                    if seq_coord:
                        distance = np.sqrt(
                            (com_mni[0] - seq_coord['mni_x'])**2 +
                            (com_mni[1] - seq_coord['mni_y'])**2 +
                            (com_mni[2] - seq_coord['mni_z'])**2
                        )
                        
                        validation_results.append({
                            'source': 'Tian',
                            'old_index': old_idx,
                            'new_index': new_idx,
                            'original_x': round(com_mni[0], 1),
                            'original_y': round(com_mni[1], 1),
                            'original_z': round(com_mni[2], 1),
                            'sequential_x': round(seq_coord['mni_x'], 1),
                            'sequential_y': round(seq_coord['mni_y'], 1),
                            'sequential_z': round(seq_coord['mni_z'], 1),
                            'distance_mm': round(distance, 2),
                            'match_status': 'MATCH' if distance < 2.0 else 'MISMATCH'
                        })
    
    # 3. Validate Destrieux regions (sample check)
    print("\n📍 Validating Destrieux Regions (sample)...")
    destrieux_path = aligned_dir / "destrieux_aligned.nii.gz"
    if destrieux_path.exists():
        des_img = nib.load(destrieux_path)
        des_data = des_img.get_fdata().astype(int)
        des_affine = des_img.affine
        
        # Check first 10 and last 10 Destrieux regions
        des_indices_to_check = list(range(1, 11)) + list(range(140, 151))
        
        for original_des_idx in des_indices_to_check:
            if original_des_idx not in [0, 42, 117]:  # Skip removed regions
                old_idx = original_des_idx + 200  # Our mapping uses 201+
                if old_idx in reindex_map:
                    new_idx = reindex_map[old_idx]
                    
                    # Get centroid from original Destrieux
                    mask = des_data == original_des_idx
                    if np.any(mask):
                        com_voxel = ndimage.center_of_mass(mask)
                        com_mni = nib.affines.apply_affine(des_affine, com_voxel)
                        
                        # Compare with sequential atlas
                        seq_coord = seq_centroids.get(new_idx, {})
                        
                        if seq_coord:
                            distance = np.sqrt(
                                (com_mni[0] - seq_coord['mni_x'])**2 +
                                (com_mni[1] - seq_coord['mni_y'])**2 +
                                (com_mni[2] - seq_coord['mni_z'])**2
                            )
                            
                            validation_results.append({
                                'source': 'Destrieux',
                                'old_index': old_idx,
                                'new_index': new_idx,
                                'original_x': round(com_mni[0], 1),
                                'original_y': round(com_mni[1], 1),
                                'original_z': round(com_mni[2], 1),
                                'sequential_x': round(seq_coord['mni_x'], 1),
                                'sequential_y': round(seq_coord['mni_y'], 1),
                                'sequential_z': round(seq_coord['mni_z'], 1),
                                'distance_mm': round(distance, 2),
                                'match_status': 'MATCH' if distance < 2.0 else 'MISMATCH'
                            })
    
    # Save validation results
    val_df = pd.DataFrame(validation_results)
    val_csv_path = val_dir / "centroid_validation_results.csv"
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
    
    if mismatches > 0:
        print(f"\n⚠️  Found {mismatches} mismatches - check validation CSV for details")
    else:
        print("\n✅ All checked regions have matching centroids!")
    
    # Create summary report
    report_path = val_dir / "validation_report.txt"
    with open(report_path, 'w') as f:
        f.write("LEVTIADES ATLAS CENTROID VALIDATION REPORT\n")
        f.write("=========================================\n\n")
        f.write(f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Sequential Atlas: {seq_atlas_path}\n\n")
        f.write("SUMMARY:\n")
        f.write(f"- Total regions checked: {total_checked}\n")
        f.write(f"- Matching centroids (< 2mm): {matches}\n")
        f.write(f"- Mismatched centroids (≥ 2mm): {mismatches}\n\n")
        
        if mismatches > 0:
            f.write("MISMATCHED REGIONS:\n")
            for _, row in val_df[val_df['match_status'] == 'MISMATCH'].iterrows():
                f.write(f"- {row['source']} region {row['old_index']} -> {row['new_index']}: ")
                f.write(f"{row['distance_mm']}mm difference\n")
    
    print(f"✅ Validation report saved: {report_path}")
    
    return val_df

if __name__ == "__main__":
    print("🚀 CREATING CSV FILES AND VALIDATING LEVTIADES ATLAS")
    print("=" * 55)
    
    # Step 1: Fix formatting
    fix_label_file_formatting()
    
    # Step 2: Rename atlas files
    rename_atlas_files()
    
    # Step 3: Extract centroids from sequential atlas
    seq_atlas_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    centroids = extract_region_centroids(seq_atlas_path)
    
    # Step 4: Create CSV files
    labels_df = create_labels_csv()
    lookup_df = create_lookup_table_csv()
    regions_df = create_regions_with_coordinates_csv(labels_df, centroids)
    
    # Step 5: Validate centroids
    validation_df = validate_centroids_across_atlases()
    
    print("\n✅ ALL TASKS COMPLETE!")
    print("=" * 25)
    print("📋 CSV Files Created:")
    print("   - levtiades_labels.csv")
    print("   - levtiades_lookup_table.csv")
    print("   - levtiades_regions_with_coordinates.csv")
    print("📁 Validation Results:")
    print("   - centroid_validation/")
    print("🧠 Atlas ready for use!")