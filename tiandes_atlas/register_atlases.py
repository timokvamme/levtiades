#!/usr/bin/env python3
"""
Atlas Registration Script for TianDes Project
Aligns Tian subcortical and Destrieux cortical atlases to the same spatial reference
"""

import os
import nibabel as nib
import numpy as np
from nilearn import image
from pathlib import Path

def register_atlases():
    """Register Destrieux to Tian space for spatial compatibility"""
    
    print("🔄 ATLAS REGISTRATION")
    print("=" * 30)
    
    # File paths
    base_dir = Path("tiandes_atlas")
    raw_dir = base_dir / "raw_atlases"
    aligned_dir = base_dir / "aligned_atlases"
    
    tian_path = raw_dir / "tian_subcortical.nii.gz"
    destrieux_path = raw_dir / "destrieux_cortical.nii.gz"
    
    # Load atlases
    print("📂 Loading atlases...")
    tian_img = nib.load(tian_path)
    destrieux_img = nib.load(destrieux_path)
    
    print(f"   Tian (reference): {tian_img.shape}, {tian_img.header.get_zooms()[:3]} mm")
    print(f"   Destrieux (to align): {destrieux_img.shape}, {destrieux_img.header.get_zooms()[:3]} mm")
    
    # Check if alignment is needed
    shape_match = tian_img.shape == destrieux_img.shape
    affine_match = np.allclose(tian_img.affine, destrieux_img.affine, atol=1e-3)
    
    if shape_match and affine_match:
        print("✅ Atlases already aligned!")
        # Just copy files
        nib.save(tian_img, aligned_dir / "tian_aligned.nii.gz")
        nib.save(destrieux_img, aligned_dir / "destrieux_aligned.nii.gz")
        return str(aligned_dir / "tian_aligned.nii.gz"), str(aligned_dir / "destrieux_aligned.nii.gz")
    
    print("🎯 Resampling Destrieux to match Tian space...")
    
    # Resample Destrieux to Tian space (using nearest neighbor to preserve integer labels)
    destrieux_resampled = image.resample_to_img(
        destrieux_img, 
        tian_img,
        interpolation='nearest'  # Critical: preserves integer region labels
    )
    
    # Save aligned atlases
    print("💾 Saving aligned atlases...")
    nib.save(tian_img, aligned_dir / "tian_aligned.nii.gz")
    nib.save(destrieux_resampled, aligned_dir / "destrieux_aligned.nii.gz")
    
    # Verify alignment
    print("\n✅ ALIGNMENT VERIFICATION")
    print("-" * 25)
    
    tian_aligned = nib.load(aligned_dir / "tian_aligned.nii.gz")
    des_aligned = nib.load(aligned_dir / "destrieux_aligned.nii.gz")
    
    print(f"Tian aligned:      {tian_aligned.shape}")
    print(f"Destrieux aligned: {des_aligned.shape}")
    print(f"Shape match:       {tian_aligned.shape == des_aligned.shape}")
    print(f"Affine match:      {np.allclose(tian_aligned.affine, des_aligned.affine)}")
    
    # Check data integrity
    tian_data = tian_aligned.get_fdata()
    des_data = des_aligned.get_fdata()
    
    print(f"\nData integrity:")
    print(f"Tian regions:      {len(np.unique(tian_data[tian_data > 0]))}")
    print(f"Destrieux regions: {len(np.unique(des_data[des_data > 0]))}")
    
    return str(aligned_dir / "tian_aligned.nii.gz"), str(aligned_dir / "destrieux_aligned.nii.gz")

def create_alignment_report():
    """Generate detailed alignment report"""
    
    print("\n📋 CREATING ALIGNMENT REPORT")
    print("=" * 35)
    
    base_dir = Path("tiandes_atlas")
    aligned_dir = base_dir / "aligned_atlases"
    
    # Load aligned atlases
    tian_img = nib.load(aligned_dir / "tian_aligned.nii.gz")
    des_img = nib.load(aligned_dir / "destrieux_aligned.nii.gz")
    
    tian_data = tian_img.get_fdata()
    des_data = des_img.get_fdata()
    
    # Generate report
    report_path = base_dir / "alignment_report.txt"
    with open(report_path, 'w') as f:
        f.write("TIANDES ATLAS ALIGNMENT REPORT\n")
        f.write("=" * 40 + "\n\n")
        
        f.write("SPATIAL PROPERTIES:\n")
        f.write(f"Shape: {tian_img.shape}\n")
        f.write(f"Voxel size: {tian_img.header.get_zooms()[:3]} mm\n")
        f.write(f"Orientation: {nib.aff2axcodes(tian_img.affine)}\n\n")
        
        f.write("TIAN SUBCORTICAL (S4):\n")
        f.write(f"Total regions: {len(np.unique(tian_data[tian_data > 0]))}\n")
        f.write(f"Label range: {int(tian_data.min())} - {int(tian_data.max())}\n")
        f.write(f"Non-zero voxels: {np.sum(tian_data > 0)}\n\n")
        
        f.write("DESTRIEUX CORTICAL:\n")
        f.write(f"Total regions: {len(np.unique(des_data[des_data > 0]))}\n")
        f.write(f"Label range: {int(des_data.min())} - {int(des_data.max())}\n")
        f.write(f"Non-zero voxels: {np.sum(des_data > 0)}\n\n")
        
        f.write("OVERLAP CHECK:\n")
        overlap_voxels = np.sum((tian_data > 0) & (des_data > 0))
        f.write(f"Overlapping voxels: {overlap_voxels}\n")
        
        if overlap_voxels > 0:
            f.write("⚠️  WARNING: Atlases have overlapping regions!\n")
            f.write("This may indicate cortical-subcortical boundary issues.\n")
        else:
            f.write("✅ No direct overlaps detected.\n")
    
    print(f"📄 Report saved: {report_path}")
    print(f"📊 Overlap check: {overlap_voxels} overlapping voxels")
    
    return overlap_voxels

if __name__ == "__main__":
    # Perform registration
    tian_path, des_path = register_atlases()
    
    # Generate report
    overlap_count = create_alignment_report()
    
    print(f"\n🎯 NEXT STEPS:")
    if overlap_count > 0:
        print("   1. ⚠️  Investigate overlapping regions")
        print("   2. Create overlap resolution strategy")
    else:
        print("   1. ✅ Proceed with atlas combination")
    print("   2. Generate individual ROI files")
    print("   3. Create MRIcrogl visualizations")