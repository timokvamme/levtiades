#!/usr/bin/env python3
"""
Reindex Levtiades Atlas - Sequential Labeling 1-207
Convert from current scheme (1-5, 101-154, 201+) to sequential (1-207)
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import json
import pandas as pd

def create_reindexing_map():
    """Create mapping from old indices to new sequential indices"""
    
    print("📊 Creating Reindexing Map...")
    
    # Load current atlas to get all existing labels
    atlas_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_hierarchical_fixed.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # Get all unique labels in order
    old_labels = sorted(np.unique(atlas_data[atlas_data > 0]))
    print(f"   Found {len(old_labels)} unique labels")
    
    # Create sequential mapping
    reindex_map = {}
    new_index = 1
    
    # Process in anatomical order: Levinson -> Tian -> Destrieux
    
    # 1. Levinson regions (1-5) -> sequential starting from 1
    levinson_labels = [l for l in old_labels if l < 100]
    for old_label in sorted(levinson_labels):
        reindex_map[old_label] = new_index
        print(f"   Levinson {old_label} -> {new_index}")
        new_index += 1
    
    # 2. Tian regions (101-154) -> continue sequentially
    tian_labels = [l for l in old_labels if 100 <= l < 200]
    for old_label in sorted(tian_labels):
        reindex_map[old_label] = new_index
        print(f"   Tian {old_label} -> {new_index}")
        new_index += 1
    
    # 3. Destrieux regions (201+) -> continue sequentially
    destrieux_labels = [l for l in old_labels if l >= 200]
    for old_label in sorted(destrieux_labels):
        reindex_map[old_label] = new_index
        print(f"   Destrieux {old_label} -> {new_index}")
        new_index += 1
    
    print(f"✅ Created mapping for {len(reindex_map)} regions")
    print(f"   New index range: 1 - {new_index-1}")
    
    # Save mapping (convert numpy int64 to regular int for JSON)
    map_path = Path("levtiades_atlas/reindexing_map.json")
    reindex_map_serializable = {int(k): int(v) for k, v in reindex_map.items()}
    with open(map_path, 'w') as f:
        json.dump(reindex_map_serializable, f, indent=2)
    
    return reindex_map, atlas_img, atlas_data

def create_reindexed_atlas(reindex_map, atlas_img, atlas_data):
    """Create new atlas with sequential indices"""
    
    print("\n🏗️ Creating Reindexed Atlas...")
    
    # Create new data array
    new_atlas_data = np.zeros_like(atlas_data, dtype=np.int16)
    
    # Apply reindexing
    for old_label, new_label in reindex_map.items():
        mask = atlas_data == old_label
        new_atlas_data[mask] = new_label
        voxel_count = np.sum(mask)
        if voxel_count > 0:  # Only print for regions that exist
            print(f"   Reindexed {old_label} -> {new_label}: {voxel_count} voxels")
    
    # Verify no data loss
    old_voxels = np.sum(atlas_data > 0)
    new_voxels = np.sum(new_atlas_data > 0)
    print(f"   Verification: {old_voxels} -> {new_voxels} voxels")
    
    if old_voxels != new_voxels:
        print("❌ ERROR: Voxel count mismatch!")
        return None
    
    # Save reindexed atlas
    output_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    new_img = nib.Nifti1Image(new_atlas_data, atlas_img.affine, atlas_img.header)
    nib.save(new_img, output_path)
    
    print(f"✅ Reindexed atlas saved: {output_path}")
    
    return new_atlas_data, new_img

def load_original_labels():
    """Load original label information"""
    
    print("\n📋 Loading Original Label Information...")
    
    # Load Levinson labels
    levinson_labels = {
        1: 'Locus_Coeruleus_LC',
        2: 'Nucleus_Tractus_Solitarius_NTS',
        3: 'Ventral_Tegmental_Area_VTA',
        4: 'Periaqueductal_Gray_PAG',
        5: 'Dorsal_Raphe_Nucleus_DRN'
    }
    
    # Load Tian labels
    tian_labels = {}
    tian_file = Path("tiandes_atlas/raw_atlases/tian_labels.txt")
    if tian_file.exists():
        with open(tian_file, 'r') as f:
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
    destrieux_labels = {}
    des_file = Path("tiandes_atlas/raw_atlases/destrieux_labels.txt")
    if des_file.exists():
        with open(des_file, 'r') as f:
            for line in f:
                if ':' in line and not line.startswith('#'):
                    parts = line.strip().split(':', 1)
                    if len(parts) == 2:
                        try:
                            idx = int(parts[0])
                            label = parts[1].strip()
                            # Skip removed regions
                            if idx not in [0, 42, 117]:
                                destrieux_labels[idx] = label
                        except ValueError:
                            continue
    
    print(f"   Loaded {len(levinson_labels)} Levinson labels")
    print(f"   Loaded {len(tian_labels)} Tian labels")
    print(f"   Loaded {len(destrieux_labels)} Destrieux labels")
    
    return levinson_labels, tian_labels, destrieux_labels

def create_sequential_label_file(reindex_map, levinson_labels, tian_labels, destrieux_labels):
    """Create new label file with sequential indices"""
    
    print("\n📝 Creating Sequential Label File...")
    
    label_path = Path("levtiades_atlas/final_atlas/levtiades_labels_sequential.txt")
    
    with open(label_path, 'w') as f:
        f.write("# Levtiades Atlas - Sequential Labels (1-207)\n")
        f.write("# Reindexed from hierarchical scheme to sequential numbering\n")
        f.write("# Format: ID: Region_Name [Source_Atlas]\n\n")
        
        # Create reverse mapping for easy lookup
        reverse_map = {new_idx: old_idx for old_idx, new_idx in reindex_map.items()}
        
        # Write all regions in sequential order
        for new_idx in sorted(reverse_map.keys()):
            old_idx = reverse_map[new_idx]
            
            # Determine source and get name
            if old_idx < 100:
                # Levinson
                source = "Levinson"
                name = levinson_labels.get(old_idx, f"Levinson_{old_idx}")
            elif old_idx < 200:
                # Tian
                source = "Tian"
                original_idx = old_idx - 100
                name = tian_labels.get(original_idx, f"Tian_{original_idx}")
            else:
                # Destrieux
                source = "Destrieux"
                original_idx = old_idx - 200
                name = destrieux_labels.get(original_idx, f"Destrieux_{original_idx}")
            
            f.write(f"{new_idx}: {name} [${source}]\n")
    
    print(f"✅ Sequential label file created: {label_path}")

def create_sequential_lookup_table(reindex_map, levinson_labels, tian_labels, destrieux_labels):
    """Create MRIcrogl lookup table with sequential indices"""
    
    print("\n🎨 Creating Sequential Lookup Table...")
    
    lookup_path = Path("levtiades_atlas/final_atlas/levtiades_lookup_table_sequential.txt")
    
    with open(lookup_path, 'w') as f:
        f.write("# Levtiades Atlas Sequential Lookup Table (MRIcrogl compatible)\n")
        f.write("# Index\\tR\\tG\\tB\\tLabel\n")
        f.write("# Format: label_number<tab>red<tab>green<tab>blue<tab>label_name\n\n")
        
        # Create reverse mapping
        reverse_map = {new_idx: old_idx for old_idx, new_idx in reindex_map.items()}
        
        # Write all regions in sequential order with colors
        for new_idx in sorted(reverse_map.keys()):
            old_idx = reverse_map[new_idx]
            
            # Determine source, name, and color scheme
            if old_idx < 100:
                # Levinson - Red/Orange tones
                source = "Levinson"
                name = levinson_labels.get(old_idx, f"Levinson_{old_idx}")
                r = 255 - (old_idx * 20)
                g = 100 + (old_idx * 30)
                b = 50
            elif old_idx < 200:
                # Tian - Green tones
                source = "Tian"
                original_idx = old_idx - 100
                name = tian_labels.get(original_idx, f"Tian_{original_idx}")
                r = 50 + (original_idx % 5) * 20
                g = 150 + (original_idx % 10) * 10
                b = 100 + (original_idx % 5) * 20
            else:
                # Destrieux - Blue tones
                source = "Destrieux"
                original_idx = old_idx - 200
                name = destrieux_labels.get(original_idx, f"Destrieux_{original_idx}")
                r = 100 + (original_idx % 5) * 20
                g = 100 + (original_idx % 10) * 10
                b = 200 + (original_idx % 3) * 20
            
            # Ensure RGB values are valid
            r = min(255, max(0, r))
            g = min(255, max(0, g))
            b = min(255, max(0, b))
            
            f.write(f"{new_idx}\\t{r}\\t{g}\\t{b}\\t{source}:{name}\n")
    
    print(f"✅ Sequential lookup table created: {lookup_path}")

def create_sequential_individual_rois(reindex_map, atlas_img):
    """Create individual ROI files with sequential indices"""
    
    print("\n🎯 Creating Sequential Individual ROI Files...")
    
    # Load atlas data
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # Create output directory
    roi_dir = Path("levtiades_atlas/individual_rois_sequential")
    roi_dir.mkdir(exist_ok=True)
    
    # Create reverse mapping
    reverse_map = {new_idx: old_idx for old_idx, new_idx in reindex_map.items()}
    
    # Create ROI files in sequential order
    for new_idx in sorted(reverse_map.keys()):
        old_idx = reverse_map[new_idx]
        
        # Create binary mask for this region (using old index in current atlas)
        roi_mask = (atlas_data == old_idx).astype(np.uint8)
        voxel_count = np.sum(roi_mask)
        
        if voxel_count > 0:  # Only create files for regions that exist
            roi_img = nib.Nifti1Image(roi_mask, atlas_img.affine, atlas_img.header)
            
            # Create filename with sequential index
            filename = f"levtiades_roi_{new_idx:03d}.nii.gz"
            output_path = roi_dir / filename
            nib.save(roi_img, output_path)
            
            if new_idx % 50 == 0:
                print(f"   Created {new_idx}/207 ROI files...")
    
    print(f"✅ Created 207 sequential ROI files in: {roi_dir}")

def create_index_mapping_reference():
    """Create reference file showing old->new index mappings"""
    
    print("\n📋 Creating Index Mapping Reference...")
    
    # Load mapping
    with open("levtiades_atlas/reindexing_map.json", 'r') as f:
        reindex_map = json.load(f)
    
    # Convert keys back to integers
    reindex_map = {int(k): v for k, v in reindex_map.items()}
    
    # Load labels
    levinson_labels, tian_labels, destrieux_labels = load_original_labels()
    
    # Create reference table
    mapping_data = []
    for old_idx, new_idx in sorted(reindex_map.items()):
        # Determine source and name
        if old_idx < 100:
            source = "Levinson"
            name = levinson_labels.get(old_idx, f"Levinson_{old_idx}")
        elif old_idx < 200:
            source = "Tian"
            original_idx = old_idx - 100
            name = tian_labels.get(original_idx, f"Tian_{original_idx}")
        else:
            source = "Destrieux"
            original_idx = old_idx - 200
            name = destrieux_labels.get(original_idx, f"Destrieux_{original_idx}")
        
        mapping_data.append({
            'old_index': old_idx,
            'new_index': new_idx,
            'source': source,
            'region_name': name
        })
    
    # Save as CSV
    df = pd.DataFrame(mapping_data)
    csv_path = Path("levtiades_atlas/index_mapping_reference.csv")
    df.to_csv(csv_path, index=False)
    
    print(f"✅ Index mapping reference saved: {csv_path}")

if __name__ == "__main__":
    print("🔄 REINDEXING LEVTIADES ATLAS TO SEQUENTIAL 1-207")
    print("=" * 55)
    
    # Step 1: Create reindexing map
    reindex_map, atlas_img, atlas_data = create_reindexing_map()
    
    # Step 2: Create reindexed atlas
    new_atlas_data, new_atlas_img = create_reindexed_atlas(reindex_map, atlas_img, atlas_data)
    
    if new_atlas_data is None:
        print("❌ Reindexing failed!")
        exit(1)
    
    # Step 3: Load original labels
    levinson_labels, tian_labels, destrieux_labels = load_original_labels()
    
    # Step 4: Create sequential label file
    create_sequential_label_file(reindex_map, levinson_labels, tian_labels, destrieux_labels)
    
    # Step 5: Create sequential lookup table
    create_sequential_lookup_table(reindex_map, levinson_labels, tian_labels, destrieux_labels)
    
    # Step 6: Create sequential individual ROIs
    create_sequential_individual_rois(reindex_map, new_atlas_img)
    
    # Step 7: Create mapping reference
    create_index_mapping_reference()
    
    print("\n✅ SEQUENTIAL REINDEXING COMPLETE!")
    print("=" * 35)
    print("📊 New atlas: levtiades_sequential.nii.gz")
    print("📋 New labels: levtiades_labels_sequential.txt")
    print("🎨 New lookup: levtiades_lookup_table_sequential.txt")
    print("🎯 New ROIs: individual_rois_sequential/")
    print("📋 Mapping: index_mapping_reference.csv")
    print("🏷️ Range: 1-207 (no gaps)")