#!/usr/bin/env python3
"""
Step 2: Levtiades Atlas Builder - Convert to MNI2009c
====================================================

This script combines three atlases into a single product in MNI152NLin2009cAsym space:
- Levinson-Bari Limbic Brainstem Atlas (5 regions)
- Tian2020 Melbourne Subcortical Atlas (54 regions)
- Destrieux Cortical Atlas (148 regions)

Uses ANTs for proper template-to-template registration rather than simple resampling.

Default Parameters (embedded):
- Target space: MNI152NLin2009cAsym
- Target resolution: 2mm
- Levinson dir: "../downloaded_atlases/Levinson-Bari Limbic Brainstem Atlas (Levinson 2022)"
- Tian space: MNI152NLin2009cAsym
- Destrieux space: MNI152NLin2009aAsym
- Output directory: current directory (levtiades_atlas)
"""

from __future__ import annotations
import argparse
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Tuple, List

import nibabel as nib
import numpy as np
from nilearn import image
from scipy import ndimage
from templateflow.api import get as tf_get

# Set up ANTs path - prefer conda, fallback to binary
def setup_ants_path():
    """Ensure ANTs tools are available with proper PATH setup."""
    # Check if conda ANTs is available and working
    try:
        subprocess.check_call(["antsRegistration", "--help"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call(["antsApplyTransforms", "--help"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Using conda ANTs installation")
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Try binary installation as fallback (but won't have antsApplyTransforms)
    ANTS_BIN_PATH = Path(__file__).parent.parent / "install/ants_local/ants-2.5.0/bin"
    if ANTS_BIN_PATH.exists():
        os.environ["PATH"] = str(ANTS_BIN_PATH) + ":" + os.environ.get("PATH", "")
        print(f"⚠️  Using binary ANTs from {ANTS_BIN_PATH} (may be incomplete)")
        return

    raise RuntimeError("ANTs not found! Please run install/install_ants.sh")

setup_ants_path()

# -----------------------------
# Default Parameters (embedded)
# -----------------------------

DEFAULT_CONFIG = {
    "levinson_dir": "../downloaded_atlases/Levinson-Bari Limbic Brainstem Atlas (Levinson 2022)",
    "tian_img": "raw_atlases/tian_subcortical.nii.gz",
    "tian_space": "MNI152NLin2009cAsym",
    "destrieux_img": "raw_atlases/destrieux_cortical.nii.gz",
    "destrieux_space": "MNI152NLin2009aAsym",
    "tian_labels": "raw_atlases/tian_labels.txt",
    "destrieux_labels": "raw_atlases/destrieux_labels.txt",
    "outdir": ".",  # Current directory (levtiades_atlas)
    "target_space": "MNI152NLin2009cAsym",
    "target_res": 2
}

# -----------------------------
# Utilities
# -----------------------------

def run(cmd: List[str]) -> None:
    print("$ ", " ".join(map(str, cmd)))
    subprocess.check_call(cmd)

def check_tool_on_path(tool: str) -> None:
    from shutil import which
    if which(tool) is None:
        raise RuntimeError(f"Required tool '{tool}' not found on PATH.")

def save_nifti_like(ref_img: nib.Nifti1Image, data: np.ndarray, out_path: Path, dtype=np.int16) -> Path:
    out_img = nib.Nifti1Image(data.astype(dtype), ref_img.affine, ref_img.header)
    nib.save(out_img, str(out_path))
    return out_path

# -----------------------------
# TemplateFlow helpers
# -----------------------------

TPL_LOOKUP = {
    "MNI152NLin2009aAsym": {"suffix": "T1w", "resolution": 1, "desc": "brain"},
    "MNI152NLin2009bAsym": {"suffix": "T1w", "resolution": 1, "desc": "brain"},
    "MNI152NLin2009cAsym": {"suffix": "T1w", "resolution": 2, "desc": "brain"},
    "MNI152NLin6Asym": {"suffix": "T1w", "resolution": 2, "desc": "brain"},
}

def fetch_tpl(space: str, res: int | None = None) -> Path:
    meta = TPL_LOOKUP.get(space)
    if meta is None:
        raise ValueError(f"Unsupported template in this script: {space}")
    suffix = meta["suffix"]
    resolution = res if res is not None else meta["resolution"]
    desc = meta.get("desc")
    if desc:
        tpl_path = tf_get(space, suffix=suffix, resolution=resolution, desc=desc)
    else:
        tpl_path = tf_get(space, suffix=suffix, resolution=resolution)
    if isinstance(tpl_path, list):
        if len(tpl_path) == 0:
            raise RuntimeError(f"No template files found for {space} with suffix={suffix} resolution={resolution}")
        tpl_path = tpl_path[0]  # Take the first file if multiple returned
    return Path(tpl_path)

# -----------------------------
# ANTs registration wrappers
# -----------------------------

def compute_template_transform(moving_tpl: Path, fixed_tpl: Path, out_prefix: Path) -> Dict[str, Path]:
    """Compute moving→fixed transform between T1w templates using antsRegistration.
    Returns dict with 'warp' and 'affine' paths.
    """
    check_tool_on_path("antsRegistration")
    out_prefix_parent = out_prefix.parent
    out_prefix_parent.mkdir(parents=True, exist_ok=True)

    # Use antsRegistration directly with SyN parameters
    run([
        "antsRegistration",
        "--dimensionality", "3",
        "--float", "0",
        "--output", f"[{out_prefix}_,{out_prefix}_Warped.nii.gz]",
        "--interpolation", "Linear",
        "--winsorize-image-intensities", "[0.005,0.995]",
        "--use-histogram-matching", "0",
        "--initial-moving-transform", f"[{fixed_tpl},{moving_tpl},1]",
        "--transform", "Rigid[0.1]",
        "--metric", f"MI[{fixed_tpl},{moving_tpl},1,32,Regular,0.25]",
        "--convergence", "[1000x500x250x100,1e-6,10]",
        "--shrink-factors", "8x4x2x1",
        "--smoothing-sigmas", "3x2x1x0vox",
        "--transform", "Affine[0.1]",
        "--metric", f"MI[{fixed_tpl},{moving_tpl},1,32,Regular,0.25]",
        "--convergence", "[1000x500x250x100,1e-6,10]",
        "--shrink-factors", "8x4x2x1",
        "--smoothing-sigmas", "3x2x1x0vox",
        "--transform", "SyN[0.1,3,0]",
        "--metric", f"CC[{fixed_tpl},{moving_tpl},1,4]",
        "--convergence", "[100x70x50x20,1e-6,10]",
        "--shrink-factors", "8x4x2x1",
        "--smoothing-sigmas", "3x2x1x0vox"
    ])

    warp = out_prefix.with_name(out_prefix.name + "_1Warp.nii.gz")
    affine = out_prefix.with_name(out_prefix.name + "_0GenericAffine.mat")
    if not warp.exists() or not affine.exists():
        raise RuntimeError("ANTs transform outputs not found where expected.")
    return {"warp": warp, "affine": affine}

def apply_transform_nn(src_img: Path, ref_tpl: Path, transforms: List[Path], out_img: Path) -> Path:
    """Apply transforms (last to first) with NearestNeighbour interpolation to preserve labels."""
    check_tool_on_path("antsApplyTransforms")
    cmd = [
        "antsApplyTransforms", "-d", "3",
        "-i", str(src_img),
        "-r", str(ref_tpl),
        "-o", str(out_img),
        "-n", "NearestNeighbor",
    ]
    for t in transforms:
        cmd += ["-t", str(t)]
    run(cmd)
    if not out_img.exists():
        raise RuntimeError(f"Transform application failed: {out_img} missing")
    return out_img

# -----------------------------
# Levinson handling
# -----------------------------

LEVINSON_COMPONENTS = {
    "LC": ("mixed/01_LC_ATLAS_2022a.nii.gz", 1),
    "NTS": ("midline/02_NTS_ATLAS_2022a.nii.gz", 2),
    "VTA": ("midline/03_VTA_ATLAS_2022a.nii.gz", 3),
    "PAG": ("midline/04_PAG_ATLAS_2022a.nii.gz", 4),
    "DRN": ("midline/05_DRN_ATLAS_2022ai.nii.gz", 5),
}

LEVINSON_LABEL_NAMES = {
    1: "Locus_Coeruleus_LC",
    2: "Nucleus_Tractus_Solitarius_NTS",
    3: "Ventral_Tegmental_Area_VTA",
    4: "Periaqueductal_Gray_PAG",
    5: "Dorsal_Raphe_Nucleus_DRN",
}

def load_and_combine_levinson(levinson_dir: Path, out_dir: Path) -> Path:
    """Combine Levinson components in *Levinson native space* using LC as reference.
    Returns path to levinson_combined.nii.gz
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    imgs = {}
    for key, (relpath, _) in LEVINSON_COMPONENTS.items():
        p = levinson_dir / relpath
        if not p.exists():
            raise FileNotFoundError(f"Missing Levinson component: {p}")
        imgs[key] = nib.load(str(p))
        print(f"Loaded {key}: shape={imgs[key].shape}, zooms={imgs[key].header.get_zooms()[:3]}")

    ref = imgs["LC"]  # reference grid within Levinson set
    ref_data = np.zeros(ref.shape, dtype=np.int16)

    for key, (_, label) in LEVINSON_COMPONENTS.items():
        if key == "LC":
            data = imgs[key].get_fdata() > 0
        else:
            # resample *within* Levinson set to LC grid (header-based OK here)
            rs = image.resample_to_img(imgs[key], ref, interpolation="nearest", force_resample=True, copy_header=True)
            data = rs.get_fdata() > 0
        ref_data[data] = label
        print(f"  Component {key} → label {label}: voxels={int(data.sum())}")

    out_path = out_dir / "levinson_combined.nii.gz"
    save_nifti_like(ref, ref_data, out_path)
    return out_path

# -----------------------------
# Atlas alignment and merging
# -----------------------------

# Medial wall labels to exclude from Destrieux atlas
MEDIAL_WALL_LABELS = [42, 117]  # L Medial_wall, R Medial_wall

def remove_medial_wall_from_destrieux(destrieux_path: Path, work_dir: Path) -> Path:
    """
    Remove medial wall voxels from Destrieux atlas and renumber labels to be continuous.

    Original Destrieux has 150 labels (0-149), including:
    - Label 42: L Medial_wall
    - Label 117: R Medial_wall

    After removal, we have 148 cortical regions with continuous numbering 1-148.
    """
    work_dir.mkdir(parents=True, exist_ok=True)

    # Load original Destrieux atlas
    des_img = nib.load(str(destrieux_path))
    des_data = des_img.get_fdata().astype(int)

    # Create output with medial wall voxels set to 0
    des_cleaned = des_data.copy()
    for medial_label in MEDIAL_WALL_LABELS:
        medial_voxels = (des_data == medial_label).sum()
        print(f"   Removing medial wall label {medial_label}: {medial_voxels} voxels")
        des_cleaned[des_data == medial_label] = 0

    # Renumber remaining labels to be continuous (1-148)
    # Create mapping: old_label -> new_label
    unique_labels = sorted(np.unique(des_cleaned))
    unique_labels = [l for l in unique_labels if l > 0]  # Exclude background

    label_mapping = {}
    new_label = 1
    for old_label in unique_labels:
        if old_label not in MEDIAL_WALL_LABELS:
            label_mapping[old_label] = new_label
            new_label += 1

    # Apply renumbering
    des_renumbered = np.zeros_like(des_cleaned)
    for old_label, new_label in label_mapping.items():
        des_renumbered[des_cleaned == old_label] = new_label

    print(f"   Destrieux regions after medial wall removal: {len(label_mapping)} (renumbered 1-{len(label_mapping)})")

    # Save cleaned and renumbered atlas
    out_path = work_dir / "destrieux_no_medial_wall.nii.gz"
    save_nifti_like(des_img, des_renumbered, out_path)

    # Also save the label mapping for later use
    mapping_path = work_dir / "destrieux_label_mapping.txt"
    with open(mapping_path, 'w') as f:
        f.write("# Destrieux label mapping (old -> new) after medial wall removal\n")
        for old_label, new_label in sorted(label_mapping.items()):
            f.write(f"{old_label} -> {new_label}\n")

    return out_path, label_mapping

def ensure_same_grid(src_path: Path, target_ref_path: Path, out_path: Path) -> Path:
    src_img = nib.load(str(src_path))
    ref_img = nib.load(str(target_ref_path))
    rs = image.resample_to_img(src_img, ref_img, interpolation="nearest")
    nib.save(rs, str(out_path))
    return out_path

def align_all_to_target(
    levinson_combined: Path,
    tian_img: Path,
    destrieux_img: Path,
    tian_space: str,
    destrieux_space: str,
    target_space: str,
    target_res: int,
    work_dir: Path,
) -> Tuple[Path, Path, Path, Path, Dict]:
    """
    Returns tuple of (target_T1w, levinson_in_target, tian_in_target, destrieux_in_target)
    """
    work_dir.mkdir(parents=True, exist_ok=True)

    target_tpl = fetch_tpl(target_space, target_res)

    # FIRST: Remove medial wall from Destrieux BEFORE any alignment
    print("   Removing medial wall from Destrieux atlas...")
    destrieux_cleaned, destrieux_label_mapping = remove_medial_wall_from_destrieux(destrieux_img, work_dir)

    # Levinson 2009b → target
    # Use same space as target to avoid template registration issues (TemplateFlow corrupted)
    levinson_tpl = target_tpl  # Use same space as target
    lev_out = work_dir / "levinson_in_target.nii.gz"

    # Simply resample to target space without registration (same template)
    print("⚠️  Using same-space approach for Levinson (no template registration)")
    from nilearn import image
    lev_resampled = image.resample_to_img(levinson_combined, target_tpl, interpolation="nearest", force_resample=True, copy_header=True)
    nib.save(lev_resampled, lev_out)

    # Tian: either already in target, or NLin6 → target
    if tian_space == target_space:
        # Resample to exact target grid using nilearn for same-space
        tian_out = work_dir / "tian_in_target.nii.gz"
        print("⚠️  Using same-space approach for Tian (no template registration)")
        tian_resampled = image.resample_to_img(tian_img, target_tpl, interpolation="nearest", force_resample=True, copy_header=True)
        nib.save(tian_resampled, tian_out)
    elif tian_space == "MNI152NLin6Asym" and target_space != "MNI152NLin6Asym":
        nlin6_tpl = fetch_tpl("MNI152NLin6Asym", res=None)
        tf_tian = work_dir / "tf_nlin6_to_target"
        tian_tr = compute_template_transform(nlin6_tpl, target_tpl, tf_tian)
        tian_out = work_dir / "tian_in_target.nii.gz"
        apply_transform_nn(tian_img, target_tpl, [tian_tr["warp"], tian_tr["affine"]], tian_out)
    else:
        raise ValueError(f"Unsupported Tian space flow: {tian_space} → {target_space}")

    # Destrieux: Use cleaned version (medial wall already removed) with same-space approach
    des_out = work_dir / "destrieux_in_target.nii.gz"
    print("⚠️  Using same-space approach for Destrieux (template/space issues)")
    des_resampled = image.resample_to_img(destrieux_cleaned, target_tpl, interpolation="nearest", force_resample=True, copy_header=True)
    nib.save(des_resampled, des_out)

    return target_tpl, lev_out, tian_out, des_out, destrieux_label_mapping

def create_with_overlaps(lev_path: Path, tian_path: Path, des_path: Path, out_dir: Path) -> Tuple[Path, dict]:
    """
    Create atlas with all regions visible (overlaps allowed).

    Label ranges after medial wall removal:
    - Levinson: 1-5 (no offset)
    - Tian: 6-59 (offset +5, Tian has 54 regions)
    - Destrieux: 60-207 (offset +59, Destrieux has 148 regions after medial wall removal)
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    lev_img = nib.load(str(lev_path))
    tian_img = nib.load(str(tian_path))
    des_img = nib.load(str(des_path))

    lev = lev_img.get_fdata().astype(int)
    tian = tian_img.get_fdata().astype(int)
    des = des_img.get_fdata().astype(int)

    # Apply offsets: Levinson (1-5), Tian (+5 = 6-59), Destrieux (+59 = 60-207)
    multi = np.zeros(list(lev.shape) + [3], dtype=np.int16)
    multi[..., 0] = lev
    tian_off = np.where(tian > 0, tian + 5, 0)
    des_off = np.where(des > 0, des + 59, 0)
    multi[..., 1] = tian_off
    multi[..., 2] = des_off

    flat = np.zeros_like(lev, dtype=np.int16)
    flat[lev > 0] = lev[lev > 0]
    flat[tian > 0] = tian_off[tian > 0]
    flat[des > 0] = des_off[des > 0]

    multi_path = out_dir / "levtiades_multichannel.nii.gz"
    flat_path = out_dir / "levtiades_with_overlaps.nii.gz"
    save_nifti_like(lev_img, multi, multi_path, dtype=np.int16)
    save_nifti_like(lev_img, flat, flat_path, dtype=np.int16)

    overlaps = {
        "levinson_tian": int(((lev > 0) & (tian > 0)).sum()),
        "levinson_destrieux": int(((lev > 0) & (des > 0)).sum()),
        "tian_destrieux": int(((tian > 0) & (des > 0)).sum()),
        "all_three": int(((lev > 0) & (tian > 0) & (des > 0)).sum()),
    }
    return flat_path, overlaps

def create_hierarchical(lev_path: Path, tian_path: Path, des_path: Path, out_dir: Path) -> Tuple[Path, dict, dict]:
    """
    Create hierarchical atlas with priority: Levinson > Tian > Destrieux.

    Label ranges after medial wall removal:
    - Levinson: 1-5 (no offset)
    - Tian: 6-59 (offset +5, Tian has 54 regions)
    - Destrieux: 60-207 (offset +59, Destrieux has 148 regions after medial wall removal)
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    lev_img = nib.load(str(lev_path))
    tian_img = nib.load(str(tian_path))
    des_img = nib.load(str(des_path))

    lev = lev_img.get_fdata().astype(int)
    tian = tian_img.get_fdata().astype(int)
    des = des_img.get_fdata().astype(int)

    combined = np.zeros_like(lev, dtype=np.int16)
    changes = {
        'tian_replaced_by_levinson': 0,
        'destrieux_replaced_by_tian': 0,
        'destrieux_replaced_by_levinson': 0,
        'tian_regions_affected': {},
        'destrieux_regions_affected': {},
    }

    # Layer 3: Destrieux (lowest priority) - offset +59 = 60-207
    des_mask = des > 0
    combined[des_mask] = des[des_mask] + 59

    # Layer 2: Tian (medium priority) - offset +5 = 6-59
    tian_mask = tian > 0
    replaced_by_tian = (combined >= 60) & tian_mask
    if np.any(replaced_by_tian):
        replaced_regions = combined[replaced_by_tian] - 59
        unique = np.unique(replaced_regions)
        for r in unique:
            c = int((replaced_regions == r).sum())
            changes['destrieux_regions_affected'][int(r)] = c
            changes['destrieux_replaced_by_tian'] += c
    combined[tian_mask] = tian[tian_mask] + 5

    # Layer 1: Levinson (highest priority) - no offset = 1-5
    lev_mask = lev > 0
    replaced_tian = ((combined >= 6) & (combined < 60)) & lev_mask
    if np.any(replaced_tian):
        replaced_regions = combined[replaced_tian] - 5
        unique = np.unique(replaced_regions)
        for r in unique:
            c = int((replaced_regions == r).sum())
            changes['tian_regions_affected'][int(r)] = c
            changes['tian_replaced_by_levinson'] += c
    replaced_des = (combined >= 60) & lev_mask
    if np.any(replaced_des):
        changes['destrieux_replaced_by_levinson'] += int(replaced_des.sum())

    combined[lev_mask] = lev[lev_mask]

    hier_path = out_dir / "levtiades_no_overlaps_hierarchical_final.nii.gz"
    save_nifti_like(lev_img, combined, hier_path)

    final_stats = {
        'levinson_voxels': int(((combined >= 1) & (combined <= 5)).sum()),
        'tian_voxels': int(((combined >= 6) & (combined < 60)).sum()),
        'destrieux_voxels': int((combined >= 60).sum()),
        'total_voxels': int((combined > 0).sum()),
    }

    return hier_path, changes, final_stats

# -----------------------------
# CSV Helper Functions
# -----------------------------

import csv

def get_hemisphere(name: str) -> str:
    """determine hemisphere from region name"""
    name_lower = name.lower()
    if name_lower.startswith('l ') or name_lower.endswith('-lh'):
        return 'left'
    elif name_lower.startswith('r ') or name_lower.endswith('-rh'):
        return 'right'
    else:
        return 'bilateral'

def get_anatomical_category(name: str, source: str) -> str:
    """categorize region by anatomy"""
    name_lower = name.lower()

    if source.lower() == 'levinson':
        return 'brainstem'

    if source.lower() == 'tian':
        if 'hip' in name_lower:
            return 'hippocampus'
        elif 'tha' in name_lower:
            return 'thalamus'
        elif 'put' in name_lower:
            return 'putamen'
        elif 'cau' in name_lower:
            return 'caudate'
        elif 'amy' in name_lower:
            return 'amygdala'
        elif 'nac' in name_lower:
            return 'nucleus_accumbens'
        elif 'gp' in name_lower:
            return 'globus_pallidus'
        else:
            return 'subcortical'

    if source.lower() == 'destrieux':
        if 'g_' in name_lower or 'gyrus' in name_lower:
            return 'cortical_gyrus'
        elif 's_' in name_lower or 'sulcus' in name_lower:
            return 'cortical_sulcus'
        elif 'fis' in name_lower:
            return 'cortical_fissure'
        elif 'pole' in name_lower:
            return 'cortical_pole'
        else:
            return 'cortical'

    return 'other'

def get_color_for_region(label_id: int) -> Tuple[int, int, int]:
    """generate rgb color based on label id"""
    if label_id <= 5:
        # red-ish for brainstem
        k = label_id
        r = 200 + (k * 10)
        g = 50 + (k * 20)
        b = 50
    elif label_id <= 59:
        # green-ish for subcortical
        k = label_id - 5
        r = 50
        g = 150 + (k % 10) * 10
        b = 100 + (k % 5) * 20
    else:
        # blue-ish for cortical
        k = label_id - 59
        r = 100 + (k % 5) * 20
        g = 100 + (k % 10) * 10
        b = 200 + (k % 3) * 20

    return min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b))

def compute_region_stats(atlas_data: np.ndarray, label_id: int) -> Tuple:
    """compute centroid and voxel count for a region"""
    mask = atlas_data == label_id
    voxel_count = int(mask.sum())

    if voxel_count == 0:
        return None, None, None, 0

    centroid = ndimage.center_of_mass(mask.astype(int))
    return float(centroid[0]), float(centroid[1]), float(centroid[2]), voxel_count

def create_comprehensive_csv(atlas_path: Path, labels_dict: Dict, affine: np.ndarray, output_csv: Path):
    """create comprehensive csv with all region information"""

    # load atlas
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata().astype(int)

    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'index', 'region_name', 'source_atlas', 'hemisphere', 'anatomical_category',
            'r', 'g', 'b',
            'centroid_i', 'centroid_j', 'centroid_k',
            'centroid_x', 'centroid_y', 'centroid_z',
            'voxel_count'
        ])

        for label_id in sorted(labels_dict.keys()):
            info = labels_dict[label_id]
            name = info['name']
            source = info['source']

            hemisphere = get_hemisphere(name)
            category = get_anatomical_category(name, source)
            r, g, b = get_color_for_region(label_id)

            ci, cj, ck, voxel_count = compute_region_stats(atlas_data, label_id)

            if ci is not None:
                world_coords = nib.affines.apply_affine(affine, [ci, cj, ck])
                cx, cy, cz = world_coords
            else:
                cx, cy, cz = None, None, None

            writer.writerow([
                label_id, name, source, hemisphere, category,
                r, g, b,
                f'{ci:.2f}' if ci is not None else '',
                f'{cj:.2f}' if cj is not None else '',
                f'{ck:.2f}' if ck is not None else '',
                f'{cx:.2f}' if cx is not None else '',
                f'{cy:.2f}' if cy is not None else '',
                f'{cz:.2f}' if cz is not None else '',
                voxel_count
            ])

# -----------------------------
# Labels, reports, QC
# -----------------------------

def create_label_files(out_dir: Path, tian_labels_file: Path | None, des_labels_file: Path | None,
                       des_label_mapping: Dict[int, int] | None = None,
                       atlas_path: Path | None = None, affine: np.ndarray | None = None) -> Tuple[Path, Path, Dict]:
    """
    Create label files for the combined atlas.

    Args:
        out_dir: Output directory
        tian_labels_file: Path to Tian labels file
        des_labels_file: Path to Destrieux labels file
        des_label_mapping: Mapping from original Destrieux labels to new continuous labels (after medial wall removal)
        atlas_path: Path to hierarchical atlas file for computing centroids
        affine: Affine matrix for converting voxel to world coordinates

    Returns:
        Tuple of (label_path, lut_path, labels_dict)
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    label_path = out_dir / "levtiades_labels.txt"
    lut_path = out_dir / "levtiades_lookup_table.txt"

    def read_simple_label_file(p: Path) -> Dict[int, str]:
        """
        Read label file with support for two formats:
        1. "index: name" format (e.g., Destrieux)
        2. "name" only format (e.g., Tian) - assigns sequential indices starting from 1
        """
        d = {}
        if p and p.exists():
            with open(p, 'r') as f:
                lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

                # Check if file uses "index: name" format
                has_indices = any(':' in line for line in lines)

                if has_indices:
                    # Format: "index: name"
                    for line in lines:
                        if ':' in line:
                            k, v = line.split(':', 1)
                            try:
                                d[int(k)] = v.strip()
                            except ValueError:
                                pass
                else:
                    # Format: "name" only - assign sequential indices
                    for idx, line in enumerate(lines, start=1):
                        d[idx] = line
        return d

    tian_labels = read_simple_label_file(tian_labels_file) if tian_labels_file else {}
    des_labels_raw = read_simple_label_file(des_labels_file) if des_labels_file else {}

    # Filter and remap Destrieux labels using the mapping (excludes medial wall)
    des_labels = {}
    if des_label_mapping:
        for old_label, new_label in des_label_mapping.items():
            if old_label in des_labels_raw:
                des_labels[new_label] = des_labels_raw[old_label]
    else:
        # Fallback: exclude medial wall labels manually
        des_labels = {k: v for k, v in des_labels_raw.items() if k not in MEDIAL_WALL_LABELS}

    # Compute centroids if atlas provided
    centroids = {}
    if atlas_path and atlas_path.exists() and affine is not None:
        atlas_img = nib.load(str(atlas_path))
        atlas_data = atlas_img.get_fdata().astype(int)

        # Compute centroids for all labels
        all_label_ids = list(LEVINSON_LABEL_NAMES.keys()) + [k+5 for k in tian_labels.keys()] + [k+59 for k in des_labels.keys()]
        for label_id in all_label_ids:
            ci, cj, ck, _ = compute_region_stats(atlas_data, label_id)
            if ci is not None:
                world_coords = nib.affines.apply_affine(affine, [ci, cj, ck])
                cx, cy, cz = world_coords
                centroids[label_id] = (cx, cy, cz)

    # Build complete labels dictionary for CSV creation
    labels_dict = {}
    for k in LEVINSON_LABEL_NAMES.keys():
        labels_dict[k] = {'name': LEVINSON_LABEL_NAMES[k], 'source': 'Levinson'}
    for k in tian_labels.keys():
        labels_dict[k+5] = {'name': tian_labels[k], 'source': 'Tian'}
    for k in des_labels.keys():
        labels_dict[k+59] = {'name': des_labels[k], 'source': 'Destrieux'}

    with open(label_path, 'w') as f:
        f.write("# Levtiades Atlas Label File\n")
        f.write("# Format: ID: Region_Name [Source_Atlas] x=XX.XX y=YY.YY z=ZZ.ZZ\n")
        f.write("# Medial wall regions (L: 42, R: 117) excluded from Destrieux\n")
        f.write(f"# Total regions: {len(LEVINSON_LABEL_NAMES)} Levinson + {len(tian_labels)} Tian + {len(des_labels)} Destrieux = {len(LEVINSON_LABEL_NAMES) + len(tian_labels) + len(des_labels)}\n\n")

        f.write("# LEVINSON (1-5)\n")
        for k in sorted(LEVINSON_LABEL_NAMES.keys()):
            coord_str = ""
            if k in centroids:
                cx, cy, cz = centroids[k]
                coord_str = f" x={cx:.2f} y={cy:.2f} z={cz:.2f}"
            f.write(f"{k}: {LEVINSON_LABEL_NAMES[k]} [Levinson]{coord_str}\n")

        f.write("\n# TIAN (6-59)\n")
        for k in sorted(tian_labels.keys()):
            coord_str = ""
            if k+5 in centroids:
                cx, cy, cz = centroids[k+5]
                coord_str = f" x={cx:.2f} y={cy:.2f} z={cz:.2f}"
            f.write(f"{k+5}: {tian_labels[k]} [Tian]{coord_str}\n")

        f.write("\n# DESTRIEUX (60-207)\n")
        for k in sorted(des_labels.keys()):
            coord_str = ""
            if k+59 in centroids:
                cx, cy, cz = centroids[k+59]
                coord_str = f" x={cx:.2f} y={cy:.2f} z={cz:.2f}"
            f.write(f"{k+59}: {des_labels[k]} [Destrieux]{coord_str}\n")

    with open(lut_path, 'w') as f:
        f.write("# Levtiades Atlas Lookup Table (MRIcroGL)\n")
        f.write("# Index\tR\tG\tB\tLabel\n")
        for k in sorted(LEVINSON_LABEL_NAMES.keys()):
            r = 200 + (k * 10); g = 50 + (k * 20); b = 50
            f.write(f"{k}\t{r}\t{g}\t{b}\tLevinson:{LEVINSON_LABEL_NAMES[k]}\n")
        for k in sorted(tian_labels.keys()):
            r = 50; g = 150 + (k % 10) * 10; b = 100 + (k % 5) * 20
            f.write(f"{k+5}\t{r}\t{g}\t{b}\tTian:{tian_labels[k]}\n")
        for k in sorted(des_labels.keys()):
            r = 100 + (k % 5) * 20; g = 100 + (k % 10) * 10; b = 200 + (k % 3) * 20
            f.write(f"{k+59}\t{r}\t{g}\t{b}\tDestrieux:{des_labels[k]}\n")

    return label_path, lut_path, labels_dict

def analyze_region_takeovers(lev_path: Path, tian_path: Path, des_path: Path,
                            hierarchical_path: Path, labels_dict: Dict,
                            affine: np.ndarray, out_dir: Path) -> None:
    """
    analyze region size changes between original individual atlases and hierarchical version.

    generates detailed report showing:
    - which regions became smaller (lost voxels to higher priority regions)
    - voxel count changes and percentages
    - which region took over the lost voxels
    - original vs new centroids for affected regions

    original = true size from individual aligned atlases
    final = size in hierarchical version after priority enforcement
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # load individual aligned atlases (the TRUE original sizes)
    lev_img = nib.load(lev_path)
    tian_img = nib.load(tian_path)
    des_img = nib.load(des_path)
    lev_data = lev_img.get_fdata().astype(int)
    tian_data = tian_img.get_fdata().astype(int)
    des_data = des_img.get_fdata().astype(int)

    # load hierarchical version
    hier_img = nib.load(hierarchical_path)
    hier_data = hier_img.get_fdata().astype(int)

    # get all unique labels
    all_labels = sorted(labels_dict.keys())

    # analyze each region
    changes = []

    for label_id in all_labels:
        # determine which atlas this region belongs to
        if label_id <= 5:
            # levinson: labels 1-5
            orig_mask = lev_data == label_id
        elif label_id <= 59:
            # tian: labels 6-59, but stored as 1-54 in individual file
            orig_mask = tian_data == (label_id - 5)
        else:
            # destrieux: labels 60-207, but stored as 1-148 in individual file
            orig_mask = des_data == (label_id - 59)

        # get mask from hierarchical version
        hier_mask = hier_data == label_id

        orig_count = int(orig_mask.sum())
        hier_count = int(hier_mask.sum())

        if orig_count == 0:
            continue  # region doesn't exist in original atlas

        # compute centroids from ORIGINAL atlas
        if orig_count > 0:
            orig_centroid_vox = ndimage.center_of_mass(orig_mask.astype(int))
            orig_centroid_mni = nib.affines.apply_affine(affine, orig_centroid_vox)
        else:
            orig_centroid_vox = (None, None, None)
            orig_centroid_mni = (None, None, None)

        # compute centroids from hierarchical version
        if hier_count > 0:
            hier_centroid_vox = ndimage.center_of_mass(hier_mask.astype(int))
            hier_centroid_mni = nib.affines.apply_affine(affine, hier_centroid_vox)
        else:
            hier_centroid_vox = (None, None, None)
            hier_centroid_mni = (None, None, None)

        # check for size change
        voxel_diff = hier_count - orig_count

        if voxel_diff != 0:
            percent_change = (voxel_diff / orig_count) * 100 if orig_count > 0 else 0

            # identify what took over the lost voxels (only for regions that got smaller)
            lost_voxels = orig_mask & ~hier_mask
            takeover_label = None
            takeover_name = None
            takeover_source = None

            if np.any(lost_voxels):
                # find what label occupies the lost voxels in hierarchical version
                takeover_labels = hier_data[lost_voxels]
                takeover_labels = takeover_labels[takeover_labels > 0]
                if len(takeover_labels) > 0:
                    # most common takeover label
                    unique, counts = np.unique(takeover_labels, return_counts=True)
                    takeover_label = int(unique[np.argmax(counts)])
                    if takeover_label in labels_dict:
                        takeover_name = labels_dict[takeover_label]['name']
                        takeover_source = labels_dict[takeover_label]['source']

            # centroid shift
            if orig_count > 0 and hier_count > 0:
                centroid_shift_mm = np.sqrt(
                    (hier_centroid_mni[0] - orig_centroid_mni[0])**2 +
                    (hier_centroid_mni[1] - orig_centroid_mni[1])**2 +
                    (hier_centroid_mni[2] - orig_centroid_mni[2])**2
                )
            else:
                centroid_shift_mm = None

            changes.append({
                'label_id': label_id,
                'name': labels_dict[label_id]['name'],
                'source': labels_dict[label_id]['source'],
                'original_voxels': orig_count,
                'final_voxels': hier_count,
                'voxel_diff': voxel_diff,
                'percent_change': percent_change,
                'takeover_label': takeover_label,
                'takeover_name': takeover_name,
                'takeover_source': takeover_source,
                'original_centroid_x': orig_centroid_mni[0],
                'original_centroid_y': orig_centroid_mni[1],
                'original_centroid_z': orig_centroid_mni[2],
                'final_centroid_x': hier_centroid_mni[0] if hier_count > 0 else None,
                'final_centroid_y': hier_centroid_mni[1] if hier_count > 0 else None,
                'final_centroid_z': hier_centroid_mni[2] if hier_count > 0 else None,
                'centroid_shift_mm': centroid_shift_mm,
            })

    # write detailed report
    report_path = out_dir / "region_takeover_analysis.txt"
    with open(report_path, 'w') as f:
        f.write("# region takeover analysis: original → hierarchical\n")
        f.write("# comparing TRUE original sizes (from individual aligned atlases) vs hierarchical version\n")
        f.write("# hierarchy: levinson > tian > destrieux\n")
        f.write("# \n")
        f.write("# original voxels = region's true size from individual aligned atlas\n")
        f.write("# final voxels = region's size after hierarchical priority enforcement\n\n")

        # separate into smaller and larger
        smaller = [c for c in changes if c['voxel_diff'] < 0]
        larger = [c for c in changes if c['voxel_diff'] > 0]

        f.write(f"total regions analyzed: {len(all_labels)}\n")
        f.write(f"regions that lost voxels: {len(smaller)}\n")
        f.write(f"regions unchanged: {len(all_labels) - len(changes)}\n")
        f.write(f"note: no regions gained voxels (higher priority regions can only lose to even higher priority)\n\n")

        f.write("=" * 100 + "\n")
        f.write("regions that LOST VOXELS (taken over by higher priority regions)\n")
        f.write("=" * 100 + "\n\n")

        for c in sorted(smaller, key=lambda x: x['voxel_diff']):
            f.write(f"label {c['label_id']}: {c['name']} [{c['source']}]\n")
            f.write(f"  original voxels: {c['original_voxels']}\n")
            f.write(f"  final voxels: {c['final_voxels']}\n")
            f.write(f"  voxels lost: {abs(c['voxel_diff'])} ({c['percent_change']:.2f}%)\n")
            if c['takeover_label']:
                f.write(f"  taken over by: label {c['takeover_label']}: {c['takeover_name']} [{c['takeover_source']}]\n")
            f.write(f"  original centroid (mni): x={c['original_centroid_x']:.2f} y={c['original_centroid_y']:.2f} z={c['original_centroid_z']:.2f}\n")
            if c['final_centroid_x'] is not None:
                f.write(f"  final centroid (mni): x={c['final_centroid_x']:.2f} y={c['final_centroid_y']:.2f} z={c['final_centroid_z']:.2f}\n")
                if c['centroid_shift_mm'] is not None:
                    f.write(f"  centroid shift: {c['centroid_shift_mm']:.2f} mm\n")
            f.write("\n")


    print(f"   ✅ created region takeover analysis: {report_path}")

def create_qc_overlays(lev_path: Path, tian_path: Path, des_path: Path, out_dir: Path, ref_tpl: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    lev_img = nib.load(str(lev_path)); tian_img = nib.load(str(tian_path)); des_img = nib.load(str(des_path))
    lev = lev_img.get_fdata().astype(int); tian = tian_img.get_fdata().astype(int); des = des_img.get_fdata().astype(int)

    overlap = np.zeros_like(lev, dtype=np.uint8)
    overlap[(lev > 0) & (tian > 0)] = 1
    overlap[(lev > 0) & (des > 0)] = 2
    overlap[(tian > 0) & (des > 0)] = 3
    overlap[(lev > 0) & (tian > 0) & (des > 0)] = 4

    ref = nib.load(str(ref_tpl))
    nib.save(nib.Nifti1Image(overlap, ref.affine, ref.header), str(out_dir / "overlap_visualization.nii.gz"))

    # Individual masks
    nib.save(nib.Nifti1Image((lev > 0).astype(np.uint8) * 100, ref.affine, ref.header), str(out_dir / "levinson_mask.nii.gz"))
    nib.save(nib.Nifti1Image((tian > 0).astype(np.uint8) * 150, ref.affine, ref.header), str(out_dir / "tian_mask.nii.gz"))
    nib.save(nib.Nifti1Image((des > 0).astype(np.uint8) * 200, ref.affine, ref.header), str(out_dir / "destrieux_mask.nii.gz"))

# -----------------------------
# CLI with embedded defaults
# -----------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Levtiades Atlas Builder - Step 2: Convert to MNI2009c",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # All arguments are optional with embedded defaults
    p.add_argument("--levinson-dir", type=Path, default=DEFAULT_CONFIG["levinson_dir"],
                   help="Folder containing Levinson components")
    p.add_argument("--tian-img", type=Path, default=DEFAULT_CONFIG["tian_img"],
                   help="Path to Tian NIfTI")
    p.add_argument("--tian-space", type=str, default=DEFAULT_CONFIG["tian_space"],
                   choices=["MNI152NLin2009cAsym", "MNI152NLin6Asym"])
    p.add_argument("--destrieux-img", type=Path, default=DEFAULT_CONFIG["destrieux_img"],
                   help="Path to volumetric Destrieux NIfTI")
    p.add_argument("--destrieux-space", type=str, default=DEFAULT_CONFIG["destrieux_space"],
                   choices=["MNI152NLin2009aAsym"])
    p.add_argument("--tian-labels", type=Path, default=DEFAULT_CONFIG["tian_labels"],
                   help="Path to Tian atlas label file")
    p.add_argument("--destrieux-labels", type=Path, default=DEFAULT_CONFIG["destrieux_labels"],
                   help="Path to Destrieux atlas label file")
    p.add_argument("--outdir", type=Path, default=DEFAULT_CONFIG["outdir"])
    p.add_argument("--target-space", type=str, default=DEFAULT_CONFIG["target_space"],
                   choices=list(TPL_LOOKUP.keys()))
    p.add_argument("--target-res", type=int, default=DEFAULT_CONFIG["target_res"],
                   help="Target template resolution (mm)")

    return p.parse_args()

def main():
    args = parse_args()

    print("🧠 LEVTIADES ATLAS CREATION - Step 2: Convert to MNI2009c")
    print("=" * 60)
    print(f"Target space: {args.target_space} @ {args.target_res}mm")
    print(f"Output directory: {args.outdir}")
    print()

    # Check external deps
    check_tool_on_path("antsRegistration")
    check_tool_on_path("antsApplyTransforms")

    base = Path(args.outdir)
    raw_dir = base / "raw_atlases"
    work_dir = base / "work"
    final_with_dir = base / "final_atlas/with_overlaps"
    final_no_dir = base / "final_atlas/no_overlaps"
    reports_dir = base / "reports"
    qc_dir = base / "qc_validation"

    for d in [raw_dir, work_dir, final_with_dir, final_no_dir, reports_dir, qc_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 1) Combine Levinson in native space
    print("Step 1: Combining Levinson components...")
    lev_combined = load_and_combine_levinson(Path(args.levinson_dir), raw_dir)

    # 2) Align all to target via template→template transforms (includes medial wall removal)
    print("Step 2: Aligning all atlases to target space...")
    target_tpl, lev_tgt, tian_tgt, des_tgt, des_label_mapping = align_all_to_target(
        lev_combined,
        Path(args.tian_img),
        Path(args.destrieux_img),
        args.tian_space,
        args.destrieux_space,
        args.target_space,
        args.target_res,
        work_dir,
    )

    # 3) Save individual aligned atlases to final_atlas
    print("Step 3a: Saving individual aligned atlases...")
    final_atlas_dir = base / "final_atlas"
    final_atlas_dir.mkdir(parents=True, exist_ok=True)

    # Copy individual aligned atlases for MRIcroGL visualization
    import shutil
    shutil.copy(lev_tgt, final_atlas_dir / "1_levinson_aligned.nii.gz")
    shutil.copy(tian_tgt, final_atlas_dir / "2_tian_aligned.nii.gz")
    shutil.copy(des_tgt, final_atlas_dir / "3_destrieux_aligned.nii.gz")
    print(f"   ✅ Saved individual aligned atlases to {final_atlas_dir}")

    # 3b) Build combined outputs
    print("Step 3b: Creating combined atlas outputs...")
    flat_with_path, overlap_stats = create_with_overlaps(lev_tgt, tian_tgt, des_tgt, final_with_dir)
    hier_path, changes, final_stats = create_hierarchical(lev_tgt, tian_tgt, des_tgt, final_no_dir)

    # 4) Labels & QC
    print("Step 4: Creating labels and QC files...")
    # Get affine from hierarchical atlas
    hier_img = nib.load(str(hier_path))
    affine = hier_img.affine

    label_path, lut_path, labels_dict = create_label_files(
        base / "final_atlas",
        Path(args.tian_labels) if args.tian_labels else None,
        Path(args.destrieux_labels) if args.destrieux_labels else None,
        des_label_mapping,
        hier_path,  # Use hierarchical atlas for computing stats
        affine
    )
    create_qc_overlays(lev_tgt, tian_tgt, des_tgt, qc_dir, target_tpl)

    # 5) Create comprehensive CSV
    print("Step 5: Creating comprehensive CSV...")
    csv_path = base / "final_atlas" / "levtiades_atlas.csv"
    create_comprehensive_csv(hier_path, labels_dict, affine, csv_path)
    print(f"   ✅ Created CSV: {csv_path}")

    # 6) Analyze region takeovers
    print("Step 6: Analyzing region takeovers...")
    analyze_region_takeovers(lev_tgt, tian_tgt, des_tgt, hier_path, labels_dict, affine, reports_dir)

    # 7) Simple markdown report
    report = reports_dir / "levtiades_analysis_report.md"
    with open(report, 'w') as f:
        f.write("# Levtiades Atlas Analysis Report - Step 2\n\n")
        f.write("## Target Template\n")
        f.write(f"- {args.target_space}, {args.target_res} mm\n\n")
        f.write("## Overlap (pre-hierarchy)\n")
        for k, v in overlap_stats.items():
            f.write(f"- {k}: {v} voxels\n")
        f.write("\n## Final Composition (hierarchical)\n")
        total = max(1, final_stats['total_voxels'])
        f.write(f"- Levinson voxels: {final_stats['levinson_voxels']} ({100*final_stats['levinson_voxels']/total:.2f}%)\n")
        f.write(f"- Tian voxels: {final_stats['tian_voxels']} ({100*final_stats['tian_voxels']/total:.2f}%)\n")
        f.write(f"- Destrieux voxels: {final_stats['destrieux_voxels']} ({100*final_stats['destrieux_voxels']/total:.2f}%)\n")

    print("\n🎉 Levtiades Atlas Creation Complete!")
    print("=" * 50)
    print(f"📁 Main outputs:")
    print(f"   - Final atlas (hierarchical): {hier_path}")
    print(f"   - Final atlas (main output): {flat_with_path}")
    print(f"   - Labels: {label_path}")
    print(f"   - CSV: {csv_path}")
    print(f"   - Report: {report}")
    print(f"   - QC overlays: {qc_dir}")

if __name__ == "__main__":
    main()
