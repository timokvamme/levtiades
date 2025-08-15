#!/usr/bin/env python3
"""
Fix Levtiades Atlas - Create Individual ROIs and Remove Wall/Background Regions
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import shutil

def identify_wall_regions():
    """Identify medial wall and background regions to remove"""
    
    print("🔍 Identifying Wall/Background Regions to Remove...")
    
    # Load Destrieux labels
    des_labels = {}
    des_label_file = Path("tiandes_atlas/raw_atlases/destrieux_labels.txt")
    
    if des_label_file.exists():
        with open(des_label_file, 'r') as f:
            for line in f:
                if ':' in line and not line.startswith('#'):
                    parts = line.strip().split(':', 1)
                    if len(parts) == 2:
                        try:
                            idx = int(parts[0])
                            label = parts[1].strip()
                            des_labels[idx] = label
                        except ValueError:
                            continue
    
    # Find wall and background regions
    regions_to_remove = []
    for idx, label in des_labels.items():
        label_lower = label.lower()
        if 'medial_wall' in label_lower or 'medial wall' in label_lower or \
           'background' in label_lower or label_lower == 'unknown':
            regions_to_remove.append(idx)
            print(f"   Found region to remove: {idx}: {label}")
    
    return regions_to_remove, des_labels

def create_fixed_atlas(regions_to_remove):
    """Create new atlas with wall regions removed"""
    
    print("\n🏗️ Creating Fixed Atlas (Removing Wall/Background)...")
    
    # Load current hierarchical atlas
    hier_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_hierarchical.nii.gz")
    hier_img = nib.load(hier_path)
    hier_data = hier_img.get_fdata().astype(int)
    
    # Create fixed version
    fixed_data = hier_data.copy()
    
    # Remove wall regions (they have labels 200+)
    removed_voxels = 0
    for region_idx in regions_to_remove:
        region_label = region_idx + 200  # Destrieux offset
        mask = fixed_data == region_label
        removed_voxels += np.sum(mask)
        fixed_data[mask] = 0
    
    print(f"   Removed {removed_voxels} voxels from {len(regions_to_remove)} wall/background regions")
    
    # Save fixed atlas
    fixed_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_hierarchical_fixed.nii.gz")
    fixed_img = nib.Nifti1Image(fixed_data.astype(np.int16), hier_img.affine, hier_img.header)
    nib.save(fixed_img, fixed_path)
    
    print(f"✅ Fixed atlas saved: {fixed_path}")
    
    return fixed_img, fixed_data

def create_individual_rois(atlas_img, atlas_data):
    """Create individual ROI files for each region"""
    
    print("\n🎯 Creating Individual ROI Files...")
    
    # Get all unique labels
    unique_labels = np.unique(atlas_data[atlas_data > 0])
    print(f"   Total regions to extract: {len(unique_labels)}")
    
    # Create directories
    roi_base = Path("levtiades_atlas/individual_rois")
    midbrain_dir = roi_base / "midbrain"
    subcortical_dir = roi_base / "subcortical"
    cortical_dir = roi_base / "cortical"
    
    for dir in [midbrain_dir, subcortical_dir, cortical_dir]:
        dir.mkdir(parents=True, exist_ok=True)
    
    # Process each region
    for i, label in enumerate(unique_labels):
        # Create binary mask for this region
        roi_mask = (atlas_data == label).astype(np.uint8)
        roi_img = nib.Nifti1Image(roi_mask, atlas_img.affine, atlas_img.header)
        
        # Determine category and create filename
        if label < 100:
            # Levinson midbrain
            category = "midbrain"
            output_dir = midbrain_dir
            filename = f"levinson_{label:03d}.nii.gz"
        elif label < 200:
            # Tian subcortical
            category = "subcortical"
            output_dir = subcortical_dir
            filename = f"tian_{label:03d}.nii.gz"
        else:
            # Destrieux cortical
            category = "cortical"
            output_dir = cortical_dir
            filename = f"destrieux_{label:03d}.nii.gz"
        
        # Save ROI
        output_path = output_dir / filename
        nib.save(roi_img, output_path)
        
        if (i + 1) % 50 == 0:
            print(f"   Processed {i + 1}/{len(unique_labels)} regions...")
    
    print(f"✅ Created {len(unique_labels)} individual ROI files")
    
    return unique_labels

def create_complete_lookup_table(unique_labels, regions_removed):
    """Create complete lookup table with all regions including Tian"""
    
    print("\n📋 Creating Complete Lookup Table...")
    
    # Load all label files
    levinson_labels = {
        1: 'Locus_Coeruleus_LC',
        2: 'Nucleus_Tractus_Solitarius_NTS',
        3: 'Ventral_Tegmental_Area_VTA',
        4: 'Periaqueductal_Gray_PAG',
        5: 'Dorsal_Raphe_Nucleus_DRN'
    }
    
    # Load Tian labels
    tian_labels = {}
    tian_label_file = Path("tiandes_atlas/raw_atlases/tian_labels.txt")
    if tian_label_file.exists():
        with open(tian_label_file, 'r') as f:
            for line in f:
                if ':' in line and not line.startswith('#'):
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
    des_label_file = Path("tiandes_atlas/raw_atlases/destrieux_labels.txt")
    if des_label_file.exists():
        with open(des_label_file, 'r') as f:
            for line in f:
                if ':' in line and not line.startswith('#'):
                    parts = line.strip().split(':', 1)
                    if len(parts) == 2:
                        try:
                            idx = int(parts[0])
                            label = parts[1].strip()
                            # Skip removed regions
                            if idx not in regions_removed:
                                des_labels[idx] = label
                        except ValueError:
                            continue
    
    # Create lookup table
    lookup_path = Path("levtiades_atlas/final_atlas/levtiades_lookup_table_complete.txt")
    with open(lookup_path, 'w') as f:
        f.write("# Levtiades Atlas Complete Lookup Table (MRIcrogl compatible)\n")
        f.write("# Index\tR\tG\tB\tLabel\n")
        f.write("# Format: label_number<tab>red<tab>green<tab>blue<tab>label_name\n\n")
        
        # Write all regions in order
        for label in sorted(unique_labels):
            if label < 100:
                # Levinson - Red/Orange tones
                name = levinson_labels.get(label, f"Levinson_{label}")
                r = 255 - (label * 20)
                g = 100 + (label * 30)
                b = 50
                source = "Levinson"
            elif label < 200:
                # Tian - Green tones
                original_idx = label - 100
                name = tian_labels.get(original_idx, f"Tian_{original_idx}")
                r = 50 + (original_idx % 5) * 20
                g = 150 + (original_idx % 10) * 10
                b = 100 + (original_idx % 5) * 20
                source = "Tian"
            else:
                # Destrieux - Blue tones
                original_idx = label - 200
                name = des_labels.get(original_idx, f"Destrieux_{original_idx}")
                r = 100 + (original_idx % 5) * 20
                g = 100 + (original_idx % 10) * 10
                b = 200 + (original_idx % 3) * 20
                source = "Destrieux"
            
            # Ensure RGB values are in valid range
            r = min(255, max(0, r))
            g = min(255, max(0, g))
            b = min(255, max(0, b))
            
            f.write(f"{label}\t{r}\t{g}\t{b}\t{source}:{name}\n")
    
    print(f"✅ Complete lookup table created: {lookup_path}")
    print(f"   Total entries: {len(unique_labels)}")

def create_complete_label_file(unique_labels, regions_removed):
    """Create complete label file with all regions"""
    
    print("\n📝 Creating Complete Label File...")
    
    # Load all labels (same as above)
    levinson_labels = {
        1: 'Locus_Coeruleus_LC',
        2: 'Nucleus_Tractus_Solitarius_NTS',
        3: 'Ventral_Tegmental_Area_VTA',
        4: 'Periaqueductal_Gray_PAG',
        5: 'Dorsal_Raphe_Nucleus_DRN'
    }
    
    # Load Tian labels
    tian_labels = {}
    tian_label_file = Path("tiandes_atlas/raw_atlases/tian_labels.txt")
    if tian_label_file.exists():
        with open(tian_label_file, 'r') as f:
            for line in f:
                if ':' in line and not line.startswith('#'):
                    parts = line.strip().split(':', 1)
                    if len(parts) == 2:
                        try:
                            idx = int(parts[0])
                            label = parts[1].strip()
                            tian_labels[idx] = label
                        except ValueError:
                            continue
    
    # Load Destrieux labels (excluding removed)
    des_labels = {}
    des_label_file = Path("tiandes_atlas/raw_atlases/destrieux_labels.txt")
    if des_label_file.exists():
        with open(des_label_file, 'r') as f:
            for line in f:
                if ':' in line and not line.startswith('#'):
                    parts = line.strip().split(':', 1)
                    if len(parts) == 2:
                        try:
                            idx = int(parts[0])
                            label = parts[1].strip()
                            if idx not in regions_removed:
                                des_labels[idx] = label
                        except ValueError:
                            continue
    
    # Create complete label file
    label_path = Path("levtiades_atlas/final_atlas/levtiades_labels_complete.txt")
    with open(label_path, 'w') as f:
        f.write("# Levtiades Atlas Complete Label File\n")
        f.write("# Combining Levinson (midbrain), Tian (subcortical), and Destrieux (cortical)\n")
        f.write("# Wall/Background regions have been removed\n")
        f.write("# Format: ID: Region_Name [Source_Atlas]\n\n")
        
        # Count regions by source
        levinson_count = sum(1 for l in unique_labels if l < 100)
        tian_count = sum(1 for l in unique_labels if 100 <= l < 200)
        des_count = sum(1 for l in unique_labels if l >= 200)
        
        f.write(f"# Total regions: {len(unique_labels)}\n")
        f.write(f"# Levinson: {levinson_count} regions\n")
        f.write(f"# Tian: {tian_count} regions\n")
        f.write(f"# Destrieux: {des_count} regions (wall/background removed)\n\n")
        
        # Write Levinson regions
        f.write("# LEVINSON BRAINSTEM/MIDBRAIN REGIONS (1-5)\n")
        for label in sorted([l for l in unique_labels if l < 100]):
            name = levinson_labels.get(label, f"Levinson_{label}")
            f.write(f"{label}: {name} [Levinson]\n")
        
        # Write Tian regions
        f.write("\n# TIAN SUBCORTICAL REGIONS (101-154)\n")
        for label in sorted([l for l in unique_labels if 100 <= l < 200]):
            original_idx = label - 100
            name = tian_labels.get(original_idx, f"Tian_{original_idx}")
            f.write(f"{label}: {name} [Tian]\n")
        
        # Write Destrieux regions
        f.write("\n# DESTRIEUX CORTICAL REGIONS (201+)\n")
        for label in sorted([l for l in unique_labels if l >= 200]):
            original_idx = label - 200
            name = des_labels.get(original_idx, f"Destrieux_{original_idx}")
            f.write(f"{label}: {name} [Destrieux]\n")
    
    print(f"✅ Complete label file created: {label_path}")

def create_summary_report(unique_labels, regions_removed, removed_voxels):
    """Create summary report of changes"""
    
    print("\n📄 Creating Summary Report...")
    
    report_path = Path("levtiades_atlas/ATLAS_FIX_SUMMARY.md")
    
    levinson_count = sum(1 for l in unique_labels if l < 100)
    tian_count = sum(1 for l in unique_labels if 100 <= l < 200)
    des_count = sum(1 for l in unique_labels if l >= 200)
    
    with open(report_path, 'w') as f:
        f.write("# Levtiades Atlas Fix Summary\n\n")
        
        f.write("## Changes Made\n")
        f.write(f"1. **Removed {len(regions_removed)} wall/background regions** from Destrieux\n")
        f.write("2. **Created {len(unique_labels)} individual ROI files**\n")
        f.write("3. **Fixed lookup table** to include all Tian regions\n")
        f.write("4. **Created complete label file** with proper organization\n\n")
        
        f.write("## Removed Regions\n")
        f.write("The following regions were removed as they represent non-brain areas:\n")
        for region_idx in regions_removed:
            f.write(f"- Destrieux region {region_idx}\n")
        f.write(f"\nTotal voxels removed: {removed_voxels}\n\n")
        
        f.write("## Final Atlas Composition\n")
        f.write(f"- **Levinson**: {levinson_count} regions\n")
        f.write(f"- **Tian**: {tian_count} regions\n")
        f.write(f"- **Destrieux**: {des_count} regions (after removing wall/background)\n")
        f.write(f"- **Total**: {len(unique_labels)} regions\n\n")
        
        f.write("## Individual ROI Files\n")
        f.write(f"Created {len(unique_labels)} individual binary masks:\n")
        f.write("- `individual_rois/midbrain/levinson_XXX.nii.gz`\n")
        f.write("- `individual_rois/subcortical/tian_XXX.nii.gz`\n")
        f.write("- `individual_rois/cortical/destrieux_XXX.nii.gz`\n\n")
        
        f.write("## Updated Files\n")
        f.write("- `final_atlas/no_overlaps/levtiades_hierarchical_fixed.nii.gz` - Atlas without wall regions\n")
        f.write("- `final_atlas/levtiades_lookup_table_complete.txt` - Complete color table\n")
        f.write("- `final_atlas/levtiades_labels_complete.txt` - Complete label list\n")
    
    print(f"✅ Summary report created: {report_path}")

if __name__ == "__main__":
    print("🔧 FIXING LEVTIADES ATLAS")
    print("=" * 30)
    
    # Step 1: Identify wall/background regions
    regions_to_remove, des_labels = identify_wall_regions()
    
    # Step 2: Create fixed atlas
    fixed_img, fixed_data = create_fixed_atlas(regions_to_remove)
    
    # Step 3: Create individual ROIs
    unique_labels = create_individual_rois(fixed_img, fixed_data)
    
    # Step 4: Create complete lookup table
    create_complete_lookup_table(unique_labels, regions_to_remove)
    
    # Step 5: Create complete label file
    create_complete_label_file(unique_labels, regions_to_remove)
    
    # Step 6: Create summary report
    removed_voxels = sum(200 + idx in unique_labels for idx in regions_to_remove)
    create_summary_report(unique_labels, regions_to_remove, removed_voxels)
    
    print("\n✅ ATLAS FIX COMPLETE!")
    print("=" * 25)
    print(f"📊 Removed {len(regions_to_remove)} wall/background regions")
    print(f"🧠 Created {len(unique_labels)} individual ROI files")
    print(f"📋 Fixed lookup table with all regions")
    print(f"📁 Check individual_rois/ folder for ROI masks")