#!/usr/bin/env python3
"""
Create spaced atlas for MRIcroGL visualization and with_overlaps analysis
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import pandas as pd
from scipy import ndimage

def create_spaced_atlas():
    """Create atlas with spaced indices (300, 350, 400...) for MRIcroGL visualization"""
    
    print("🎨 CREATING SPACED ATLAS FOR MRIcroGL")
    print("=" * 40)
    
    # Load sequential atlas
    atlas_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # Create spaced version
    spaced_data = np.zeros_like(atlas_data, dtype=np.int16)
    
    unique_labels = sorted(np.unique(atlas_data[atlas_data > 0]))
    print(f"   Converting {len(unique_labels)} regions to spaced indices...")
    
    for sequential_idx in unique_labels:
        spaced_idx = 300 + (sequential_idx - 1) * 50  # 300, 350, 400, 450...
        mask = atlas_data == sequential_idx
        spaced_data[mask] = spaced_idx
        
        if sequential_idx <= 10 or sequential_idx % 50 == 0:
            print(f"     Region {sequential_idx} -> {spaced_idx}")
    
    # Save spaced atlas
    spaced_img = nib.Nifti1Image(spaced_data, atlas_img.affine, atlas_img.header)
    spaced_path = Path("levtiades_atlas/final_atlas/no_overlaps/levtiades_spaced_mricrogl.nii.gz")
    nib.save(spaced_img, spaced_path)
    
    print(f"✅ Spaced atlas created: {spaced_path}")
    print(f"   Index range: 300 - {300 + (len(unique_labels)-1) * 50}")
    
    return spaced_path

def create_with_overlaps_atlas():
    """Create atlas showing overlapping regions and analyze overlaps"""
    
    print("\n🔍 CREATING WITH_OVERLAPS ATLAS")
    print("=" * 35)
    
    # Load aligned individual atlases
    aligned_dir = Path("levtiades_atlas/aligned_atlases")
    
    lev_img = nib.load(aligned_dir / "levinson_aligned.nii.gz")
    tian_img = nib.load(aligned_dir / "tian_aligned.nii.gz")
    des_img = nib.load(aligned_dir / "destrieux_aligned.nii.gz")
    
    lev_data = lev_img.get_fdata().astype(int)
    tian_data = tian_img.get_fdata().astype(int)
    des_data = des_img.get_fdata().astype(int)
    
    print("   Analyzing overlaps between atlases...")
    
    # Create masks for each atlas
    lev_mask = lev_data > 0
    tian_mask = tian_data > 0
    des_mask = des_data > 0
    
    # Find overlap regions
    lev_tian_overlap = lev_mask & tian_mask
    lev_des_overlap = lev_mask & des_mask
    tian_des_overlap = tian_mask & des_mask
    all_three_overlap = lev_mask & tian_mask & des_mask
    
    # Calculate overlap statistics
    total_brain_voxels = np.sum(lev_mask | tian_mask | des_mask)
    
    overlap_stats = {
        'levinson_voxels': np.sum(lev_mask),
        'tian_voxels': np.sum(tian_mask),
        'destrieux_voxels': np.sum(des_mask),
        'total_brain_voxels': total_brain_voxels,
        'lev_tian_overlap': np.sum(lev_tian_overlap),
        'lev_des_overlap': np.sum(lev_des_overlap),
        'tian_des_overlap': np.sum(tian_des_overlap),
        'all_three_overlap': np.sum(all_three_overlap)
    }
    
    print(f"   Levinson voxels: {overlap_stats['levinson_voxels']:,}")
    print(f"   Tian voxels: {overlap_stats['tian_voxels']:,}")
    print(f"   Destrieux voxels: {overlap_stats['destrieux_voxels']:,}")
    print(f"   Total brain voxels: {overlap_stats['total_brain_voxels']:,}")
    print(f"   Lev-Tian overlaps: {overlap_stats['lev_tian_overlap']:,}")
    print(f"   Lev-Des overlaps: {overlap_stats['lev_des_overlap']:,}")
    print(f"   Tian-Des overlaps: {overlap_stats['tian_des_overlap']:,}")
    print(f"   All-three overlaps: {overlap_stats['all_three_overlap']:,}")
    
    # Create combined with_overlaps atlas using multichannel approach
    print("   Creating multichannel with_overlaps atlas...")
    
    # Create 4D multichannel image (each atlas as separate channel)
    multichannel_data = np.zeros((*lev_data.shape, 4), dtype=np.int16)
    
    # Channel 0: Levinson (indices 1-5)
    multichannel_data[:, :, :, 0] = lev_data
    
    # Channel 1: Tian (indices 1-54) 
    multichannel_data[:, :, :, 1] = tian_data
    
    # Channel 2: Destrieux (indices 1-148+)
    multichannel_data[:, :, :, 2] = des_data
    
    # Channel 3: Overlap map
    overlap_map = np.zeros_like(lev_data, dtype=np.int16)
    overlap_map[lev_tian_overlap] = 1  # Lev-Tian overlaps
    overlap_map[lev_des_overlap] = 2   # Lev-Des overlaps  
    overlap_map[tian_des_overlap] = 3  # Tian-Des overlaps
    overlap_map[all_three_overlap] = 4 # All-three overlaps
    multichannel_data[:, :, :, 3] = overlap_map
    
    # Create flat version showing priority resolution
    print("   Creating flat with_overlaps atlas (hierarchy: Levinson > Tian > Destrieux)...")
    
    flat_data = np.zeros_like(lev_data, dtype=np.int16)
    
    # Apply hierarchical priority: Levinson > Tian > Destrieux
    # Start with Destrieux (lowest priority)
    unique_des = sorted(np.unique(des_data[des_data > 0]))
    for des_idx in unique_des:
        mask = des_data == des_idx
        flat_data[mask] = 2000 + des_idx  # Destrieux: 2001-2148+
    
    # Add Tian (medium priority) - overwrites Destrieux where they overlap
    unique_tian = sorted(np.unique(tian_data[tian_data > 0]))
    for tian_idx in unique_tian:
        mask = tian_data == tian_idx
        flat_data[mask] = 1000 + tian_idx  # Tian: 1001-1054
    
    # Add Levinson (highest priority) - overwrites everything
    unique_lev = sorted(np.unique(lev_data[lev_data > 0]))
    for lev_idx in unique_lev:
        mask = lev_data == lev_idx
        flat_data[mask] = lev_idx  # Levinson: 1-5
    
    # Save atlases
    with_overlaps_dir = Path("levtiades_atlas/final_atlas/with_overlaps")
    with_overlaps_dir.mkdir(exist_ok=True)
    
    # Save multichannel version
    multichannel_img = nib.Nifti1Image(multichannel_data, lev_img.affine, lev_img.header)
    multichannel_path = with_overlaps_dir / "levtiades_multichannel.nii.gz"
    nib.save(multichannel_img, multichannel_path)
    
    # Save flat version
    flat_img = nib.Nifti1Image(flat_data, lev_img.affine, lev_img.header)
    flat_path = with_overlaps_dir / "levtiades_flat_with_overlaps.nii.gz"
    nib.save(flat_img, flat_path)
    
    print(f"✅ Multichannel atlas: {multichannel_path}")
    print(f"✅ Flat with overlaps: {flat_path}")
    
    return overlap_stats, with_overlaps_dir

def analyze_region_overlaps(overlap_stats, output_dir):
    """Analyze which specific regions overlap with each other"""
    
    print("\n🔬 ANALYZING SPECIFIC REGION OVERLAPS")
    print("=" * 40)
    
    # Load aligned atlases
    aligned_dir = Path("levtiades_atlas/aligned_atlases")
    
    lev_img = nib.load(aligned_dir / "levinson_aligned.nii.gz")
    tian_img = nib.load(aligned_dir / "tian_aligned.nii.gz") 
    des_img = nib.load(aligned_dir / "destrieux_aligned.nii.gz")
    
    lev_data = lev_img.get_fdata().astype(int)
    tian_data = tian_img.get_fdata().astype(int)
    des_data = des_img.get_fdata().astype(int)
    
    # Load mapping data for region names
    mapping_df = pd.read_csv("levtiades_atlas/index_mapping_reference.csv")
    
    # Load Tian labels
    tian_labels = {}
    tian_file = Path("data/Tian2020MSA_v1.4/3T/Subcortex-Only/Tian_Subcortex_S4_3T_label.txt")
    if tian_file.exists():
        with open(tian_file, 'r') as f:
            for i, line in enumerate(f, 1):
                label = line.strip()
                if label:
                    tian_labels[i] = label
    
    overlap_details = []
    
    # Analyze Levinson-Tian overlaps
    print("   Analyzing Levinson-Tian overlaps...")
    for lev_idx in sorted(np.unique(lev_data[lev_data > 0])):
        lev_mask = lev_data == lev_idx
        lev_name = mapping_df[mapping_df['old_index'] == lev_idx]['region_name'].iloc[0] if len(mapping_df[mapping_df['old_index'] == lev_idx]) > 0 else f"Levinson_{lev_idx}"
        
        for tian_idx in sorted(np.unique(tian_data[tian_data > 0])):
            tian_mask = tian_data == tian_idx
            overlap_mask = lev_mask & tian_mask
            overlap_voxels = np.sum(overlap_mask)
            
            if overlap_voxels > 0:
                tian_name = tian_labels.get(tian_idx, f"Tian_{tian_idx}")
                lev_total = np.sum(lev_mask)
                tian_total = np.sum(tian_mask)
                
                overlap_details.append({
                    'overlap_type': 'Levinson-Tian',
                    'region1_atlas': 'Levinson',
                    'region1_index': lev_idx,
                    'region1_name': lev_name,
                    'region1_total_voxels': lev_total,
                    'region2_atlas': 'Tian',
                    'region2_index': tian_idx,
                    'region2_name': tian_name,
                    'region2_total_voxels': tian_total,
                    'overlap_voxels': overlap_voxels,
                    'overlap_percent_region1': round((overlap_voxels / lev_total) * 100, 2),
                    'overlap_percent_region2': round((overlap_voxels / tian_total) * 100, 2)
                })
                print(f"     {lev_name} ↔ {tian_name}: {overlap_voxels} voxels")
    
    # Analyze Levinson-Destrieux overlaps
    print("   Analyzing Levinson-Destrieux overlaps...")
    for lev_idx in sorted(np.unique(lev_data[lev_data > 0])):
        lev_mask = lev_data == lev_idx
        lev_name = mapping_df[mapping_df['old_index'] == lev_idx]['region_name'].iloc[0] if len(mapping_df[mapping_df['old_index'] == lev_idx]) > 0 else f"Levinson_{lev_idx}"
        
        for des_idx in sorted(np.unique(des_data[des_data > 0])):
            des_mask = des_data == des_idx
            overlap_mask = lev_mask & des_mask
            overlap_voxels = np.sum(overlap_mask)
            
            if overlap_voxels > 0:
                des_row = mapping_df[mapping_df['old_index'] == (200 + des_idx)]
                des_name = des_row['region_name'].iloc[0] if len(des_row) > 0 else f"Destrieux_{des_idx}"
                if isinstance(des_name, str) and "')," in des_name:
                    des_name = des_name.split("'")[1]
                    
                lev_total = np.sum(lev_mask)
                des_total = np.sum(des_mask)
                
                overlap_details.append({
                    'overlap_type': 'Levinson-Destrieux',
                    'region1_atlas': 'Levinson',
                    'region1_index': lev_idx,
                    'region1_name': lev_name,
                    'region1_total_voxels': lev_total,
                    'region2_atlas': 'Destrieux',
                    'region2_index': des_idx,
                    'region2_name': des_name,
                    'region2_total_voxels': des_total,
                    'overlap_voxels': overlap_voxels,
                    'overlap_percent_region1': round((overlap_voxels / lev_total) * 100, 2),
                    'overlap_percent_region2': round((overlap_voxels / des_total) * 100, 2)
                })
                print(f"     {lev_name} ↔ {des_name}: {overlap_voxels} voxels")
    
    # Analyze Tian-Destrieux overlaps (top 20 only due to volume)
    print("   Analyzing Tian-Destrieux overlaps (showing top 20)...")
    tian_des_overlaps = []
    
    for tian_idx in sorted(np.unique(tian_data[tian_data > 0])):
        tian_mask = tian_data == tian_idx
        tian_name = tian_labels.get(tian_idx, f"Tian_{tian_idx}")
        
        for des_idx in sorted(np.unique(des_data[des_data > 0])):
            des_mask = des_data == des_idx
            overlap_mask = tian_mask & des_mask
            overlap_voxels = np.sum(overlap_mask)
            
            if overlap_voxels > 0:
                des_row = mapping_df[mapping_df['old_index'] == (200 + des_idx)]
                des_name = des_row['region_name'].iloc[0] if len(des_row) > 0 else f"Destrieux_{des_idx}"
                if isinstance(des_name, str) and "')," in des_name:
                    des_name = des_name.split("'")[1]
                
                tian_total = np.sum(tian_mask)
                des_total = np.sum(des_mask)
                
                tian_des_overlaps.append({
                    'overlap_type': 'Tian-Destrieux',
                    'region1_atlas': 'Tian',
                    'region1_index': tian_idx,
                    'region1_name': tian_name,
                    'region1_total_voxels': tian_total,
                    'region2_atlas': 'Destrieux',
                    'region2_index': des_idx,
                    'region2_name': des_name,
                    'region2_total_voxels': des_total,
                    'overlap_voxels': overlap_voxels,
                    'overlap_percent_region1': round((overlap_voxels / tian_total) * 100, 2),
                    'overlap_percent_region2': round((overlap_voxels / des_total) * 100, 2)
                })
    
    # Sort by overlap size and take top 20
    tian_des_overlaps.sort(key=lambda x: x['overlap_voxels'], reverse=True)
    for overlap in tian_des_overlaps[:20]:
        print(f"     {overlap['region1_name']} ↔ {overlap['region2_name']}: {overlap['overlap_voxels']} voxels")
        overlap_details.append(overlap)
    
    # Save detailed overlap analysis
    if overlap_details:
        overlap_df = pd.DataFrame(overlap_details)
        overlap_csv = output_dir / "region_overlap_analysis.csv"
        overlap_df.to_csv(overlap_csv, index=False)
        print(f"✅ Detailed overlap analysis: {overlap_csv}")
    
    return overlap_details

def create_overlap_report(overlap_stats, overlap_details, output_dir):
    """Create comprehensive overlap analysis report"""
    
    print("\n📋 CREATING OVERLAP ANALYSIS REPORT")
    print("=" * 36)
    
    report_path = output_dir / "overlap_analysis_report.txt"
    
    with open(report_path, 'w') as f:
        f.write("LEVTIADES ATLAS OVERLAP ANALYSIS REPORT\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("Atlas files analyzed:\n")
        f.write("- levtiades_atlas/aligned_atlases/levinson_aligned.nii.gz\n")
        f.write("- levtiades_atlas/aligned_atlases/tian_aligned.nii.gz\n")
        f.write("- levtiades_atlas/aligned_atlases/destrieux_aligned.nii.gz\n\n")
        
        # Overall statistics
        f.write("OVERALL OVERLAP STATISTICS\n")
        f.write("-" * 26 + "\n")
        f.write(f"Total brain coverage: {overlap_stats['total_brain_voxels']:,} voxels\n")
        f.write(f"Levinson coverage: {overlap_stats['levinson_voxels']:,} voxels ({overlap_stats['levinson_voxels']/overlap_stats['total_brain_voxels']*100:.1f}%)\n")
        f.write(f"Tian coverage: {overlap_stats['tian_voxels']:,} voxels ({overlap_stats['tian_voxels']/overlap_stats['total_brain_voxels']*100:.1f}%)\n")
        f.write(f"Destrieux coverage: {overlap_stats['destrieux_voxels']:,} voxels ({overlap_stats['destrieux_voxels']/overlap_stats['total_brain_voxels']*100:.1f}%)\n\n")
        
        f.write("OVERLAP SUMMARY\n")
        f.write("-" * 15 + "\n")
        f.write(f"Levinson-Tian overlaps: {overlap_stats['lev_tian_overlap']:,} voxels\n")
        f.write(f"Levinson-Destrieux overlaps: {overlap_stats['lev_des_overlap']:,} voxels\n")
        f.write(f"Tian-Destrieux overlaps: {overlap_stats['tian_des_overlap']:,} voxels\n")
        f.write(f"Three-way overlaps: {overlap_stats['all_three_overlap']:,} voxels\n\n")
        
        # Overlap percentages
        total_overlap = overlap_stats['lev_tian_overlap'] + overlap_stats['lev_des_overlap'] + overlap_stats['tian_des_overlap']
        f.write(f"Total overlapping voxels: {total_overlap:,} ({total_overlap/overlap_stats['total_brain_voxels']*100:.1f}% of brain)\n\n")
        
        # Resolution hierarchy explanation
        f.write("OVERLAP RESOLUTION HIERARCHY\n")
        f.write("-" * 28 + "\n")
        f.write("When regions from multiple atlases occupy the same voxel,\n")
        f.write("the final atlas uses this priority hierarchy:\n")
        f.write("1. LEVINSON (brainstem) - HIGHEST priority\n")
        f.write("2. TIAN (subcortical) - MEDIUM priority\n")
        f.write("3. DESTRIEUX (cortical) - LOWEST priority\n\n")
        f.write("This ensures anatomically critical brainstem and subcortical\n")
        f.write("structures are preserved over cortical regions when overlaps occur.\n\n")
        
        # Specific region overlaps
        if overlap_details:
            f.write("SPECIFIC REGION OVERLAPS\n")
            f.write("-" * 23 + "\n")
            
            # Group by overlap type
            by_type = {}
            for detail in overlap_details:
                overlap_type = detail['overlap_type']
                if overlap_type not in by_type:
                    by_type[overlap_type] = []
                by_type[overlap_type].append(detail)
            
            for overlap_type, details in by_type.items():
                f.write(f"\n{overlap_type.upper()}:\n")
                for detail in details:
                    f.write(f"  {detail['region1_name']} ↔ {detail['region2_name']}\n")
                    f.write(f"    Overlap: {detail['overlap_voxels']} voxels\n")
                    f.write(f"    % of {detail['region1_atlas']}: {detail['overlap_percent_region1']}%\n")
                    f.write(f"    % of {detail['region2_atlas']}: {detail['overlap_percent_region2']}%\n\n")
        
        f.write("FILES CREATED\n")
        f.write("-" * 13 + "\n")
        f.write("- levtiades_multichannel.nii.gz: 4D image with each atlas as separate channel\n")
        f.write("- levtiades_flat_with_overlaps.nii.gz: 3D image with hierarchy-resolved overlaps\n")
        f.write("- region_overlap_analysis.csv: Detailed overlap statistics\n")
        f.write("- overlap_analysis_report.txt: This comprehensive report\n\n")
        
        f.write("INTERPRETATION\n")
        f.write("-" * 14 + "\n")
        f.write("Overlaps are expected when combining atlases from different sources\n")
        f.write("as they may define boundaries differently or have different resolution.\n")
        f.write("The hierarchical resolution ensures the most functionally important\n")
        f.write("regions (brainstem) take precedence over less critical ones (cortical).\n")
    
    print(f"✅ Overlap report saved: {report_path}")

def main():
    """Main function to create all atlas variants and analyses"""
    
    # Step 1: Clean up and create spaced atlas
    spaced_path = create_spaced_atlas()
    
    # Step 2: Create with_overlaps atlas and analyze
    overlap_stats, output_dir = create_with_overlaps_atlas()
    
    # Step 3: Analyze specific region overlaps
    overlap_details = analyze_region_overlaps(overlap_stats, output_dir)
    
    # Step 4: Create comprehensive report
    create_overlap_report(overlap_stats, overlap_details, output_dir)
    
    print("\n✅ ALL ATLAS VARIANTS AND ANALYSES COMPLETE!")
    print("=" * 45)
    print("📊 Sequential atlas: levtiades_atlas/final_atlas/no_overlaps/levtiades_sequential.nii.gz")
    print("🎨 Spaced atlas: levtiades_atlas/final_atlas/no_overlaps/levtiades_spaced_mricrogl.nii.gz") 
    print("🔍 With overlaps: levtiades_atlas/final_atlas/with_overlaps/")
    print("📋 Reports: levtiades_atlas/final_atlas/with_overlaps/overlap_analysis_report.txt")

if __name__ == "__main__":
    main()