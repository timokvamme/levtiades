#!/usr/bin/env python3
"""
Step 0: Download Destrieux Atlas

This script downloads the Destrieux cortical atlas to the downloaded_atlases folder.
The Destrieux atlas provides 148 cortical parcellation regions.

Reference: Destrieux, C., et al. (2010). NeuroImage, 53(1), 1-15.
"""

import os
import urllib.request
import zipfile
from pathlib import Path

def download_destrieux_atlas():
    """Download the Destrieux cortical atlas using nilearn."""

    # Create download directory if it doesn't exist
    download_dir = Path(__file__).parent
    destrieux_dir = download_dir / "destrieux_atlas"
    destrieux_dir.mkdir(exist_ok=True)

    print("🧠 Downloading Destrieux Cortical Atlas...")
    print(f"📁 Download directory: {destrieux_dir}")

    # Check if already downloaded
    atlas_file = destrieux_dir / "destrieux_cortical.nii.gz"
    labels_file = destrieux_dir / "destrieux_labels.txt"

    if atlas_file.exists() and labels_file.exists():
        print("✅ Destrieux atlas already exists - skipping download")
        return destrieux_dir

    try:
        # Download Destrieux atlas via nilearn
        print("📥 Downloading via nilearn...")
        from nilearn.datasets import fetch_atlas_destrieux_2009
        import nibabel as nib

        destrieux = fetch_atlas_destrieux_2009()

        # Load and save atlas
        des_img = nib.load(destrieux.maps)
        nib.save(des_img, atlas_file)

        # Save labels with proper formatting
        with open(labels_file, 'w') as f:
            for i, label in enumerate(destrieux.labels):
                if i > 0:  # Skip background (0)
                    f.write(f"{i}: {label}\n")

        print(f"✅ Destrieux atlas downloaded: {des_img.shape} voxels")
        print(f"   Regions: {len(destrieux.labels)-1} cortical areas")
        print(f"   Atlas saved: {atlas_file}")
        print(f"   Labels saved: {labels_file}")

    except ImportError:
        print("❌ Error: nilearn not installed. Please install with: pip install nilearn")
        print("📝 Creating manual download instructions instead...")

        # Create fallback instructions
        instructions_file = destrieux_dir / "download_instructions.txt"
        with open(instructions_file, 'w') as f:
            f.write("""Destrieux Atlas Download Instructions
=====================================

The Destrieux cortical atlas can be obtained from:

1. Python (recommended):
   pip install nilearn
   python -c "from nilearn.datasets import fetch_atlas_destrieux_2009; fetch_atlas_destrieux_2009()"

2. FreeSurfer:
   - If FreeSurfer is installed: $FREESURFER_HOME/subjects/fsaverage/label/

3. FSL:
   - Part of FSL atlas collection at $FSLDIR/data/atlases/

Required files:
- destrieux_cortical.nii.gz (atlas volume)
- destrieux_labels.txt (region names and indices)
""")
        print(f"✅ Instructions created at: {instructions_file}")

    except Exception as e:
        print(f"❌ Error downloading Destrieux: {e}")
        return None

    return destrieux_dir

if __name__ == "__main__":
    download_dir = download_destrieux_atlas()
    print(f"\n🎯 Next steps:")
    print(f"   1. Obtain Destrieux atlas files (see instructions)")
    print(f"   2. Place them in: {download_dir}")
    print(f"   3. Run the next processing script")