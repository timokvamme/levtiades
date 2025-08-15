#!/usr/bin/env python3
"""
Create Levtiades Atlas - Comprehensive Brain Atlas
Combining Levinson (midbrain/brainstem), Tian (subcortical), and Destrieux (cortical)
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import pandas as pd
import shutil
import glob

def gather_and_analyze_atlases():
    """Gather all three atlases and analyze their properties"""
    
    print("🧠 LEVTIADES ATLAS CREATION")
    print("Combining Levinson + Tian + Destrieux")
    print("=" * 50)
    
    base_dir = Path("levtiades_atlas")
    raw_dir = base_dir / "raw_atlases"
    raw_dir.mkdir(exist_ok=True)
    
    # Copy Levinson atlas components
    print("\n📋 Gathering Levinson-Bari Brainstem Atlas...")
    levinson_base = Path("data/Levinson-Bari Limbic Brainstem Atlas (Levinson 2022)")
    
    # Get all Levinson components
    levinson_files = {
        'LC': levinson_base / "mixed" / "01_LC_ATLAS_2022a.nii.gz",
        'NTS': levinson_base / "midline" / "02_NTS_ATLAS_2022a.nii.gz",
        'VTA': levinson_base / "midline" / "03_VTA_ATLAS_2022a.nii.gz",
        'PAG': levinson_base / "midline" / "04_PAG_ATLAS_2022a.nii.gz",
        'DRN': levinson_base / "midline" / "05_DRN_ATLAS_2022ai.nii.gz",
        'GM_MASK': levinson_base / "gm_mask.nii.gz"
    }
    
    levinson_data = {}
    for name, path in levinson_files.items():
        if path.exists():
            # Copy to raw directory
            dest = raw_dir / f"levinson_{name.lower()}.nii.gz"
            shutil.copy(path, dest)
            
            # Load and analyze
            img = nib.load(path)
            data = img.get_fdata()
            levinson_data[name] = {
                'img': img,
                'data': data,
                'shape': data.shape,
                'voxel_size': img.header.get_zooms()[:3],
                'unique_values': np.unique(data[data > 0]),
                'voxel_count': np.sum(data > 0)
            }
            print(f"   {name}: {data.shape}, {img.header.get_zooms()[:3]} mm, {np.sum(data > 0)} voxels")
    
    # Copy Tian atlas
    print("\n📋 Gathering Tian Subcortical Atlas...")
    tian_path = Path("tiandes_atlas/raw_atlases/tian_subcortical.nii.gz")
    if tian_path.exists():
        shutil.copy(tian_path, raw_dir / "tian_subcortical.nii.gz")
        tian_img = nib.load(tian_path)
        tian_data = tian_img.get_fdata()
        print(f"   Tian: {tian_data.shape}, {tian_img.header.get_zooms()[:3]} mm, 54 regions")
    else:
        print("   ❌ Tian atlas not found!")
        return None
    
    # Copy Destrieux atlas
    print("\n📋 Gathering Destrieux Cortical Atlas...")
    des_path = Path("tiandes_atlas/raw_atlases/destrieux_cortical.nii.gz")
    if des_path.exists():
        shutil.copy(des_path, raw_dir / "destrieux_cortical.nii.gz")
        des_img = nib.load(des_path)
        des_data = des_img.get_fdata()
        print(f"   Destrieux: {des_data.shape}, {des_img.header.get_zooms()[:3]} mm, 148 regions")
    else:
        print("   ❌ Destrieux atlas not found!")
        return None
    
    return levinson_data, tian_img, des_img

def create_combined_levinson_mask(levinson_data):
    """Create a single combined mask from all Levinson components"""
    
    print("\n🔧 Creating Combined Levinson Mask...")
    
    # Use the first component as reference
    ref_name = next(iter(levinson_data))
    ref_img = levinson_data[ref_name]['img']
    
    # Initialize combined mask
    combined_mask = np.zeros_like(levinson_data[ref_name]['data'])
    
    # Assign unique labels to each brainstem nucleus
    label_mapping = {
        'LC': 1,   # Locus Coeruleus
        'NTS': 2,  # Nucleus Tractus Solitarius
        'VTA': 3,  # Ventral Tegmental Area
        'PAG': 4,  # Periaqueductal Gray
        'DRN': 5   # Dorsal Raphe Nucleus
    }
    
    # Combine all components
    total_voxels = 0
    for name, label in label_mapping.items():
        if name in levinson_data and name != 'GM_MASK':
            mask = levinson_data[name]['data'] > 0
            combined_mask[mask] = label
            voxel_count = np.sum(mask)
            total_voxels += voxel_count
            print(f"   {name} (label {label}): {voxel_count} voxels")
    
    print(f"   Total Levinson voxels: {total_voxels}")
    
    # Save combined Levinson mask
    combined_img = nib.Nifti1Image(combined_mask.astype(np.int16), ref_img.affine, ref_img.header)
    nib.save(combined_img, Path("levtiades_atlas/raw_atlases/levinson_combined.nii.gz"))
    
    return combined_img, label_mapping

def check_spatial_alignment(levinson_img, tian_img, des_img):
    """Check if all atlases are in the same space"""
    
    print("\n🔍 Checking Spatial Alignment...")
    
    # Get properties
    atlases = {
        'Levinson': levinson_img,
        'Tian': tian_img,
        'Destrieux': des_img
    }
    
    print("\n📊 Atlas Properties:")
    for name, img in atlases.items():
        print(f"\n{name}:")
        print(f"   Shape: {img.shape}")
        print(f"   Voxel size: {img.header.get_zooms()[:3]} mm")
        print(f"   Affine origin: {img.affine[:3, 3]}")
    
    # Check if they match
    shapes_match = levinson_img.shape == tian_img.shape == des_img.shape
    voxels_match = (np.allclose(levinson_img.header.get_zooms()[:3], tian_img.header.get_zooms()[:3]) and
                    np.allclose(tian_img.header.get_zooms()[:3], des_img.header.get_zooms()[:3]))
    affines_match = (np.allclose(levinson_img.affine, tian_img.affine, atol=1e-3) and
                     np.allclose(tian_img.affine, des_img.affine, atol=1e-3))
    
    print(f"\n📋 Alignment Check:")
    print(f"   Shapes match: {'✅' if shapes_match else '❌'}")
    print(f"   Voxel sizes match: {'✅' if voxels_match else '❌'}")
    print(f"   Affines match: {'✅' if affines_match else '❌'}")
    
    return shapes_match and voxels_match and affines_match

def align_atlases_to_common_space(levinson_img, tian_img, des_img):
    """Align all atlases to a common space (using Tian as reference)"""
    
    print("\n🔄 Aligning Atlases to Common Space...")
    
    aligned_dir = Path("levtiades_atlas/aligned_atlases")
    aligned_dir.mkdir(exist_ok=True)
    
    # Use Tian as reference (it's in the middle of the hierarchy)
    print("   Using Tian as reference space...")
    
    # Save Tian as-is
    nib.save(tian_img, aligned_dir / "tian_aligned.nii.gz")
    
    # Resample others to match Tian
    from nilearn import image
    
    # Resample Levinson
    print("   Resampling Levinson to match Tian...")
    levinson_resampled = image.resample_to_img(levinson_img, tian_img, interpolation='nearest')
    nib.save(levinson_resampled, aligned_dir / "levinson_aligned.nii.gz")
    
    # Resample Destrieux (should already match from TianDes work)
    print("   Resampling Destrieux to match Tian...")
    des_resampled = image.resample_to_img(des_img, tian_img, interpolation='nearest')
    nib.save(des_resampled, aligned_dir / "destrieux_aligned.nii.gz")
    
    print("✅ All atlases aligned to common space")
    
    return levinson_resampled, tian_img, des_resampled

def create_levtiades_with_overlaps(levinson_img, tian_img, des_img):
    """Create version allowing overlaps - simple combination"""
    
    print("\n🎯 Creating Levtiades Atlas WITH Overlaps...")
    
    # Load data
    levinson_data = levinson_img.get_fdata().astype(int)
    tian_data = tian_img.get_fdata().astype(int)
    des_data = des_img.get_fdata().astype(int)
    
    # Create multi-label atlas allowing overlaps
    # Each atlas gets its own "channel"
    atlas_shape = list(levinson_data.shape) + [3]  # 3 channels for 3 atlases
    combined_overlaps = np.zeros(atlas_shape, dtype=np.int16)
    
    # Channel 0: Levinson (midbrain)
    combined_overlaps[:, :, :, 0] = levinson_data
    
    # Channel 1: Tian (subcortical) - offset labels by 100
    tian_offset = tian_data.copy()
    tian_offset[tian_data > 0] = tian_data[tian_data > 0] + 100
    combined_overlaps[:, :, :, 1] = tian_offset
    
    # Channel 2: Destrieux (cortical) - offset labels by 200
    des_offset = des_data.copy()
    des_offset[des_data > 0] = des_data[des_data > 0] + 200
    combined_overlaps[:, :, :, 2] = des_offset
    
    # Save multi-channel version
    output_dir = Path("levtiades_atlas/final_atlas/with_overlaps")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    multi_img = nib.Nifti1Image(combined_overlaps, levinson_img.affine, levinson_img.header)
    nib.save(multi_img, output_dir / "levtiades_multichannel.nii.gz")
    
    # Also create flattened version showing all regions
    combined_flat = np.zeros_like(levinson_data)
    combined_flat[levinson_data > 0] = levinson_data[levinson_data > 0]
    combined_flat[tian_data > 0] = tian_data[tian_data > 0] + 100
    combined_flat[des_data > 0] = des_data[des_data > 0] + 200
    
    flat_img = nib.Nifti1Image(combined_flat.astype(np.int16), levinson_img.affine, levinson_img.header)
    nib.save(flat_img, output_dir / "levtiades_flat_with_overlaps.nii.gz")
    
    # Calculate overlap statistics
    overlap_stats = {
        'levinson_tian': np.sum((levinson_data > 0) & (tian_data > 0)),
        'levinson_destrieux': np.sum((levinson_data > 0) & (des_data > 0)),
        'tian_destrieux': np.sum((tian_data > 0) & (des_data > 0)),
        'all_three': np.sum((levinson_data > 0) & (tian_data > 0) & (des_data > 0))
    }
    
    print(f"📊 Overlap Statistics:")
    for pair, count in overlap_stats.items():
        print(f"   {pair}: {count} voxels")
    
    return combined_overlaps, overlap_stats

def create_levtiades_hierarchical(levinson_img, tian_img, des_img):
    """Create version with hierarchical resolution: midbrain > subcortical > cortical"""
    
    print("\n🏗️ Creating Levtiades Atlas with Hierarchical Resolution...")
    print("   Priority: Midbrain > Subcortical > Cortical")
    
    # Load data
    levinson_data = levinson_img.get_fdata().astype(int)
    tian_data = tian_img.get_fdata().astype(int)
    des_data = des_img.get_fdata().astype(int)
    
    # Initialize combined atlas
    combined_hierarchical = np.zeros_like(levinson_data, dtype=np.int16)
    
    # Track changes for analysis
    changes = {
        'tian_replaced_by_levinson': 0,
        'destrieux_replaced_by_tian': 0,
        'destrieux_replaced_by_levinson': 0,
        'tian_regions_affected': {},
        'destrieux_regions_affected': {}
    }
    
    # Layer 3 (lowest priority): Cortical - Destrieux
    des_mask = des_data > 0
    combined_hierarchical[des_mask] = des_data[des_mask] + 200
    
    # Layer 2 (medium priority): Subcortical - Tian
    tian_mask = tian_data > 0
    
    # Track what Destrieux regions are replaced by Tian
    replaced_by_tian = (combined_hierarchical > 200) & tian_mask
    if np.any(replaced_by_tian):
        replaced_regions = combined_hierarchical[replaced_by_tian] - 200
        for region in np.unique(replaced_regions):
            count = np.sum(replaced_regions == region)
            changes['destrieux_regions_affected'][int(region)] = count
            changes['destrieux_replaced_by_tian'] += count
    
    combined_hierarchical[tian_mask] = tian_data[tian_mask] + 100
    
    # Layer 1 (highest priority): Midbrain - Levinson
    levinson_mask = levinson_data > 0
    
    # Track what Tian regions are replaced by Levinson
    replaced_by_levinson_from_tian = ((combined_hierarchical > 100) & (combined_hierarchical < 200)) & levinson_mask
    if np.any(replaced_by_levinson_from_tian):
        replaced_regions = combined_hierarchical[replaced_by_levinson_from_tian] - 100
        for region in np.unique(replaced_regions):
            count = np.sum(replaced_regions == region)
            changes['tian_regions_affected'][int(region)] = count
            changes['tian_replaced_by_levinson'] += count
    
    # Track what Destrieux regions are replaced by Levinson
    replaced_by_levinson_from_des = (combined_hierarchical > 200) & levinson_mask
    if np.any(replaced_by_levinson_from_des):
        changes['destrieux_replaced_by_levinson'] += np.sum(replaced_by_levinson_from_des)
    
    combined_hierarchical[levinson_mask] = levinson_data[levinson_mask]
    
    # Save hierarchical version
    output_dir = Path("levtiades_atlas/final_atlas/no_overlaps")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    hier_img = nib.Nifti1Image(combined_hierarchical, levinson_img.affine, levinson_img.header)
    nib.save(hier_img, output_dir / "levtiades_hierarchical.nii.gz")
    
    # Final statistics
    final_stats = {
        'levinson_voxels': np.sum((combined_hierarchical > 0) & (combined_hierarchical < 100)),
        'tian_voxels': np.sum((combined_hierarchical > 100) & (combined_hierarchical < 200)),
        'destrieux_voxels': np.sum(combined_hierarchical > 200),
        'total_voxels': np.sum(combined_hierarchical > 0)
    }
    
    print(f"\n📊 Hierarchical Resolution Statistics:")
    print(f"   Tian voxels replaced by Levinson: {changes['tian_replaced_by_levinson']}")
    print(f"   Destrieux voxels replaced by Tian: {changes['destrieux_replaced_by_tian']}")
    print(f"   Destrieux voxels replaced by Levinson: {changes['destrieux_replaced_by_levinson']}")
    
    print(f"\n📈 Final Atlas Composition:")
    for atlas, count in final_stats.items():
        print(f"   {atlas}: {count}")
    
    return combined_hierarchical, changes, final_stats

def create_label_files(levinson_labels, hierarchical=True):
    """Create comprehensive label files for Levtiades atlas"""
    
    print("\n📝 Creating Label Files...")
    
    output_dir = Path("levtiades_atlas/final_atlas")
    
    # Load existing label files
    tian_labels = {}
    tian_label_file = Path("tiandes_atlas/raw_atlases/tian_labels.txt")
    if tian_label_file.exists():
        with open(tian_label_file, 'r') as f:
            for line in f:
                if ':' in line:
                    idx, label = line.strip().split(':', 1)
                    try:
                        tian_labels[int(idx)] = label.strip()
                    except ValueError:
                        continue
    
    des_labels = {}
    des_label_file = Path("tiandes_atlas/raw_atlases/destrieux_labels.txt")
    if des_label_file.exists():
        with open(des_label_file, 'r') as f:
            for line in f:
                if ':' in line:
                    idx, label = line.strip().split(':', 1)
                    try:
                        des_labels[int(idx)] = label.strip()
                    except ValueError:
                        continue
    
    # Create comprehensive label file
    label_file = output_dir / "levtiades_labels.txt"
    with open(label_file, 'w') as f:
        f.write("# Levtiades Atlas Label File\n")
        f.write("# Combining Levinson (midbrain), Tian (subcortical), and Destrieux (cortical)\n")
        f.write("# Format: ID: Region_Name [Source_Atlas]\n\n")
        
        f.write("# LEVINSON BRAINSTEM/MIDBRAIN REGIONS (1-5)\n")
        for label, name in levinson_labels.items():
            f.write(f"{label}: {name} [Levinson]\n")
        
        f.write("\n# TIAN SUBCORTICAL REGIONS (101-154)\n")
        for idx, label in sorted(tian_labels.items()):
            f.write(f"{idx + 100}: {label} [Tian]\n")
        
        f.write("\n# DESTRIEUX CORTICAL REGIONS (201-348)\n")
        for idx, label in sorted(des_labels.items()):
            f.write(f"{idx + 200}: {label} [Destrieux]\n")
    
    print(f"✅ Label file created: {label_file}")
    
    # Create lookup table for MRIcrogl
    lookup_file = output_dir / "levtiades_lookup_table.txt"
    with open(lookup_file, 'w') as f:
        f.write("# Levtiades Atlas Lookup Table (MRIcrogl compatible)\n")
        f.write("# Index\tR\tG\tB\tLabel\n")
        
        # Levinson - Red tones (brainstem)
        for label, name in levinson_labels.items():
            r = 200 + (label * 10)
            g = 50 + (label * 20)
            b = 50
            f.write(f"{label}\t{r}\t{g}\t{b}\tLevinson:{name}\n")
        
        # Tian - Green tones (subcortical)
        for idx, label in sorted(tian_labels.items()):
            r = 50
            g = 150 + (idx % 10) * 10
            b = 100 + (idx % 5) * 20
            f.write(f"{idx + 100}\t{r}\t{g}\t{b}\tTian:{label}\n")
        
        # Destrieux - Blue tones (cortical)
        for idx, label in sorted(des_labels.items()):
            r = 100 + (idx % 5) * 20
            g = 100 + (idx % 10) * 10
            b = 200 + (idx % 3) * 20
            f.write(f"{idx + 200}\t{r}\t{g}\t{b}\tDestrieux:{label}\n")
    
    print(f"✅ Lookup table created: {lookup_file}")

def create_analysis_report(overlap_stats, changes, final_stats):
    """Create comprehensive analysis report"""
    
    print("\n📄 Creating Analysis Report...")
    
    report_path = Path("levtiades_atlas/reports/levtiades_analysis_report.md")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write("# Levtiades Atlas Analysis Report\n\n")
        f.write("## Overview\n")
        f.write("The Levtiades atlas combines three complementary brain atlases:\n")
        f.write("- **Levinson**: Brainstem/midbrain nuclei (5 regions)\n")
        f.write("- **Tian**: Subcortical structures (54 regions)\n")
        f.write("- **Destrieux**: Cortical parcellation (148 regions)\n\n")
        
        f.write("## Spatial Hierarchy\n")
        f.write("Priority order: Midbrain > Subcortical > Cortical\n")
        f.write("This reflects neuroanatomical organization from core to periphery.\n\n")
        
        f.write("## Overlap Analysis (Before Hierarchical Resolution)\n")
        for pair, count in overlap_stats.items():
            f.write(f"- **{pair}**: {count} voxels\n")
        
        f.write(f"\n## Hierarchical Resolution Impact\n")
        f.write(f"### Voxel Replacements\n")
        f.write(f"- Tian voxels replaced by Levinson: {changes['tian_replaced_by_levinson']}\n")
        f.write(f"- Destrieux voxels replaced by Tian: {changes['destrieux_replaced_by_tian']}\n")
        f.write(f"- Destrieux voxels replaced by Levinson: {changes['destrieux_replaced_by_levinson']}\n")
        
        if changes['tian_regions_affected']:
            f.write(f"\n### Tian Regions Affected by Levinson Priority\n")
            for region, count in sorted(changes['tian_regions_affected'].items()):
                f.write(f"- Region {region}: {count} voxels\n")
        
        if changes['destrieux_regions_affected']:
            f.write(f"\n### Destrieux Regions Affected by Tian Priority\n")
            for region, count in sorted(changes['destrieux_regions_affected'].items()):
                f.write(f"- Region {region}: {count} voxels\n")
        
        f.write(f"\n## Final Atlas Composition\n")
        total = final_stats['total_voxels']
        f.write(f"- **Levinson regions**: {final_stats['levinson_voxels']} voxels ({100*final_stats['levinson_voxels']/total:.2f}%)\n")
        f.write(f"- **Tian regions**: {final_stats['tian_voxels']} voxels ({100*final_stats['tian_voxels']/total:.2f}%)\n")
        f.write(f"- **Destrieux regions**: {final_stats['destrieux_voxels']} voxels ({100*final_stats['destrieux_voxels']/total:.2f}%)\n")
        f.write(f"- **Total brain coverage**: {total} voxels\n")
        
        f.write(f"\n## Scientific Rationale\n")
        f.write("The hierarchical resolution strategy reflects:\n")
        f.write("1. **Anatomical precision**: Smaller, well-defined structures take precedence\n")
        f.write("2. **Functional importance**: Core brainstem nuclei are preserved intact\n")
        f.write("3. **Clinical relevance**: Critical for understanding psychiatric/neurological conditions\n")
    
    print(f"✅ Analysis report created: {report_path}")

if __name__ == "__main__":
    # Step 1: Gather and analyze all atlases
    levinson_data, tian_img, des_img = gather_and_analyze_atlases()
    
    if not all([levinson_data, tian_img, des_img]):
        print("❌ Failed to load all atlases!")
        exit(1)
    
    # Step 2: Create combined Levinson mask
    levinson_img, levinson_labels = create_combined_levinson_mask(levinson_data)
    
    # Add Levinson labels
    levinson_label_names = {
        1: 'Locus_Coeruleus_LC',
        2: 'Nucleus_Tractus_Solitarius_NTS', 
        3: 'Ventral_Tegmental_Area_VTA',
        4: 'Periaqueductal_Gray_PAG',
        5: 'Dorsal_Raphe_Nucleus_DRN'
    }
    
    # Step 3: Check spatial alignment
    aligned = check_spatial_alignment(levinson_img, tian_img, des_img)
    
    # Step 4: Align if necessary
    if not aligned:
        levinson_img, tian_img, des_img = align_atlases_to_common_space(levinson_img, tian_img, des_img)
    
    # Step 5: Create version with overlaps
    combined_overlaps, overlap_stats = create_levtiades_with_overlaps(levinson_img, tian_img, des_img)
    
    # Step 6: Create hierarchical version (no overlaps)
    combined_hierarchical, changes, final_stats = create_levtiades_hierarchical(levinson_img, tian_img, des_img)
    
    # Step 7: Create label files
    create_label_files(levinson_label_names)
    
    # Step 8: Create analysis report
    create_analysis_report(overlap_stats, changes, final_stats)
    
    print("\n🎉 LEVTIADES ATLAS CREATION COMPLETE!")
    print("=" * 40)
    print("📁 Output location: levtiades_atlas/")
    print("🧠 Total regions: 207 (5 midbrain + 54 subcortical + 148 cortical)")
    print("📊 Two versions created:")
    print("   - WITH overlaps (multichannel)")
    print("   - NO overlaps (hierarchical resolution)")
    print("✅ Ready for validation and use!")