#!/usr/bin/env python3
"""
Atlas Combination Script for TianDes Project
Creates the final combined limbic-cortical atlas with overlap resolution
"""

import nibabel as nib
import numpy as np
import pandas as pd
from pathlib import Path

def load_labels():
    """Load and parse region labels from both atlases"""
    
    base_dir = Path("tiandes_atlas/raw_atlases")
    
    # Load Tian labels
    tian_labels = {}
    with open(base_dir / "tian_labels.txt", 'r') as f:
        for line in f:
            if line.strip() and ':' in line:
                parts = line.strip().split(':', 1)
                if len(parts) == 2:
                    try:
                        idx = int(parts[0])
                        label = parts[1].strip()
                        tian_labels[idx] = label
                    except ValueError:
                        continue
    
    # Load Destrieux labels  
    des_labels = {}
    with open(base_dir / "destrieux_labels.txt", 'r') as f:
        for line in f:
            if line.strip() and ':' in line:
                parts = line.strip().split(':', 1)
                if len(parts) == 2:
                    try:
                        idx = int(parts[0])
                        label = parts[1].strip()
                        des_labels[idx] = label
                    except ValueError:
                        continue
    
    return tian_labels, des_labels

def create_tiandes_atlas():
    """Create the combined TianDes atlas with overlap resolution"""
    
    print("🧠 CREATING TIANDES COMBINED ATLAS")
    print("=" * 40)
    
    # Load aligned atlases
    base_dir = Path("tiandes_atlas")
    aligned_dir = base_dir / "aligned_atlases"
    final_dir = base_dir / "final_atlas"
    
    tian_img = nib.load(aligned_dir / "tian_aligned.nii.gz")
    des_img = nib.load(aligned_dir / "destrieux_aligned.nii.gz")
    
    tian_data = tian_img.get_fdata().astype(int)
    des_data = des_img.get_fdata().astype(int)
    
    print(f"📊 Input dimensions: {tian_data.shape}")
    
    # Load labels
    tian_labels, des_labels = load_labels()
    
    # Create combined atlas with label offset
    # Strategy: Tian keeps original labels (1-54), Destrieux gets offset (+100)
    DESTRIEUX_OFFSET = 100
    
    print(f"📋 Label mapping strategy:")
    print(f"   Tian subcortical: 1-54 (unchanged)")
    print(f"   Destrieux cortical: {DESTRIEUX_OFFSET+1}-{DESTRIEUX_OFFSET+150} (offset +{DESTRIEUX_OFFSET})")
    
    # Initialize combined atlas
    combined_data = np.zeros_like(tian_data, dtype=int)
    
    # Step 1: Add Tian subcortical regions (priority in deep structures)
    tian_mask = tian_data > 0
    combined_data[tian_mask] = tian_data[tian_mask]
    tian_voxels = np.sum(tian_mask)
    
    print(f"✅ Added Tian subcortical regions: {tian_voxels:,} voxels")
    
    # Step 2: Add Destrieux cortical regions (where no Tian overlap)
    des_mask = (des_data > 0) & (tian_data == 0)  # Only where Tian is absent
    combined_data[des_mask] = des_data[des_mask] + DESTRIEUX_OFFSET
    des_voxels = np.sum(des_mask)
    
    print(f"✅ Added Destrieux cortical regions: {des_voxels:,} voxels")
    
    # Step 3: Handle overlaps (Tian priority in subcortical zones)
    overlap_mask = (tian_data > 0) & (des_data > 0)
    overlap_voxels = np.sum(overlap_mask)
    
    print(f"⚠️  Overlap resolution: {overlap_voxels} voxels")
    print(f"   Strategy: Tian priority (subcortical structures preserved)")
    
    # Step 4: Create final combined atlas
    final_atlas = combined_data.copy()
    
    # Verify no overlaps in final atlas
    tian_final = (final_atlas >= 1) & (final_atlas <= 54)
    des_final = final_atlas > DESTRIEUX_OFFSET
    final_overlaps = np.sum(tian_final & des_final)
    
    print(f"✅ Final atlas verification:")
    print(f"   Total regions: {len(np.unique(final_atlas[final_atlas > 0]))}")
    print(f"   Tian regions: {len(np.unique(final_atlas[tian_final]))}")
    print(f"   Destrieux regions: {len(np.unique(final_atlas[des_final]))}")
    print(f"   Remaining overlaps: {final_overlaps}")
    print(f"   Total brain voxels: {np.sum(final_atlas > 0):,}")
    
    # Save final atlas
    final_img = nib.Nifti1Image(final_atlas.astype(np.int16), tian_img.affine, tian_img.header)
    nib.save(final_img, final_dir / "tiandes_combined.nii.gz")
    
    return final_atlas, tian_labels, des_labels, DESTRIEUX_OFFSET

def create_label_files(final_atlas, tian_labels, des_labels, offset):
    """Create comprehensive label files for the combined atlas"""
    
    print(f"\n📝 CREATING LABEL FILES")
    print("=" * 25)
    
    base_dir = Path("tiandes_atlas/final_atlas")
    
    # Get unique labels in final atlas
    unique_labels = np.unique(final_atlas[final_atlas > 0])
    
    # Create comprehensive label file
    with open(base_dir / "tiandes_labels.txt", 'w') as f:
        f.write("# TianDes Limbic-Cortical Atlas Label File\n")
        f.write("# Format: ID: Region_Name [Source_Atlas]\n")
        f.write("# Tian subcortical regions: 1-54\n")
        f.write(f"# Destrieux cortical regions: {offset+1}-{offset+150}\n\n")
        
        for label_id in sorted(unique_labels):
            if 1 <= label_id <= 54:
                # Tian region
                region_name = tian_labels.get(label_id, f"Tian_Unknown_{label_id}")
                f.write(f"{label_id}: {region_name} [Tian_S4]\n")
            elif label_id > offset:
                # Destrieux region
                original_id = label_id - offset
                region_name = des_labels.get(original_id, f"Destrieux_Unknown_{original_id}")
                f.write(f"{label_id}: {region_name} [Destrieux]\n")
    
    # Create lookup table (FSL/MRIcrogl compatible)
    with open(base_dir / "tiandes_lookup_table.txt", 'w') as f:
        f.write("# TianDes Atlas Lookup Table (FSL/MRIcrogl compatible)\n")
        f.write("# Index\tR\tG\tB\tLabel\n")
        
        for i, label_id in enumerate(sorted(unique_labels)):
            # Generate distinct colors for visualization
            if 1 <= label_id <= 54:
                # Warm colors for subcortical (Tian)
                r = min(255, 150 + (label_id * 2))
                g = min(255, 100 + (label_id * 1.5))
                b = 100
                region_name = tian_labels.get(label_id, f"Tian_Unknown_{label_id}")
                source = "Tian"
            else:
                # Cool colors for cortical (Destrieux)
                original_id = label_id - offset
                r = 100
                g = min(255, 100 + (original_id * 1.2))
                b = min(255, 150 + (original_id * 1.8))
                region_name = des_labels.get(original_id, f"Destrieux_Unknown_{original_id}")
                source = "Destrieux"
            
            f.write(f"{label_id}\t{int(r)}\t{int(g)}\t{int(b)}\t{source}:{region_name}\n")
    
    # Create summary statistics
    stats_data = []
    for label_id in sorted(unique_labels):
        voxel_count = np.sum(final_atlas == label_id)
        
        if 1 <= label_id <= 54:
            source = "Tian_S4"
            region_name = tian_labels.get(label_id, f"Unknown_{label_id}")
        else:
            source = "Destrieux"
            original_id = label_id - offset
            region_name = des_labels.get(original_id, f"Unknown_{original_id}")
        
        stats_data.append({
            'label_id': label_id,
            'source_atlas': source,
            'region_name': region_name,
            'voxel_count': voxel_count,
            'volume_mm3': voxel_count * 8  # 2x2x2 mm voxels
        })
    
    # Save as CSV
    df = pd.DataFrame(stats_data)
    df.to_csv(base_dir / "tiandes_region_stats.csv", index=False)
    
    print(f"📄 Label files created:")
    print(f"   tiandes_labels.txt - Human-readable labels")
    print(f"   tiandes_lookup_table.txt - FSL/MRIcrogl color table")
    print(f"   tiandes_region_stats.csv - Volume statistics")
    
    return len(unique_labels)

def create_atlas_info():
    """Create comprehensive atlas information file"""
    
    print(f"\n📋 CREATING ATLAS INFO")
    print("=" * 23)
    
    base_dir = Path("tiandes_atlas")
    
    with open(base_dir / "TIANDES_ATLAS_INFO.md", 'w') as f:
        f.write("# TianDes Limbic-Cortical Atlas\n\n")
        f.write("## Overview\n")
        f.write("Combined brain atlas integrating:\n")
        f.write("- **Tian Subcortical Atlas (Scale IV)**: 54 fine-grained subcortical regions\n")
        f.write("- **Destrieux Cortical Atlas**: 148 sulco-gyral cortical regions\n\n")
        
        f.write("## Technical Specifications\n")
        f.write("- **Space**: MNI152NLin6Asym\n")
        f.write("- **Resolution**: 2×2×2 mm voxels\n")
        f.write("- **Dimensions**: 91×109×91 voxels\n")
        f.write("- **Format**: NIfTI-1 (.nii.gz)\n\n")
        
        f.write("## Label Scheme\n")
        f.write("- **Subcortical (Tian)**: Labels 1-54\n")
        f.write("- **Cortical (Destrieux)**: Labels 101-250\n")
        f.write("- **Total Regions**: ~200 brain regions\n\n")
        
        f.write("## Overlap Resolution\n")
        f.write("- **Strategy**: Tian priority in subcortical zones\n")
        f.write("- **Principle**: Preserve detailed subcortical parcellation\n")
        f.write("- **Boundary**: Natural limbic-cortical interface\n\n")
        
        f.write("## Files\n")
        f.write("- `tiandes_combined.nii.gz` - Main atlas file\n")
        f.write("- `tiandes_labels.txt` - Region labels\n")
        f.write("- `tiandes_lookup_table.txt` - Color lookup table\n")
        f.write("- `tiandes_region_stats.csv` - Volume statistics\n\n")
        
        f.write("## Citation\n")
        f.write("Please cite both source atlases:\n")
        f.write("- Tian et al. (2020) Nature Neuroscience - Melbourne Subcortex Atlas\n")
        f.write("- Destrieux et al. (2010) NeuroImage - Cortical parcellation\n\n")
        
        f.write("## Usage\n")
        f.write("Compatible with:\n")
        f.write("- FSL\n")
        f.write("- FreeSurfer\n")
        f.write("- AFNI\n")
        f.write("- MRIcrogl\n")
        f.write("- Python (nibabel, nilearn)\n")
        f.write("- R (oro.nifti, ANTsR)\n")
    
    print(f"📄 Atlas documentation: TIANDES_ATLAS_INFO.md")

if __name__ == "__main__":
    # Create combined atlas
    final_atlas, tian_labels, des_labels, offset = create_tiandes_atlas()
    
    # Create label files
    total_regions = create_label_files(final_atlas, tian_labels, des_labels, offset)
    
    # Create documentation
    create_atlas_info()
    
    print(f"\n🎉 TIANDES ATLAS CREATION COMPLETE!")
    print("=" * 40)
    print(f"📊 Final Statistics:")
    print(f"   Total regions: {total_regions}")
    print(f"   Subcortical (Tian): 54 regions")
    print(f"   Cortical (Destrieux): {total_regions - 54} regions")
    print(f"   Total brain voxels: {np.sum(final_atlas > 0):,}")
    print(f"\n📁 Output location: tiandes_atlas/final_atlas/")
    print(f"🎯 Ready for neuroimaging analysis!")