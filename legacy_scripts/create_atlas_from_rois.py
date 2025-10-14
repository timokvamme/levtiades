#!/usr/bin/env python3
"""
Create atlas file from individual ROI files
"""

import nibabel as nib
import numpy as np
from pathlib import Path

def create_atlas_from_rois():
    """Create single atlas file from individual ROI files"""
    
    print("🔧 Creating atlas from individual ROI files...")
    
    roi_dir = Path("levtiades_atlas/individual_rois_sequential")
    roi_files = sorted(roi_dir.glob("levtiades_roi_*.nii.gz"))
    
    if not roi_files:
        print("❌ No ROI files found!")
        return
    
    print(f"   Found {len(roi_files)} ROI files")
    
    # Load first ROI to get dimensions
    first_roi = nib.load(roi_files[0])
    atlas_shape = first_roi.shape
    affine = first_roi.affine
    header = first_roi.header
    
    # Create empty atlas
    atlas_data = np.zeros(atlas_shape, dtype=np.int16)
    
    # Load each ROI and add to atlas
    for roi_file in roi_files:
        # Extract ROI number from filename
        roi_num = int(roi_file.name.split('_')[-1].split('.')[0])
        
        # Load ROI
        roi_img = nib.load(roi_file)
        roi_data = roi_img.get_fdata()
        
        # Add to atlas (ROI data should be binary 0/1)
        mask = roi_data > 0
        atlas_data[mask] = roi_num
        
        if roi_num % 50 == 0:
            print(f"   Processed ROI {roi_num}")
    
    # Save atlas
    output_dir = Path("levtiades_atlas/final_atlas/no_overlaps")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    atlas_img = nib.Nifti1Image(atlas_data, affine, header)
    output_path = output_dir / "levtiades_sequential.nii.gz"
    nib.save(atlas_img, output_path)
    
    print(f"✅ Created atlas: {output_path}")
    print(f"   Atlas contains {len(np.unique(atlas_data[atlas_data > 0]))} regions")
    
    return output_path

if __name__ == "__main__":
    create_atlas_from_rois()