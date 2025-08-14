#!/usr/bin/env python3
"""
MRIcrogl Visualization Script for TianDes Atlas
Auto-generates key visualizations for boundary inspection
"""

import gl

def visualize_tiandes_atlas():
    """Main visualization function for TianDes atlas"""
    
    # Set up MRIcrogl
    gl.resetdefaults()
    
    # Load background template (adjust path as needed)
    # gl.loadimage('path/to/MNI152_T1_2mm.nii.gz')
    
    print("🧠 TianDes Atlas Visualization")
    print("=" * 35)
    
    # 1. Full atlas overview
    print("1. Loading full TianDes atlas...")
    gl.overlayload('tiandes_atlas/final_atlas/tiandes_combined.nii.gz')
    gl.overlaycolorname(1, 'Custom')
    gl.overlaylut(1, 'tiandes_atlas/final_atlas/tiandes_lookup_table.txt')
    gl.opacity(1, 70)
    
    # Save overview
    gl.savebmp('tiandes_atlas/plots_4_mricrogl/tiandes_full_atlas.png')
    
    # 2. Subcortical regions only
    print("2. Visualizing subcortical regions...")
    gl.overlayclose(1)
    gl.overlayload('tiandes_atlas/plots_4_mricrogl/tiandes_subcortical_only.nii.gz')
    gl.overlaycolorname(1, 'Warm')
    gl.opacity(1, 80)
    gl.savebmp('tiandes_atlas/plots_4_mricrogl/tiandes_subcortical.png')
    
    # 3. Cortical regions only
    print("3. Visualizing cortical regions...")
    gl.overlayclose(1)
    gl.overlayload('tiandes_atlas/plots_4_mricrogl/tiandes_cortical_only.nii.gz')
    gl.overlaycolorname(1, 'Cool')
    gl.opacity(1, 60)
    gl.savebmp('tiandes_atlas/plots_4_mricrogl/tiandes_cortical.png')
    
    # 4. Boundary zones
    print("4. Visualizing limbic-cortical boundaries...")
    gl.overlayclose(1)
    gl.overlayload('tiandes_atlas/plots_4_mricrogl/boundary_checks/limbic_cortical_boundaries.nii.gz')
    gl.overlaycolorname(1, 'Custom')
    gl.opacity(1, 85)
    gl.savebmp('tiandes_atlas/plots_4_mricrogl/boundary_checks/boundaries.png')
    
    # 5. Hemisphere views
    print("5. Creating hemisphere visualizations...")
    
    # Left hemisphere
    gl.overlayclose(1)
    gl.overlayload('tiandes_atlas/plots_4_mricrogl/tiandes_left_hemisphere.nii.gz')
    gl.overlaycolorname(1, 'Spectrum')
    gl.opacity(1, 75)
    gl.savebmp('tiandes_atlas/plots_4_mricrogl/tiandes_left_hemi.png')
    
    # Right hemisphere
    gl.overlayclose(1)
    gl.overlayload('tiandes_atlas/plots_4_mricrogl/tiandes_right_hemisphere.nii.gz')
    gl.overlaycolorname(1, 'Spectrum')
    gl.opacity(1, 75)
    gl.savebmp('tiandes_atlas/plots_4_mricrogl/tiandes_right_hemi.png')
    
    print("✅ Visualization complete!")
    print("📁 Images saved in plots_4_mricrogl/")

if __name__ == "__main__":
    visualize_tiandes_atlas()
