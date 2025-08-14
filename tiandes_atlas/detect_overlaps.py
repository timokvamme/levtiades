#!/usr/bin/env python3
"""
Overlap Detection Script for TianDes Atlas
Analyzes conflicts between Tian subcortical and Destrieux cortical atlases
"""

import nibabel as nib
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

def load_label_files():
    """Load region labels for both atlases"""
    
    base_dir = Path("tiandes_atlas/raw_atlases")
    
    # Load Tian labels
    tian_labels = {}
    with open(base_dir / "tian_labels.txt", 'r') as f:
        for line in f:
            if line.strip() and ':' in line:
                idx, label = line.strip().split(':', 1)
                tian_labels[int(idx)] = label.strip()
    
    # Load Destrieux labels  
    des_labels = {}
    with open(base_dir / "destrieux_labels.txt", 'r') as f:
        for line in f:
            if line.strip() and ':' in line:
                idx, label = line.strip().split(':', 1)
                des_labels[int(idx)] = label.strip()
    
    return tian_labels, des_labels

def analyze_overlaps():
    """Detailed analysis of atlas overlaps"""
    
    print("🔍 DETAILED OVERLAP ANALYSIS")
    print("=" * 35)
    
    # Load aligned atlases
    base_dir = Path("tiandes_atlas")
    aligned_dir = base_dir / "aligned_atlases"
    
    tian_img = nib.load(aligned_dir / "tian_aligned.nii.gz")
    des_img = nib.load(aligned_dir / "destrieux_aligned.nii.gz")
    
    tian_data = tian_img.get_fdata().astype(int)
    des_data = des_img.get_fdata().astype(int)
    
    # Load labels
    tian_labels, des_labels = load_label_files()
    
    print(f"📊 Atlas dimensions: {tian_data.shape}")
    print(f"   Tian regions: {len(np.unique(tian_data[tian_data > 0]))}")
    print(f"   Destrieux regions: {len(np.unique(des_data[des_data > 0]))}")
    
    # Find overlapping voxels
    overlap_mask = (tian_data > 0) & (des_data > 0)
    overlap_coords = np.where(overlap_mask)
    overlap_count = np.sum(overlap_mask)
    
    print(f"\n⚠️  OVERLAP SUMMARY:")
    print(f"   Total overlapping voxels: {overlap_count}")
    print(f"   Percentage of brain: {100 * overlap_count / np.sum((tian_data > 0) | (des_data > 0)):.2f}%")
    
    if overlap_count == 0:
        print("✅ No overlaps detected!")
        return
    
    # Analyze overlap patterns
    overlap_pairs = defaultdict(int)
    
    for i in range(len(overlap_coords[0])):
        x, y, z = overlap_coords[0][i], overlap_coords[1][i], overlap_coords[2][i]
        tian_label = tian_data[x, y, z]
        des_label = des_data[x, y, z]
        overlap_pairs[(tian_label, des_label)] += 1
    
    # Create detailed overlap report
    print(f"\n📋 OVERLAP DETAILS:")
    print(f"   Unique overlap pairs: {len(overlap_pairs)}")
    
    # Sort by overlap size
    sorted_overlaps = sorted(overlap_pairs.items(), key=lambda x: x[1], reverse=True)
    
    # Create reports directory
    reports_dir = base_dir / "validation" / "overlap_reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Detailed CSV report
    overlap_data = []
    for (tian_id, des_id), voxel_count in sorted_overlaps:
        tian_name = tian_labels.get(tian_id, f"Unknown_{tian_id}")
        des_name = des_labels.get(des_id, f"Unknown_{des_id}")
        
        overlap_data.append({
            'tian_id': tian_id,
            'tian_name': tian_name,
            'destrieux_id': des_id,
            'destrieux_name': des_name,
            'overlap_voxels': voxel_count,
            'percentage': 100 * voxel_count / overlap_count
        })
    
    df = pd.DataFrame(overlap_data)
    df.to_csv(reports_dir / "overlap_details.csv", index=False)
    
    # Summary report
    with open(reports_dir / "overlap_summary.txt", 'w') as f:
        f.write("TIANDES ATLAS OVERLAP ANALYSIS\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total overlapping voxels: {overlap_count}\n")
        f.write(f"Unique region pairs: {len(overlap_pairs)}\n\n")
        
        f.write("TOP 10 LARGEST OVERLAPS:\n")
        f.write("-" * 25 + "\n")
        
        for i, ((tian_id, des_id), voxels) in enumerate(sorted_overlaps[:10]):
            tian_name = tian_labels.get(tian_id, f"Unknown_{tian_id}")
            des_name = des_labels.get(des_id, f"Unknown_{des_id}")
            percentage = 100 * voxels / overlap_count
            
            f.write(f"{i+1:2d}. {voxels:3d} voxels ({percentage:4.1f}%)\n")
            f.write(f"    Tian: {tian_name}\n")
            f.write(f"    Destrieux: {des_name}\n\n")
        
        f.write("OVERLAP PATTERNS:\n")
        f.write("-" * 16 + "\n")
        
        # Analyze which Tian regions overlap most
        tian_overlap_counts = defaultdict(int)
        for (tian_id, des_id), count in overlap_pairs.items():
            tian_overlap_counts[tian_id] += count
        
        f.write("Most problematic Tian regions:\n")
        for tian_id, total_overlap in sorted(tian_overlap_counts.items(), 
                                           key=lambda x: x[1], reverse=True)[:5]:
            tian_name = tian_labels.get(tian_id, f"Unknown_{tian_id}")
            f.write(f"  {tian_name}: {total_overlap} overlapping voxels\n")
    
    print(f"📄 Detailed reports saved:")
    print(f"   {reports_dir}/overlap_details.csv")
    print(f"   {reports_dir}/overlap_summary.txt")
    
    # Show top overlaps
    print(f"\n🔥 TOP 5 LARGEST OVERLAPS:")
    for i, ((tian_id, des_id), voxels) in enumerate(sorted_overlaps[:5]):
        tian_name = tian_labels.get(tian_id, f"Unknown_{tian_id}")
        des_name = des_labels.get(des_id, f"Unknown_{des_id}")
        percentage = 100 * voxels / overlap_count
        print(f"   {i+1}. {voxels} voxels ({percentage:.1f}%)")
        print(f"      Tian: {tian_name}")
        print(f"      Destrieux: {des_name}")
    
    return overlap_pairs, overlap_count

def create_overlap_masks():
    """Create individual overlap masks for visualization"""
    
    print(f"\n🎯 CREATING OVERLAP MASKS")
    print("=" * 28)
    
    base_dir = Path("tiandes_atlas")
    aligned_dir = base_dir / "aligned_atlases"
    vis_dir = base_dir / "validation" / "boundary_visualizations"
    vis_dir.mkdir(exist_ok=True)
    
    # Load data
    tian_img = nib.load(aligned_dir / "tian_aligned.nii.gz")
    des_img = nib.load(aligned_dir / "destrieux_aligned.nii.gz")
    
    tian_data = tian_img.get_fdata().astype(int)
    des_data = des_img.get_fdata().astype(int)
    
    # Create overall overlap mask
    overlap_mask = ((tian_data > 0) & (des_data > 0)).astype(int)
    overlap_img = nib.Nifti1Image(overlap_mask, tian_img.affine, tian_img.header)
    nib.save(overlap_img, vis_dir / "all_overlaps_mask.nii.gz")
    
    # Create boundary zone masks
    tian_boundary = ((tian_data > 0).astype(int) * 100)  # Tian regions = 100
    des_boundary = ((des_data > 0).astype(int) * 200)    # Destrieux regions = 200
    overlap_boundary = (overlap_mask * 300)              # Overlaps = 300
    
    # Combined boundary visualization
    boundary_viz = tian_boundary + des_boundary + overlap_boundary
    boundary_img = nib.Nifti1Image(boundary_viz, tian_img.affine, tian_img.header)
    nib.save(boundary_img, vis_dir / "boundary_zones.nii.gz")
    
    print(f"📄 Overlap masks created:")
    print(f"   all_overlaps_mask.nii.gz - Binary overlap mask")
    print(f"   boundary_zones.nii.gz - Multi-level boundary visualization")
    print(f"   Use these with MRIcrogl for visual inspection!")

def suggest_resolution_strategy():
    """Suggest strategies for resolving overlaps"""
    
    print(f"\n💡 OVERLAP RESOLUTION STRATEGIES")
    print("=" * 38)
    print("Based on neuroanatomical principles:")
    print()
    print("1. 🧠 PRIORITY-BASED RESOLUTION:")
    print("   - Subcortical structures (Tian) take priority in deep regions")
    print("   - Cortical structures (Destrieux) take priority in superficial regions")
    print("   - Limbic boundaries require case-by-case evaluation")
    print()
    print("2. 🔄 EROSION-BASED RESOLUTION:")
    print("   - Erode overlapping boundaries by 1-2 voxels")
    print("   - Create transition zones marked as 'boundary'")
    print("   - Preserve core regions of each structure")
    print()
    print("3. 📊 ANATOMICAL VALIDATION:")
    print("   - Cross-reference with anatomical atlases")
    print("   - Use expert knowledge for limbic-cortical boundaries")
    print("   - Validate against histological references")
    print()
    print("🎯 RECOMMENDED APPROACH:")
    print("   Implement priority-based resolution with Tian precedence")
    print("   in subcortical regions and Destrieux precedence in cortical areas.")

if __name__ == "__main__":
    # Run overlap analysis
    overlap_pairs, overlap_count = analyze_overlaps()
    
    if overlap_count > 0:
        # Create visualization masks
        create_overlap_masks()
        
        # Suggest resolution strategies
        suggest_resolution_strategy()
    
    print(f"\n🎯 STATUS: Overlap analysis complete!")
    print(f"   Next step: Implement overlap resolution strategy")