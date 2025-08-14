#!/usr/bin/env python3
"""
MRIcrogl ROI Generator for TianDes Atlas
Creates individual ROI files for visualization and boundary inspection
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import pandas as pd

def load_tiandes_labels():
    """Load TianDes labels and create lookup dictionaries"""
    
    labels_file = Path("tiandes_atlas/final_atlas/tiandes_labels.txt")
    
    labels = {}
    with open(labels_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    try:
                        label_id = int(parts[0])
                        label_name = parts[1].strip()
                        labels[label_id] = label_name
                    except ValueError:
                        continue
    
    return labels

def generate_individual_rois():
    """Generate individual ROI files for each region"""
    
    print("🎨 GENERATING INDIVIDUAL ROI FILES")
    print("=" * 40)
    
    # Load atlas and labels
    atlas_path = Path("tiandes_atlas/final_atlas/tiandes_combined.nii.gz")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    
    labels = load_tiandes_labels()
    
    # Create output directories
    base_dir = Path("tiandes_atlas")
    limbic_dir = base_dir / "individual_rois" / "limbic"
    cortical_dir = base_dir / "individual_rois" / "cortical"
    
    limbic_dir.mkdir(exist_ok=True)
    cortical_dir.mkdir(exist_ok=True)
    
    # Get unique regions
    unique_regions = np.unique(atlas_data[atlas_data > 0])
    
    print(f"📊 Processing {len(unique_regions)} regions...")
    
    # Separate subcortical and cortical regions
    subcortical_count = 0
    cortical_count = 0
    
    for region_id in unique_regions:
        # Create binary mask for this region
        roi_mask = (atlas_data == region_id).astype(np.uint8)
        roi_img = nib.Nifti1Image(roi_mask, atlas_img.affine, atlas_img.header)
        
        # Get region info
        region_name = labels.get(region_id, f"Unknown_{region_id}")
        voxel_count = np.sum(roi_mask)
        
        # Determine if subcortical (Tian) or cortical (Destrieux)
        if 1 <= region_id <= 54:
            # Tian subcortical region
            clean_name = region_name.replace('[Tian_S4]', '').strip()
            safe_name = "".join(c for c in clean_name if c.isalnum() or c in '-_').replace(' ', '_')
            output_path = limbic_dir / f"Tian_{region_id:02d}_{safe_name}.nii.gz"
            subcortical_count += 1
            region_type = "Subcortical"
        else:
            # Destrieux cortical region
            clean_name = region_name.replace('[Destrieux]', '').strip()
            safe_name = "".join(c for c in clean_name if c.isalnum() or c in '-_').replace(' ', '_')
            output_path = cortical_dir / f"Des_{region_id:03d}_{safe_name}.nii.gz"
            cortical_count += 1
            region_type = "Cortical"
        
        # Save ROI file
        nib.save(roi_img, output_path)
        
        if len(unique_regions) <= 20 or region_id % 20 == 0:  # Show progress for large atlases
            print(f"   {region_type} ROI {region_id}: {voxel_count} voxels -> {output_path.name}")
    
    print(f"\n✅ ROI Generation Complete:")
    print(f"   Subcortical ROIs: {subcortical_count} files in {limbic_dir.name}/")
    print(f"   Cortical ROIs: {cortical_count} files in {cortical_dir.name}/")
    
    return subcortical_count, cortical_count

def create_mricrogl_overlays():
    """Create specialized overlays for MRIcrogl boundary visualization"""
    
    print(f"\n🔍 CREATING MRICROGL BOUNDARY OVERLAYS")
    print("=" * 42)
    
    base_dir = Path("tiandes_atlas")
    plots_dir = base_dir / "plots_4_mricrogl"
    
    # Load atlas
    atlas_path = base_dir / "final_atlas" / "tiandes_combined.nii.gz"
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)
    
    # 1. Create subcortical-only overlay
    subcortical_mask = ((atlas_data >= 1) & (atlas_data <= 54)).astype(np.uint8) * 100
    subcortical_img = nib.Nifti1Image(subcortical_mask, atlas_img.affine, atlas_img.header)
    nib.save(subcortical_img, plots_dir / "tiandes_subcortical_only.nii.gz")
    
    # 2. Create cortical-only overlay
    cortical_mask = (atlas_data > 100).astype(np.uint8) * 200
    cortical_img = nib.Nifti1Image(cortical_mask, atlas_img.affine, atlas_img.header)
    nib.save(cortical_img, plots_dir / "tiandes_cortical_only.nii.gz")
    
    # 3. Create boundary zone visualization
    # Dilate subcortical regions to find boundaries
    from scipy import ndimage
    
    subcortical_binary = (atlas_data >= 1) & (atlas_data <= 54)
    cortical_binary = atlas_data > 100
    
    # Create boundary zones
    subcortical_dilated = ndimage.binary_dilation(subcortical_binary, iterations=2)
    cortical_dilated = ndimage.binary_dilation(cortical_binary, iterations=2)
    
    # Boundary is where dilated regions meet
    boundary_zone = subcortical_dilated & cortical_dilated
    
    # Create multi-level visualization
    boundary_viz = np.zeros_like(atlas_data)
    boundary_viz[subcortical_binary] = 100  # Subcortical = 100
    boundary_viz[cortical_binary] = 200     # Cortical = 200
    boundary_viz[boundary_zone] = 300       # Boundary = 300
    
    boundary_img = nib.Nifti1Image(boundary_viz.astype(np.uint16), atlas_img.affine, atlas_img.header)
    nib.save(boundary_img, plots_dir / "boundary_checks" / "limbic_cortical_boundaries.nii.gz")
    
    # 4. Create hemisphere-separated overlays
    # Assume midline is at x = atlas_data.shape[0] // 2
    midline = atlas_data.shape[0] // 2
    
    # Left hemisphere (x < midline)
    left_mask = atlas_data.copy()
    left_mask[midline:, :, :] = 0
    left_img = nib.Nifti1Image(left_mask.astype(np.uint16), atlas_img.affine, atlas_img.header)
    nib.save(left_img, plots_dir / "tiandes_left_hemisphere.nii.gz")
    
    # Right hemisphere (x >= midline)  
    right_mask = atlas_data.copy()
    right_mask[:midline, :, :] = 0
    right_img = nib.Nifti1Image(right_mask.astype(np.uint16), atlas_img.affine, atlas_img.header)
    nib.save(right_img, plots_dir / "tiandes_right_hemisphere.nii.gz")
    
    print(f"📄 MRIcrogl overlays created:")
    print(f"   tiandes_subcortical_only.nii.gz - Tian regions only")
    print(f"   tiandes_cortical_only.nii.gz - Destrieux regions only")
    print(f"   limbic_cortical_boundaries.nii.gz - Boundary visualization")
    print(f"   tiandes_left_hemisphere.nii.gz - Left hemisphere regions")
    print(f"   tiandes_right_hemisphere.nii.gz - Right hemisphere regions")

def create_mricrogl_script():
    """Create MRIcrogl script for automated visualization"""
    
    print(f"\n📝 CREATING MRICROGL VISUALIZATION SCRIPT")
    print("=" * 44)
    
    script_path = Path("tiandes_atlas/mricrogl_tiandes_visualization.py")
    
    with open(script_path, 'w') as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
MRIcrogl Visualization Script for TianDes Atlas
Auto-generates key visualizations for boundary inspection
\"\"\"

import gl

def visualize_tiandes_atlas():
    \"\"\"Main visualization function for TianDes atlas\"\"\"
    
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
""")
    
    print(f"📄 MRIcrogl script created: {script_path.name}")
    print(f"💡 Usage: Run this script in MRIcrogl Python console")

def create_roi_inventory():
    """Create inventory of all generated ROI files"""
    
    print(f"\n📋 CREATING ROI INVENTORY")
    print("=" * 27)
    
    base_dir = Path("tiandes_atlas")
    
    # Collect all ROI files
    limbic_rois = list((base_dir / "individual_rois" / "limbic").glob("*.nii.gz"))
    cortical_rois = list((base_dir / "individual_rois" / "cortical").glob("*.nii.gz"))
    
    inventory_data = []
    
    # Process subcortical ROIs
    for roi_file in sorted(limbic_rois):
        roi_img = nib.load(roi_file)
        voxel_count = np.sum(roi_img.get_fdata() > 0)
        volume_mm3 = voxel_count * 8  # 2x2x2 mm voxels
        
        inventory_data.append({
            'roi_file': roi_file.name,
            'roi_type': 'Subcortical',
            'source_atlas': 'Tian_S4',
            'voxel_count': voxel_count,
            'volume_mm3': volume_mm3,
            'relative_path': f"individual_rois/limbic/{roi_file.name}"
        })
    
    # Process cortical ROIs
    for roi_file in sorted(cortical_rois):
        roi_img = nib.load(roi_file)
        voxel_count = np.sum(roi_img.get_fdata() > 0)
        volume_mm3 = voxel_count * 8
        
        inventory_data.append({
            'roi_file': roi_file.name,
            'roi_type': 'Cortical',
            'source_atlas': 'Destrieux',
            'voxel_count': voxel_count,
            'volume_mm3': volume_mm3,
            'relative_path': f"individual_rois/cortical/{roi_file.name}"
        })
    
    # Save inventory
    df = pd.DataFrame(inventory_data)
    df.to_csv(base_dir / "roi_inventory.csv", index=False)
    
    print(f"📄 ROI inventory saved: roi_inventory.csv")
    print(f"📊 Total ROI files: {len(inventory_data)}")
    print(f"   Subcortical: {len(limbic_rois)}")
    print(f"   Cortical: {len(cortical_rois)}")

if __name__ == "__main__":
    # Generate individual ROIs
    subcount, cortcount = generate_individual_rois()
    
    # Create MRIcrogl overlays
    create_mricrogl_overlays()
    
    # Create MRIcrogl script
    create_mricrogl_script()
    
    # Create ROI inventory
    create_roi_inventory()
    
    print(f"\n🎉 MRICROGL VISUALIZATION SETUP COMPLETE!")
    print("=" * 45)
    print(f"📁 Individual ROI files: {subcount + cortcount} regions")
    print(f"🎨 MRIcrogl overlays: Ready for visualization")
    print(f"📝 Visualization script: mricrogl_tiandes_visualization.py")
    print(f"📊 ROI inventory: roi_inventory.csv")