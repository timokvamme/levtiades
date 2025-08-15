#!/usr/bin/env python3
"""
Recreate Levtiades Atlas from aligned files and apply correct hemisphere ordering
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import pandas as pd
from scipy import ndimage

def recreate_atlas_from_aligned():
    """Recreate atlas from aligned individual atlas files"""
    
    print("🔧 RECREATING LEVTIADES ATLAS FROM ALIGNED FILES")
    print("=" * 55)
    
    aligned_dir = Path("levtiades_atlas/aligned_atlases")
    
    # Load aligned atlases
    levinson_path = aligned_dir / "levinson_aligned.nii.gz"
    tian_path = aligned_dir / "tian_aligned.nii.gz"
    destrieux_path = aligned_dir / "destrieux_aligned.nii.gz"
    
    # Load images
    lev_img = nib.load(levinson_path)
    tian_img = nib.load(tian_path)
    des_img = nib.load(destrieux_path)
    
    # Get data
    lev_data = lev_img.get_fdata().astype(int)
    tian_data = tian_img.get_fdata().astype(int)
    des_data = des_img.get_fdata().astype(int)
    
    # Create combined atlas
    combined_data = np.zeros_like(lev_data, dtype=np.int16)
    
    # Add Levinson (1-5)
    for i in range(1, 6):
        mask = lev_data == i
        combined_data[mask] = i
        print(f"   Added Levinson region {i}: {np.sum(mask)} voxels")
    
    # Add Tian (101-154 -> 6-59)
    tian_index = 6
    for i in range(1, 55):  # Tian has 54 regions
        mask = tian_data == i
        if np.any(mask):
            combined_data[mask] = 100 + i  # Store as 101-154 temporarily
            print(f"   Added Tian region {i} -> {100 + i}: {np.sum(mask)} voxels")
    
    # Add Destrieux (201+ -> 60+)
    des_index = 60
    unique_des = sorted(np.unique(des_data[des_data > 0]))
    for orig_idx in unique_des:
        mask = des_data == orig_idx
        if np.any(mask):
            combined_data[mask] = 200 + orig_idx
            print(f"   Added Destrieux region {orig_idx} -> {200 + orig_idx}: {np.sum(mask)} voxels")
    
    # Save initial combined atlas
    output_dir = Path("levtiades_atlas/final_atlas/no_overlaps")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    combined_img = nib.Nifti1Image(combined_data, lev_img.affine, lev_img.header)
    temp_path = output_dir / "levtiades_temp.nii.gz"
    nib.save(combined_img, temp_path)
    
    print(f"✅ Created temporary atlas: {temp_path}")
    
    # Now apply sequential reindexing
    print("\n🔢 Applying sequential reindexing...")
    
    # Create mapping
    sequential_data = np.zeros_like(combined_data, dtype=np.int16)
    new_index = 1
    
    # Levinson (1-5) stays the same
    for i in range(1, 6):
        mask = combined_data == i
        sequential_data[mask] = new_index
        new_index += 1
    
    # Tian (101-154) becomes sequential (6-59)
    for i in range(101, 155):
        mask = combined_data == i
        if np.any(mask):
            sequential_data[mask] = new_index
            new_index += 1
    
    # Destrieux (201+) becomes sequential (60+)
    unique_des_combined = sorted([x for x in np.unique(combined_data) if x >= 201])
    for orig_idx in unique_des_combined:
        mask = combined_data == orig_idx
        sequential_data[mask] = new_index
        new_index += 1
    
    # Save sequential atlas
    sequential_img = nib.Nifti1Image(sequential_data, lev_img.affine, lev_img.header)
    sequential_path = output_dir / "levtiades_sequential.nii.gz"
    nib.save(sequential_img, sequential_path)
    
    print(f"✅ Created sequential atlas: {sequential_path}")
    print(f"   Total regions: {len(np.unique(sequential_data[sequential_data > 0]))}")
    
    return sequential_path

if __name__ == "__main__":
    atlas_path = recreate_atlas_from_aligned()
    print(f"\n✅ Atlas recreated: {atlas_path}")