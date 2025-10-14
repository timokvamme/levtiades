#!/usr/bin/env python3
"""
Fix Sequential ROI Creation
Create all 207 individual ROI files from the sequential atlas
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import json

def fix_sequential_rois():
    """Create all 207 individual ROI files from sequential atlas"""
    
    print("🔧 Fixing Sequential Individual ROI Files...")
    
    # Load the sequential atlas
    atlas_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # Get all unique labels
    unique_labels = sorted(np.unique(atlas_data[atlas_data > 0]))
    print(f"   Found {len(unique_labels)} unique labels in sequential atlas")
    print(f"   Range: {min(unique_labels)} to {max(unique_labels)}")
    
    # Create output directory
    roi_dir = Path("levtiades_atlas/individual_rois_sequential")
    roi_dir.mkdir(exist_ok=True)
    
    # Remove existing files first
    for existing_file in roi_dir.glob("*.nii.gz"):
        existing_file.unlink()
    
    # Create ROI files for each region
    created_count = 0
    for label in unique_labels:
        # Create binary mask for this region
        roi_mask = (atlas_data == label).astype(np.uint8)
        voxel_count = np.sum(roi_mask)
        
        if voxel_count > 0:  # Only create files for regions that exist
            roi_img = nib.Nifti1Image(roi_mask, atlas_img.affine, atlas_img.header)
            
            # Create filename with sequential index
            filename = f"levtiades_roi_{label:03d}.nii.gz"
            output_path = roi_dir / filename
            nib.save(roi_img, output_path)
            created_count += 1
            
            if label % 50 == 0:
                print(f"   Created {created_count} ROI files... (current: {label})")
    
    print(f"✅ Created {created_count} sequential ROI files")
    
    # Verify we have all expected files
    roi_files = sorted(roi_dir.glob("*.nii.gz"))
    print(f"   Verified: {len(roi_files)} ROI files in directory")
    
    if len(roi_files) != len(unique_labels):
        print(f"⚠️  Warning: Expected {len(unique_labels)} files, found {len(roi_files)}")
    else:
        print("✅ All ROI files created successfully!")

if __name__ == "__main__":
    fix_sequential_rois()