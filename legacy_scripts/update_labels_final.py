#!/usr/bin/env python3
"""
Update Levtiades Atlas Labels - Final Version
Remove '_complete' suffix and incorporate proper Tian labels
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import json

def load_proper_tian_labels():
    """Load Tian labels from the source file"""
    
    print("📋 Loading Proper Tian Labels...")
    
    tian_file = Path("data/Tian2020MSA_v1.4/3T/Subcortex-Only/Tian_Subcortex_S4_3T_label.txt")
    
    if not tian_file.exists():
        print(f"❌ Tian label file not found: {tian_file}")
        return {}
    
    tian_labels = {}
    with open(tian_file, 'r') as f:
        for i, line in enumerate(f, 1):
            label = line.strip()
            if label:  # Skip empty lines
                tian_labels[i] = label
    
    print(f"   Loaded {len(tian_labels)} Tian labels")
    return tian_labels

def load_destrieux_labels():
    """Load Destrieux labels from existing file"""
    
    print("📋 Loading Destrieux Labels...")
    
    des_file = Path("tiandes_atlas/raw_atlases/destrieux_labels.txt")
    des_labels = {}
    
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
                                # Extract clean name from tuple format like "(1, 'L G_and_S_frontomargin')"
                                if label.startswith('(') and ', \'' in label and label.endswith('\')'):
                                    # Extract just the region name from the tuple
                                    clean_name = label.split(', \'')[1][:-2]  # Remove ') at end
                                    des_labels[idx] = clean_name
                                else:
                                    des_labels[idx] = label
                        except ValueError:
                            continue
    
    print(f"   Loaded {len(des_labels)} Destrieux labels")
    return des_labels

def create_updated_label_file():
    """Create updated label file with proper Tian labels"""
    
    print("📝 Creating Updated Label File...")
    
    # Load reindexing map
    with open("levtiades_atlas/reindexing_map.json", 'r') as f:
        reindex_map = json.load(f)
    
    # Convert keys back to integers
    reindex_map = {int(k): v for k, v in reindex_map.items()}
    
    # Load proper labels
    levinson_labels = {
        1: 'Locus_Coeruleus_LC',
        2: 'Nucleus_Tractus_Solitarius_NTS',
        3: 'Ventral_Tegmental_Area_VTA',
        4: 'Periaqueductal_Gray_PAG',
        5: 'Dorsal_Raphe_Nucleus_DRN'
    }
    
    tian_labels = load_proper_tian_labels()
    destrieux_labels = load_destrieux_labels()
    
    # Create label file (remove '_complete' suffix)
    label_path = Path("levtiades_atlas/final_atlas/levtiades_labels.txt")
    
    with open(label_path, 'w') as f:
        f.write("# Levtiades Atlas - Complete Brain Parcellation Labels\\n")
        f.write("# Sequential indexing 1-207 (no gaps)\\n")
        f.write("#\\n")
        f.write("# Combining three complementary atlases:\\n")
        f.write("# 1. Levinson-Bari Limbic Brainstem Atlas (Levinson et al. 2022)\\n")
        f.write("#    - 5 critical brainstem/midbrain nuclei\\n")
        f.write("# 2. Tian Subcortex S4 - Melbourne Subcortical Atlas (Tian et al. 2020)\\n")
        f.write("#    - 54 subcortical structures at maximum resolution\\n")
        f.write("#    - https://github.com/yetianmed/subcortex\\n")
        f.write("# 3. Destrieux Cortical Atlas (Destrieux et al. 2010)\\n")
        f.write("#    - 148 cortical regions (wall/background removed)\\n")
        f.write("#\\n")
        f.write("# Hierarchical resolution: Midbrain > Subcortical > Cortical\\n")
        f.write("# Format: ID: Region_Name [Source_Atlas]\\n\\n")
        
        # Create reverse mapping for easy lookup
        reverse_map = {new_idx: old_idx for old_idx, new_idx in reindex_map.items()}
        
        # Count regions by source
        levinson_count = len([l for l in reverse_map.values() if l < 100])
        tian_count = len([l for l in reverse_map.values() if 100 <= l < 200])
        destrieux_count = len([l for l in reverse_map.values() if l >= 200])
        
        f.write(f"# Total regions: {len(reverse_map)}\\n")
        f.write(f"# Levinson: {levinson_count} regions (1-{levinson_count})\\n")
        f.write(f"# Tian: {tian_count} regions ({levinson_count+1}-{levinson_count+tian_count})\\n")
        f.write(f"# Destrieux: {destrieux_count} regions ({levinson_count+tian_count+1}-{len(reverse_map)})\\n\\n")
        
        # Write Levinson regions
        f.write("# LEVINSON-BARI LIMBIC BRAINSTEM NUCLEI\\n")
        f.write("# Critical psychiatric circuit nodes\\n")
        for new_idx in sorted([k for k, v in reverse_map.items() if v < 100]):
            old_idx = reverse_map[new_idx]
            name = levinson_labels.get(old_idx, f"Levinson_{old_idx}")
            f.write(f"{new_idx}: {name} [Levinson-Bari]\\n")
        
        # Write Tian regions
        f.write("\\n# TIAN SUBCORTEX S4 - MELBOURNE SUBCORTICAL ATLAS\\n")
        f.write("# Scale IV (maximum resolution) - 54 subcortical structures\\n")
        f.write("# Reference: https://github.com/yetianmed/subcortex\\n")
        tian_new_indices = sorted([k for k, v in reverse_map.items() if 100 <= v < 200])
        for i, new_idx in enumerate(tian_new_indices, 1):
            old_idx = reverse_map[new_idx]
            name = tian_labels.get(i, f"Tian_S4_{i}")
            f.write(f"{new_idx}: {name} [Tian-Melbourne-S4]\\n")
        
        # Write Destrieux regions
        f.write("\\n# DESTRIEUX CORTICAL PARCELLATION\\n")
        f.write("# 148 cortical regions (medial wall and background removed)\\n")
        for new_idx in sorted([k for k, v in reverse_map.items() if v >= 200]):
            old_idx = reverse_map[new_idx]
            original_idx = old_idx - 200
            name = destrieux_labels.get(original_idx, f"Destrieux_{original_idx}")
            f.write(f"{new_idx}: {name} [Destrieux]\\n")
    
    print(f"✅ Updated label file created: {label_path}")
    return len(reverse_map)

def create_updated_lookup_table():
    """Create updated lookup table with proper Tian labels"""
    
    print("🎨 Creating Updated Lookup Table...")
    
    # Load reindexing map
    with open("levtiades_atlas/reindexing_map.json", 'r') as f:
        reindex_map = json.load(f)
    
    # Convert keys back to integers
    reindex_map = {int(k): v for k, v in reindex_map.items()}
    
    # Load proper labels
    levinson_labels = {
        1: 'Locus_Coeruleus_LC',
        2: 'Nucleus_Tractus_Solitarius_NTS',
        3: 'Ventral_Tegmental_Area_VTA',
        4: 'Periaqueductal_Gray_PAG',
        5: 'Dorsal_Raphe_Nucleus_DRN'
    }
    
    tian_labels = load_proper_tian_labels()
    destrieux_labels = load_destrieux_labels()
    
    # Create lookup table (remove '_complete' suffix)
    lookup_path = Path("levtiades_atlas/final_atlas/levtiades_lookup_table.txt")
    
    with open(lookup_path, 'w') as f:
        f.write("# Levtiades Atlas Lookup Table (MRIcrogl compatible)\\n")
        f.write("# Sequential indexing 1-207\\n")
        f.write("# Index\\tR\\tG\\tB\\tLabel\\n")
        f.write("# Format: label_number<tab>red<tab>green<tab>blue<tab>source:label_name\\n\\n")
        
        # Create reverse mapping
        reverse_map = {new_idx: old_idx for old_idx, new_idx in reindex_map.items()}
        
        # Write all regions in sequential order with colors
        tian_new_indices = sorted([k for k, v in reverse_map.items() if 100 <= v < 200])
        tian_counter = 1
        
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
                source = "Tian-S4"
                name = tian_labels.get(tian_counter, f"Tian_S4_{tian_counter}")
                tian_counter += 1
                r = 50 + (new_idx % 5) * 20
                g = 150 + (new_idx % 10) * 10
                b = 100 + (new_idx % 5) * 20
            else:
                # Destrieux - Blue tones
                source = "Destrieux"
                original_idx = old_idx - 200
                name = destrieux_labels.get(original_idx, f"Destrieux_{original_idx}")
                r = 100 + (new_idx % 5) * 20
                g = 100 + (new_idx % 10) * 10
                b = 200 + (new_idx % 3) * 20
            
            # Ensure RGB values are valid
            r = min(255, max(0, r))
            g = min(255, max(0, g))
            b = min(255, max(0, b))
            
            f.write(f"{new_idx}\\t{r}\\t{g}\\t{b}\\t{source}:{name}\\n")
    
    print(f"✅ Updated lookup table created: {lookup_path}")

def cleanup_old_files():
    """Remove old files with '_complete' suffix"""
    
    print("🧹 Cleaning Up Old Files...")
    
    old_files = [
        "levtiades_atlas/final_atlas/levtiades_labels_complete.txt",
        "levtiades_atlas/final_atlas/levtiades_lookup_table_complete.txt"
    ]
    
    removed_count = 0
    for old_file in old_files:
        old_path = Path(old_file)
        if old_path.exists():
            old_path.unlink()
            print(f"   Removed: {old_path.name}")
            removed_count += 1
    
    if removed_count == 0:
        print("   No old files to remove")
    else:
        print(f"✅ Removed {removed_count} old files")

if __name__ == "__main__":
    print("🔧 UPDATING LEVTIADES ATLAS LABELS")
    print("=" * 40)
    
    # Step 1: Create updated label file
    total_regions = create_updated_label_file()
    
    # Step 2: Create updated lookup table
    create_updated_lookup_table()
    
    # Step 3: Clean up old files
    cleanup_old_files()
    
    print("\\n✅ LABEL UPDATE COMPLETE!")
    print("=" * 25)
    print(f"📋 New files:")
    print("   levtiades_labels.txt")
    print("   levtiades_lookup_table.txt")
    print(f"🧠 {total_regions} regions with proper Tian S4 labels")
    print("🔗 Melbourne Subcortex reference included")