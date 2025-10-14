#!/usr/bin/env python3
"""
Step 1: Levtiades Atlas Setup Script #
====================================

Sets up the Levtiades Atlas project by:
1. Copying source atlases from downloaded_atlases folder
2. Downloading Destrieux cortical atlas via nilearn
3. Preparing Tian subcortical atlas data
4. Setting up directory structure for atlas creation
5. Verifying atlas properties and spatial compatibility

This copies the original atlases from downloaded_atlases/ so step 2 can work with them.
"""

import os
import shutil
import nibabel as nib
import numpy as np
from pathlib import Path

def setup_levtiades_project():
    """Setup Levtiades project by copying source atlases and preparing structure"""

    # Base directories
    base_dir = Path(".")  # Current directory (levtiades_atlas)
    raw_dir = base_dir / "raw_atlases"
    raw_dir.mkdir(exist_ok=True)

    print("🧠 Setting up Levtiades Atlas Project")
    print("=" * 60)

    # 1. Copy Levinson-Bari atlas from downloaded_atlases
    print("📋 Copying Levinson-Bari Limbic Brainstem Atlas...")
    levinson_source = Path("../downloaded_atlases/Levinson-Bari Limbic Brainstem Atlas (Levinson 2022)")

    if levinson_source.exists():
        # The Levinson atlas will be accessed directly by path, just verify it exists
        print(f"✅ Levinson atlas found: {levinson_source}")

        # Count the components
        components = [
            "mixed/01_LC_ATLAS_2022a.nii.gz",
            "midline/02_NTS_ATLAS_2022a.nii.gz",
            "midline/03_VTA_ATLAS_2022a.nii.gz",
            "midline/04_PAG_ATLAS_2022a.nii.gz",
            "midline/05_DRN_ATLAS_2022ai.nii.gz"
        ]

        found_components = []
        for comp in components:
            comp_path = levinson_source / comp
            if comp_path.exists():
                found_components.append(comp.split('/')[-1])

        print(f"   Components found: {len(found_components)}/5")
        for comp in found_components:
            print(f"   - {comp}")

    else:
        print(f"❌ Error: Levinson atlas not found at {levinson_source}")
        print("   Please ensure downloaded_atlases contains the Levinson atlas")
        return False

    # 2. Copy or download Tian atlas
    print("\n📋 Preparing Tian subcortical atlas...")
    tian_source = Path("../downloaded_atlases/Tian2020MSA_v1.4/3T/Subcortex-Only/Tian_Subcortex_S4_3T.nii.gz")
    tian_labels_source = Path("../downloaded_atlases/Tian2020MSA_v1.4/3T/Subcortex-Only/Tian_Subcortex_S4_3T_label.txt")

    if tian_source.exists() and tian_labels_source.exists():
        shutil.copy(tian_source, raw_dir / "tian_subcortical.nii.gz")
        shutil.copy(tian_labels_source, raw_dir / "tian_labels.txt")

        # Load and check Tian atlas
        tian_img = nib.load(tian_source)
        print(f"✅ Tian S4 atlas copied: {tian_img.shape} voxels")
        print(f"   Scale IV: 54 subcortical regions (most detailed)")

    else:
        print(f"❌ Error: Tian atlas files not found at {tian_source}")
        print("   Please ensure downloaded_atlases contains the Tian atlas")
        return False

    # 3. Copy or download Destrieux atlas
    print("\n📋 Preparing Destrieux cortical atlas...")
    destrieux_source = Path("../downloaded_atlases/destrieux_atlas/destrieux_cortical.nii.gz")
    destrieux_labels_source = Path("../downloaded_atlases/destrieux_atlas/destrieux_labels.txt")

    if destrieux_source.exists() and destrieux_labels_source.exists():
        # Copy from downloaded_atlases
        shutil.copy(destrieux_source, raw_dir / "destrieux_cortical.nii.gz")
        shutil.copy(destrieux_labels_source, raw_dir / "destrieux_labels.txt")

        # Load and check atlas
        des_img = nib.load(destrieux_source)
        print(f"✅ Destrieux atlas copied from downloaded_atlases: {des_img.shape} voxels")

        # Count regions from labels file
        with open(destrieux_labels_source, 'r') as f:
            lines = f.readlines()
        print(f"   Regions: {len(lines)} cortical areas")

    else:
        # Fallback: download via nilearn
        print("📥 Destrieux not found in downloaded_atlases, downloading via nilearn...")
        try:
            from nilearn.datasets import fetch_atlas_destrieux_2009
            destrieux = fetch_atlas_destrieux_2009()

            # Load and save atlas
            des_img = nib.load(destrieux.maps)
            nib.save(des_img, raw_dir / "destrieux_cortical.nii.gz")

            # Save labels with proper formatting
            with open(raw_dir / "destrieux_labels.txt", 'w') as f:
                for i, label in enumerate(destrieux.labels):
                    if i > 0:  # Skip background (0)
                        f.write(f"{i}: {label}\n")

            print(f"✅ Destrieux atlas downloaded: {des_img.shape} voxels")
            print(f"   Regions: {len(destrieux.labels)-1} cortical areas (excluding background)")

        except ImportError:
            print("❌ Error: nilearn not installed. Please install with: pip install nilearn")
            print("   Alternative: Run Step 0 to download Destrieux atlas first")
            return False
        except Exception as e:
            print(f"❌ Error downloading Destrieux: {e}")
            return False

    # 4. Create project structure
    print("\n📁 Creating project directory structure...")
    dirs_to_create = [
        "work",
        "final_atlas/with_overlaps",
        "final_atlas/no_overlaps",
        "reports",
        "qc_validation",
        "individual_rois"
    ]

    for dir_path in dirs_to_create:
        (base_dir / dir_path).mkdir(parents=True, exist_ok=True)

    print("✅ Directory structure created")

    # 5. Create atlas info summary
    info_file = base_dir / "atlas_info.txt"
    with open(info_file, 'w') as f:
        f.write("Levtiades Atlas Project Information\n")
        f.write("=" * 40 + "\n\n")
        f.write("COMPONENT ATLASES:\n\n")

        f.write("1. Levinson-Bari Limbic Brainstem Atlas (2022)\n")
        f.write("   - Source: Levinson et al. 2022\n")
        f.write("   - Regions: 5 critical brainstem nuclei for psychiatric disorders\n")
        f.write("   - Components: LC, NTS, VTA, PAG, DRN\n")
        f.write("   - Native space: MNI152NLin2009bAsym (0.5mm)\n")
        f.write("   - Label range: 1-5\n\n")

        f.write("2. Tian Subcortical Atlas (Scale IV - S4)\n")
        f.write("   - Source: Melbourne Subcortex Atlas v1.4\n")
        f.write("   - Regions: 54 fine-grained subcortical areas\n")
        f.write("   - Structures: Striatum, Thalamus, Hippocampus, Amygdala, Globus Pallidus\n")
        f.write("   - Native space: MNI152NLin6Asym (2mm)\n")
        f.write("   - Label range: 101-154 (offset by +100)\n\n")

        f.write("3. Destrieux Cortical Atlas (2009)\n")
        f.write("   - Source: Destrieux et al. 2010, via Nilearn\n")
        f.write("   - Regions: 148 sulco-gyral cortical areas (74 per hemisphere)\n")
        f.write("   - Native space: MNI152NLin2009aAsym (2mm)\n")
        f.write("   - Label range: 201-348 (offset by +200)\n\n")

        f.write("COMBINATION STRATEGY:\n")
        f.write("- Hierarchical priority: Levinson > Tian > Destrieux\n")
        f.write("- Template-to-template registration using ANTs\n")
        f.write("- Target space: MNI152NLin2009cAsym at 2mm resolution\n")
        f.write("- Total regions: 207 (5 + 54 + 148)\n\n")

        f.write("PSYCHIATRIC CIRCUIT FOCUS:\n")
        f.write("- Depression: LC-DRN-VTA connectivity\n")
        f.write("- Anxiety: PAG-amygdala-prefrontal circuits\n")
        f.write("- PTSD: Brainstem arousal system analysis\n")
        f.write("- Addiction: VTA-striatal reward pathways\n")

    print(f"📄 Project info saved to: {info_file}")

    print("\n🎯 Next steps:")
    print("   1. Verify atlas properties and spatial compatibility")
    print("   2. Run Step 2: 2_levtiades_to_mni2009c.py")
    print("   3. Generate validation and QC reports")
    print("   4. Create visualization files")

    return True

def verify_atlas_properties():
    """Check basic properties of all three atlases"""

    print("\n🔍 ATLAS VERIFICATION")
    print("=" * 30)

    raw_dir = Path("raw_atlases")

    try:
        # Load atlases
        tian_img = nib.load(raw_dir / "tian_subcortical.nii.gz")
        des_img = nib.load(raw_dir / "destrieux_cortical.nii.gz")

        print("TIAN SUBCORTICAL (S4):")
        print(f"  Shape: {tian_img.shape}")
        print(f"  Voxel size: {tian_img.header.get_zooms()[:3]} mm")
        tian_data = tian_img.get_fdata()
        print(f"  Data range: {tian_data.min():.0f} - {tian_data.max():.0f}")
        print(f"  Unique regions: {len(np.unique(tian_data[tian_data > 0]))}")

        print("\nDESTRIEUX CORTICAL:")
        print(f"  Shape: {des_img.shape}")
        print(f"  Voxel size: {des_img.header.get_zooms()[:3]} mm")
        des_data = des_img.get_fdata()
        print(f"  Data range: {des_data.min():.0f} - {des_data.max():.0f}")
        print(f"  Unique regions: {len(np.unique(des_data[des_data > 0]))}")

        # Check Levinson components
        print("\nLEVINSON COMPONENTS:")
        levinson_dir = Path("../downloaded_atlases/Levinson-Bari Limbic Brainstem Atlas (Levinson 2022)")
        components = {
            "LC": "mixed/01_LC_ATLAS_2022a.nii.gz",
            "NTS": "midline/02_NTS_ATLAS_2022a.nii.gz",
            "VTA": "midline/03_VTA_ATLAS_2022a.nii.gz",
            "PAG": "midline/04_PAG_ATLAS_2022a.nii.gz",
            "DRN": "midline/05_DRN_ATLAS_2022ai.nii.gz"
        }

        for name, path in components.items():
            comp_path = levinson_dir / path
            if comp_path.exists():
                comp_img = nib.load(comp_path)
                comp_data = comp_img.get_fdata()
                voxels = int((comp_data > 0).sum())
                print(f"  {name}: {comp_img.shape}, {voxels} voxels")
            else:
                print(f"  {name}: NOT FOUND")

        # Check spatial compatibility
        print("\nSPATIAL COMPATIBILITY:")
        shape_match = tian_img.shape == des_img.shape
        affine_close = np.allclose(tian_img.affine, des_img.affine, atol=1e-2)

        print(f"  Tian-Destrieux shape match: {shape_match}")
        print(f"  Tian-Destrieux affine close: {affine_close}")

        if not shape_match or not affine_close:
            print("  ⚠️  Template-to-template registration will handle differences")
        else:
            print("  ✅ Tian and Destrieux appear spatially compatible")

        print("\n✅ Verification complete. Ready for Step 2: atlas creation")
        return True

    except Exception as e:
        print(f"❌ Error verifying atlases: {e}")
        return False

if __name__ == "__main__":
    print("🚀 LEVTIADES ATLAS PROJECT SETUP")
    print("=" * 50)

    success = setup_levtiades_project()
    if success:
        verify_atlas_properties()
        print("\n🎉 Setup complete! Ready to run Step 2.")
    else:
        print("❌ Setup failed. Please check error messages above.")