#!/usr/bin/env python3
"""
Check Original Destrieux Atlas Properties
Verify the native resolution and space of the Destrieux atlas before resampling
"""

import nibabel as nib
import numpy as np
from pathlib import Path

def check_original_destrieux():
    """Check the original Destrieux atlas properties"""
    
    print("🔍 ORIGINAL DESTRIEUX ATLAS PROPERTIES")
    print("=" * 42)
    
    base_dir = Path("tiandes_atlas")
    
    # Load the original downloaded Destrieux atlas
    original_des_path = base_dir / "raw_atlases" / "destrieux_cortical.nii.gz"
    
    if not original_des_path.exists():
        print(f"❌ Original Destrieux not found at {original_des_path}")
        return
    
    # Load original
    des_img = nib.load(original_des_path)
    
    print(f"📊 ORIGINAL DESTRIEUX SPECIFICATIONS:")
    print(f"   File: {original_des_path.name}")
    print(f"   Dimensions: {des_img.shape}")
    print(f"   Voxel size: {des_img.header.get_zooms()[:3]} mm")
    print(f"   Data type: {des_img.get_fdata().dtype}")
    print(f"   Orientation: {nib.aff2axcodes(des_img.affine)}")
    
    # Check coordinate system details
    print(f"\n🌍 COORDINATE SYSTEM:")
    print(f"   Origin: {des_img.affine[:3, 3]}")
    print(f"   Field of view: {np.array(des_img.shape[:3]) * np.array(des_img.header.get_zooms()[:3])} mm")
    
    # Compare with Tian
    tian_path = base_dir / "raw_atlases" / "tian_subcortical.nii.gz"
    if tian_path.exists():
        tian_img = nib.load(tian_path)
        
        print(f"\n🔄 COMPARISON WITH TIAN:")
        print(f"   Tian dimensions: {tian_img.shape}")
        print(f"   Tian voxel size: {tian_img.header.get_zooms()[:3]} mm")
        print(f"   Tian origin: {tian_img.affine[:3, 3]}")
        
        # Check if they match
        same_voxel_size = np.allclose(des_img.header.get_zooms()[:3], 
                                     tian_img.header.get_zooms()[:3])
        same_shape = des_img.shape == tian_img.shape
        
        print(f"\n📋 COMPATIBILITY CHECK:")
        print(f"   Same voxel size: {'✅' if same_voxel_size else '❌'}")
        print(f"   Same dimensions: {'✅' if same_shape else '❌'}")
        
        if not same_voxel_size:
            print(f"   🔧 Resampling was necessary")
            print(f"   Original Destrieux: {des_img.header.get_zooms()[:3]} mm")
            print(f"   Target Tian: {tian_img.header.get_zooms()[:3]} mm")
        else:
            print(f"   ✅ Native resolutions already matched")
    
    # Check what nilearn typically provides
    print(f"\n📚 NILEARN DESTRIEUX INFO:")
    try:
        from nilearn.datasets import fetch_atlas_destrieux_2009
        destrieux_info = fetch_atlas_destrieux_2009()
        
        print(f"   Source: {destrieux_info.description}")
        print(f"   Reference: FreeSurfer's aparc.a2009s atlas")
        print(f"   Typical resolution: Usually 1×1×1 mm (FreeSurfer native)")
        print(f"   Standard space: MNI152 (various versions)")
        
    except ImportError:
        print(f"   nilearn not available for additional info")
    
    return des_img.header.get_zooms()[:3], des_img.shape

def investigate_destrieux_source():
    """Investigate the typical Destrieux atlas specifications"""
    
    print(f"\n📖 DESTRIEUX ATLAS BACKGROUND")
    print("-" * 32)
    
    print("🎯 TYPICAL DESTRIEUX SPECIFICATIONS:")
    print("   • Original source: FreeSurfer's aparc.a2009s")
    print("   • Native resolution: 1×1×1 mm (FreeSurfer default)")
    print("   • Coordinate system: Various MNI152 variants")
    print("   • Distribution format: Often resampled to 2×2×2 mm")
    print("   • Purpose: Compatibility with fMRI analysis (2mm standard)")
    
    print(f"\n💡 WHY 2×2×2 mm VERSION EXISTS:")
    print("   • fMRI data commonly acquired at 2-4mm resolution")
    print("   • 2×2×2 mm is standard for group analysis")
    print("   • Reduces file sizes and computation time")
    print("   • Maintains anatomical detail while being practical")
    
    print(f"\n🔬 WHAT NILEARN PROVIDES:")
    print("   • Pre-resampled version for convenience")
    print("   • Already in 2×2×2 mm MNI152 space")
    print("   • Ready for immediate fMRI analysis")
    print("   • No further resampling needed if target is 2mm")

if __name__ == "__main__":
    # Check original properties
    voxel_size, shape = check_original_destrieux()
    
    # Provide background context
    investigate_destrieux_source()
    
    print(f"\n🎯 SUMMARY:")
    if voxel_size is not None:
        if np.allclose(voxel_size, [2.0, 2.0, 2.0]):
            print("✅ Destrieux was already in 2×2×2 mm resolution")
            print("   Our resampling step just ensured spatial alignment")
        elif np.allclose(voxel_size, [1.0, 1.0, 1.0]):
            print("📏 Destrieux was in 1×1×1 mm resolution (FreeSurfer native)")
            print("   Our resampling downsampled to 2×2×2 mm to match Tian")
        else:
            print(f"📐 Destrieux was in {voxel_size} mm resolution")
            print("   Our resampling standardized to 2×2×2 mm")
    
    print("\n💡 BOTTOM LINE:")
    print("   The resampling step ensured both atlases use identical")
    print("   coordinate systems, regardless of original resolution.")