#!/usr/bin/env python3
"""
TianDes Atlas Setup Script
Creates combined limbic-cortical atlas by merging Tian subcortical with Destrieux cortical atlases
"""

import os
import shutil
import nibabel as nib
import numpy as np
from pathlib import Path

def setup_tiandes_project():
    """Download Destrieux and prepare for combination with local Tian data"""
    
    # Base directories
    base_dir = Path("tiandes_atlas")
    raw_dir = base_dir / "raw_atlases"
    
    print("🧠 Setting up TianDes Limbic-Cortical Atlas Project")
    print("=" * 60)
    
    # Download Destrieux atlas
    print("📥 Downloading Destrieux cortical atlas...")
    try:
        from nilearn.datasets import fetch_atlas_destrieux_2009
        destrieux = fetch_atlas_destrieux_2009()
        
        # Load and save atlas
        des_img = nib.load(destrieux.maps)
        nib.save(des_img, raw_dir / "destrieux_cortical.nii.gz")
        
        # Save labels with proper formatting
        with open(raw_dir / "destrieux_labels.txt", 'w') as f:
            for i, label in enumerate(destrieux.labels):
                f.write(f"{i}: {label}\n")
        
        print(f"✅ Destrieux atlas saved: {des_img.shape} voxels")
        print(f"   Regions: {len(destrieux.labels)} cortical areas")
        
    except ImportError:
        print("❌ Error: nilearn not installed. Please install with: pip install nilearn")
        return False
    except Exception as e:
        print(f"❌ Error downloading Destrieux: {e}")
        return False
    
    # Copy Tian data (Scale IV for maximum subcortical detail)
    print("\n📋 Preparing Tian subcortical data...")
    
    # We want the pure subcortex-only version (not the combined cortex-subcortex)
    tian_source = Path("data/Tian2020MSA_v1.4/3T/Subcortex-Only/Tian_Subcortex_S4_3T.nii.gz")
    tian_labels = Path("data/Tian2020MSA_v1.4/3T/Subcortex-Only/Tian_Subcortex_S4_3T_label.txt")
    
    if tian_source.exists() and tian_labels.exists():
        shutil.copy(tian_source, raw_dir / "tian_subcortical.nii.gz")
        shutil.copy(tian_labels, raw_dir / "tian_labels.txt")
        
        # Load and check Tian atlas
        tian_img = nib.load(tian_source)
        print(f"✅ Tian S4 atlas copied: {tian_img.shape} voxels")
        print(f"   Scale IV: 54 subcortical regions (most detailed)")
        
    else:
        print(f"❌ Error: Tian atlas files not found at {tian_source}")
        return False
    
    # Create atlas info summary
    info_file = base_dir / "atlas_info.txt"
    with open(info_file, 'w') as f:
        f.write("TianDes Limbic-Cortical Atlas Information\n")
        f.write("=" * 45 + "\n\n")
        f.write("COMPONENT ATLASES:\n")
        f.write("1. Tian Subcortical Atlas (Scale IV - S4)\n")
        f.write("   - Source: Melbourne Subcortex Atlas v1.4\n")
        f.write("   - Regions: 54 fine-grained subcortical areas\n")
        f.write("   - Structures: Striatum, Thalamus, Hippocampus, Amygdala, Globus Pallidus\n")
        f.write("   - Space: MNI152NLin6Asym (3T)\n\n")
        f.write("2. Destrieux Cortical Atlas (2009)\n")
        f.write("   - Source: Nilearn/FSL\n")
        f.write("   - Regions: 148 sulco-gyral cortical areas (74 per hemisphere)\n")
        f.write("   - Space: MNI152 standard\n\n")
        f.write("COMBINATION STRATEGY:\n")
        f.write("- Limbic structures: High-detail Tian subcortical regions\n")
        f.write("- Cortical structures: Fine-grained Destrieux parcellation\n")
        f.write("- Target space: MNI152 standard (aligned)\n")
        f.write("- Label range: Tian (1-54), Destrieux (55-202)\n")
    
    print(f"\n📄 Project info saved to: {info_file}")
    print("\n🎯 Next steps:")
    print("   1. Run spatial compatibility check")
    print("   2. Align atlases if needed")
    print("   3. Check for overlaps")
    print("   4. Combine atlases")
    print("   5. Generate visualization files")
    
    return True

def verify_atlas_properties():
    """Check basic properties of both atlases"""
    
    print("\n🔍 ATLAS VERIFICATION")
    print("=" * 30)
    
    raw_dir = Path("tiandes_atlas/raw_atlases")
    
    # Load both atlases
    try:
        tian_img = nib.load(raw_dir / "tian_subcortical.nii.gz")
        des_img = nib.load(raw_dir / "destrieux_cortical.nii.gz")
        
        print("TIAN SUBCORTICAL (S4):")
        print(f"  Shape: {tian_img.shape}")
        print(f"  Voxel size: {tian_img.header.get_zooms()[:3]} mm")
        print(f"  Data range: {tian_img.get_fdata().min():.0f} - {tian_img.get_fdata().max():.0f}")
        print(f"  Unique regions: {len(np.unique(tian_img.get_fdata()[tian_img.get_fdata() > 0]))}")
        
        print("\nDESTRIEUX CORTICAL:")
        print(f"  Shape: {des_img.shape}")
        print(f"  Voxel size: {des_img.header.get_zooms()[:3]} mm")
        print(f"  Data range: {des_img.get_fdata().min():.0f} - {des_img.get_fdata().max():.0f}")
        print(f"  Unique regions: {len(np.unique(des_img.get_fdata()[des_img.get_fdata() > 0]))}")
        
        # Check spatial compatibility
        print("\nSPATIAL COMPATIBILITY:")
        shape_match = tian_img.shape == des_img.shape
        affine_match = np.allclose(tian_img.affine, des_img.affine, atol=1e-3)
        
        print(f"  Shape match: {shape_match}")
        print(f"  Affine match: {affine_match}")
        
        if not shape_match or not affine_match:
            print("  ⚠️  Registration will be needed")
        else:
            print("  ✅ Atlases appear spatially compatible")
        
        return shape_match and affine_match
        
    except Exception as e:
        print(f"❌ Error verifying atlases: {e}")
        return False

if __name__ == "__main__":
    success = setup_tiandes_project()
    if success:
        verify_atlas_properties()
    else:
        print("❌ Setup failed. Please check error messages above.")