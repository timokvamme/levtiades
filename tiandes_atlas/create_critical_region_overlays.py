#!/usr/bin/env python3
"""
Critical Region Overlays Generator
Creates specific overlays for the most problematic overlap regions identified
"""

import nibabel as nib
import numpy as np
from pathlib import Path

def create_critical_overlays():
    """Create overlays for critical regions with overlap issues"""
    
    print("🔍 CREATING CRITICAL REGION OVERLAYS")
    print("=" * 40)
    
    base_dir = Path("tiandes_atlas")
    aligned_dir = base_dir / "aligned_atlases"
    critical_dir = base_dir / "plots_4_mricrogl" / "critical_region_overlays"
    
    # Load aligned atlases
    tian_img = nib.load(aligned_dir / "tian_aligned.nii.gz")
    des_img = nib.load(aligned_dir / "destrieux_aligned.nii.gz")
    
    tian_data = tian_img.get_fdata().astype(int)
    des_data = des_img.get_fdata().astype(int)
    
    # Critical regions identified from overlap analysis
    critical_tian_regions = [21, 48, 1, 32, 28]  # Most problematic Tian regions
    critical_des_regions = [98, 23]  # Parahippocampal regions causing issues
    
    print(f"Creating overlays for {len(critical_tian_regions)} Tian + {len(critical_des_regions)} Destrieux critical regions")
    
    # 1. Create individual critical Tian region overlays
    for tian_id in critical_tian_regions:
        tian_mask = (tian_data == tian_id).astype(np.uint8) * 100
        tian_critical_img = nib.Nifti1Image(tian_mask, tian_img.affine, tian_img.header)
        nib.save(tian_critical_img, critical_dir / f"critical_tian_{tian_id:02d}.nii.gz")
        
        voxel_count = np.sum(tian_mask > 0)
        print(f"   Tian region {tian_id}: {voxel_count} voxels")
    
    # 2. Create individual critical Destrieux region overlays  
    for des_id in critical_des_regions:
        des_mask = (des_data == des_id).astype(np.uint8) * 200
        des_critical_img = nib.Nifti1Image(des_mask, des_img.affine, des_img.header)
        nib.save(des_critical_img, critical_dir / f"critical_destrieux_{des_id:03d}.nii.gz")
        
        voxel_count = np.sum(des_mask > 0)
        print(f"   Destrieux region {des_id}: {voxel_count} voxels")
    
    # 3. Create combined critical regions overlay
    critical_combined = np.zeros_like(tian_data)
    
    # Add Tian critical regions (values 100-154)
    for i, tian_id in enumerate(critical_tian_regions):
        critical_combined[tian_data == tian_id] = 100 + i
    
    # Add Destrieux critical regions (values 200-202)
    for i, des_id in enumerate(critical_des_regions):
        critical_combined[des_data == des_id] = 200 + i
    
    combined_img = nib.Nifti1Image(critical_combined.astype(np.uint8), tian_img.affine, tian_img.header)
    nib.save(combined_img, critical_dir / "all_critical_regions_combined.nii.gz")
    
    # 4. Create parahippocampal focus overlay (biggest problem area)
    parahip_focus = np.zeros_like(tian_data)
    parahip_focus[(des_data == 98) | (des_data == 23)] = 300  # Parahippocampal regions
    parahip_focus[np.isin(tian_data, [21, 48, 1, 32, 28])] = 400  # Overlapping Tian regions
    
    parahip_img = nib.Nifti1Image(parahip_focus.astype(np.uint16), tian_img.affine, tian_img.header)
    nib.save(parahip_img, critical_dir / "parahippocampal_boundary_focus.nii.gz")
    
    # 5. Create actual overlap regions overlay
    overlap_mask = (tian_data > 0) & (des_data > 0)
    overlap_regions = np.zeros_like(tian_data)
    overlap_regions[overlap_mask] = 500  # All overlaps
    
    overlap_img = nib.Nifti1Image(overlap_regions.astype(np.uint16), tian_img.affine, tian_img.header)
    nib.save(overlap_img, critical_dir / "actual_overlap_voxels.nii.gz")
    
    print(f"\n✅ Critical region overlays created:")
    print(f"   Individual Tian regions: {len(critical_tian_regions)} files")
    print(f"   Individual Destrieux regions: {len(critical_des_regions)} files") 
    print(f"   Combined critical regions: all_critical_regions_combined.nii.gz")
    print(f"   Parahippocampal focus: parahippocampal_boundary_focus.nii.gz")
    print(f"   Actual overlaps: actual_overlap_voxels.nii.gz")
    
    return len(critical_tian_regions) + len(critical_des_regions)

def create_screenshot_validation_overlay():
    """Create specific overlay matching the screenshot for validation"""
    
    print(f"\n📸 CREATING SCREENSHOT VALIDATION OVERLAY")
    print("=" * 42)
    
    base_dir = Path("tiandes_atlas")
    final_dir = base_dir / "final_atlas"
    critical_dir = base_dir / "plots_4_mricrogl" / "critical_region_overlays"
    
    # Load final atlas
    atlas_img = nib.load(final_dir / "tiandes_combined.nii.gz")
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # Create validation overlay matching screenshot view
    validation_overlay = np.zeros_like(atlas_data)
    
    # Tian subcortical (green in screenshot) - value 100
    validation_overlay[(atlas_data >= 1) & (atlas_data <= 54)] = 100
    
    # Destrieux cortical (red in screenshot) - value 200  
    validation_overlay[atlas_data > 100] = 200
    
    # Highlight specific regions visible in screenshot
    # Focus on regions that should be clearly visible in axial/sagittal views
    
    validation_img = nib.Nifti1Image(validation_overlay.astype(np.uint8), atlas_img.affine, atlas_img.header)
    nib.save(validation_img, critical_dir / "screenshot_validation_overlay.nii.gz")
    
    print(f"✅ Screenshot validation overlay created")
    print(f"   Use this to confirm anatomical placement matches your screenshot")
    
    return validation_overlay

if __name__ == "__main__":
    # Create critical region overlays
    critical_count = create_critical_overlays()
    
    # Create screenshot validation overlay
    validation_overlay = create_screenshot_validation_overlay()
    
    print(f"\n🎯 CRITICAL OVERLAYS COMPLETE")
    print("=" * 30)
    print(f"📁 Location: plots_4_mricrogl/critical_region_overlays/")
    print(f"📊 Files created: {critical_count + 3} overlay files")
    print(f"🔍 Next: Load these in MRIcrogl to validate problematic regions")