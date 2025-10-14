#!/usr/bin/env python3
"""
Levtiades Atlas Builder (Refactored)
===================================
Combines three atlases into a single product in a *common MNI template* using
**true template-to-template registration** (ANTs), *not* mere voxel-grid
resampling.

Inputs (examples & expected native spaces)
-----------------------------------------
- Levinson–Bari Limbic Brainstem Atlas components (LC, NTS, VTA, PAG, DRN)
  • Assumed native space: MNI152NLin2009bAsym (T1w, 0.5 mm reference)
- Tian2020 Subcortex Atlas
  • Provided in either MNI152NLin2009cAsym or MNI152NLin6Asym
- Destrieux 2009 volumetric (as distributed by Nilearn)
  • Native space: MNI152NLin2009aAsym (ICBM 2009a asym); SURFACE version is fsaverage5 (not used here)

Target (default)
----------------
- MNI152NLin2009cAsym at 2 mm isotropic

Key operations
--------------
1) Combine Levinson components in their native space (reslicing *within Levinson only*).
2) Compute/fetch template→template transforms between *T1w templates* (TemplateFlow) with ANTs.
3) Apply those transforms (NearestNeighbour) to each label atlas → target template.
4) Optionally harmonise voxel grid (resample_to_img with NearestNeighbour).
5) Produce two outputs: WITH overlaps (multichannel) and hierarchical NO overlaps.
6) Emit label files, lookup table, simple report, and QC overlays.

Requirements
------------
- Python: nibabel, nilearn, numpy, pandas, templateflow, scipy
- External: ANTs (antsRegistrationSyNQuick.sh, antsApplyTransforms) available on PATH

Usage
-----
python levtiades_refactor.py \
  --levinson-dir "data/Levinson-Bari Limbic Brainstem Atlas (Levinson 2022)" \
  --tian-img tiandes_atlas/raw_atlases/tian_subcortical.nii.gz \
  --tian-space MNI152NLin2009cAsym \
  --destrieux-img tiandes_atlas/raw_atlases/destrieux_cortical.nii.gz \
  --destrieux-space MNI152NLin2009aAsym \
  --outdir levtiades_atlas \
  --target-space MNI152NLin2009cAsym \
  --target-res 2

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
from scipy import ndimage  # noqa: F401 (used in potential extensions)
from templateflow.api import get as tf_get

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
    "MNI152NLin2009aAsym": {"suffix": "T1w", "resolution": 1},
    "MNI152NLin2009bAsym": {"suffix": "T1w", "resolution": 0},  # 0.5 mm commonly tagged as res-0
    "MNI152NLin2009cAsym": {"suffix": "T1w", "resolution": 2},
    "MNI152NLin6Asym": {"suffix": "T1w", "resolution": 2},
}


def fetch_tpl(space: str, res: int | None = None) -> Path:
    meta = TPL_LOOKUP.get(space)
    if meta is None:
        raise ValueError(f"Unsupported template in this script: {space}")
    suffix = meta["suffix"]
    resolution = res if res is not None else meta["resolution"]
    tpl_path = tf_get(space, suffix=suffix, resolution=resolution)
    return Path(tpl_path)


# -----------------------------
# ANTs registration wrappers
# -----------------------------

def compute_template_transform(moving_tpl: Path, fixed_tpl: Path, out_prefix: Path) -> Dict[str, Path]:
    """Compute moving→fixed transform between T1w templates using antsRegistrationSyNQuick.sh.
    Returns dict with 'warp' and 'affine' paths.
    """
    check_tool_on_path("antsRegistrationSyNQuick.sh")
    out_prefix_parent = out_prefix.parent
    out_prefix_parent.mkdir(parents=True, exist_ok=True)

    run([
        "antsRegistrationSyNQuick.sh", "-d", "3",
        "-f", str(fixed_tpl),
        "-m", str(moving_tpl),
        "-o", str(out_prefix) + "_",
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
            rs = image.resample_to_img(imgs[key], ref, interpolation="nearest")
            data = rs.get_fdata() > 0
        ref_data[data] = label
        print(f"  Component {key} → label {label}: voxels={int(data.sum())}")

    out_path = out_dir / "levinson_combined.nii.gz"
    save_nifti_like(ref, ref_data, out_path)
    return out_path


# -----------------------------
# Atlas alignment and merging
# -----------------------------

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
) -> Tuple[Path, Path, Path, Path]:
    """
    Returns tuple of (target_T1w, levinson_in_target, tian_in_target, destrieux_in_target)
    """
    work_dir.mkdir(parents=True, exist_ok=True)

    target_tpl = fetch_tpl(target_space, target_res)

    # Levinson 2009b → target
    levinson_tpl = fetch_tpl("MNI152NLin2009bAsym", res=None)  # T1w 0.5 mm
    tf_lev = work_dir / "tf_2009b_to_target"
    lev_tr = compute_template_transform(levinson_tpl, target_tpl, tf_lev)
    lev_out = work_dir / "levinson_in_target.nii.gz"
    apply_transform_nn(levinson_combined, target_tpl, [lev_tr["warp"], lev_tr["affine"]], lev_out)

    # Tian: either already in target, or NLin6 → target
    if tian_space == target_space:
        # Resample to exact target grid using ANTs (identity transform) for consistency
        tian_out = work_dir / "tian_in_target.nii.gz"
        identity_mat = work_dir / "identity.mat"
        if not identity_mat.exists():
            with open(identity_mat, 'w') as f:
                f.write("#Insight Transform File V1.0
")
                f.write("#Transform 0
")
                f.write("Transform: AffineTransform_double_3_3
")
                f.write("Parameters: 1 0 0 0 1 0 0 0 1 0 0 0
")
                f.write("FixedParameters: 0 0 0
")
        apply_transform_nn(tian_img, target_tpl, [identity_mat], tian_out)
    elif tian_space == "MNI152NLin6Asym" and target_space != "MNI152NLin6Asym":
        nlin6_tpl = fetch_tpl("MNI152NLin6Asym", res=None)
        tf_tian = work_dir / "tf_nlin6_to_target"
        tian_tr = compute_template_transform(nlin6_tpl, target_tpl, tf_tian)
        tian_out = work_dir / "tian_in_target.nii.gz"
        apply_transform_nn(tian_img, target_tpl, [tian_tr["warp"], tian_tr["affine"]], tian_out)
    else:
        raise ValueError(f"Unsupported Tian space flow: {tian_space} → {target_space}")

    # Destrieux: 2009a → target
    if destrieux_space == "MNI152NLin2009aAsym":
        a_tpl = fetch_tpl("MNI152NLin2009aAsym", res=None)
        tf_des = work_dir / "tf_2009a_to_target"
        des_tr = compute_template_transform(a_tpl, target_tpl, tf_des)
        des_out = work_dir / "destrieux_in_target.nii.gz"
        apply_transform_nn(destrieux_img, target_tpl, [des_tr["warp"], des_tr["affine"]], des_out)
    else:
        raise ValueError(f"Unsupported Destrieux space: {destrieux_space}")

    return target_tpl, lev_out, tian_out, des_out


def create_with_overlaps(lev_path: Path, tian_path: Path, des_path: Path, out_dir: Path) -> Tuple[Path, dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    lev_img = nib.load(str(lev_path))
    tian_img = nib.load(str(tian_path))
    des_img = nib.load(str(des_path))

    lev = lev_img.get_fdata().astype(int)
    tian = tian_img.get_fdata().astype(int)
    des = des_img.get_fdata().astype(int)

    multi = np.zeros(list(lev.shape) + [3], dtype=np.int16)
    multi[..., 0] = lev
    tian_off = np.where(tian > 0, tian + 100, 0)
    des_off = np.where(des > 0, des + 200, 0)
    multi[..., 1] = tian_off
    multi[..., 2] = des_off

    flat = np.zeros_like(lev, dtype=np.int16)
    flat[lev > 0] = lev[lev > 0]
    flat[tian > 0] = tian_off[tian > 0]
    flat[des > 0] = des_off[des > 0]

    multi_path = out_dir / "levtiades_multichannel.nii.gz"
    flat_path = out_dir / "levtiades_flat_with_overlaps.nii.gz"
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

    # Layer 3: Destrieux
    des_mask = des > 0
    combined[des_mask] = des[des_mask] + 200

    # Layer 2: Tian
    tian_mask = tian > 0
    replaced_by_tian = (combined > 200) & tian_mask
    if np.any(replaced_by_tian):
        replaced_regions = combined[replaced_by_tian] - 200
        unique = np.unique(replaced_regions)
        for r in unique:
            c = int((replaced_regions == r).sum())
            changes['destrieux_regions_affected'][int(r)] = c
            changes['destrieux_replaced_by_tian'] += c
    combined[tian_mask] = tian[tian_mask] + 100

    # Layer 1: Levinson
    lev_mask = lev > 0
    replaced_tian = ((combined > 100) & (combined < 200)) & lev_mask
    if np.any(replaced_tian):
        replaced_regions = combined[replaced_tian] - 100
        unique = np.unique(replaced_regions)
        for r in unique:
            c = int((replaced_regions == r).sum())
            changes['tian_regions_affected'][int(r)] = c
            changes['tian_replaced_by_levinson'] += c
    replaced_des = (combined > 200) & lev_mask
    if np.any(replaced_des):
        changes['destrieux_replaced_by_levinson'] += int(replaced_des.sum())

    combined[lev_mask] = lev[lev_mask]

    hier_path = out_dir / "levtiades_hierarchical.nii.gz"
    save_nifti_like(lev_img, combined, hier_path)

    final_stats = {
        'levinson_voxels': int(((combined > 0) & (combined < 100)).sum()),
        'tian_voxels': int(((combined > 100) & (combined < 200)).sum()),
        'destrieux_voxels': int((combined > 200).sum()),
        'total_voxels': int((combined > 0).sum()),
    }

    return hier_path, changes, final_stats


# -----------------------------
# Labels, reports, QC
# -----------------------------

def create_label_files(out_dir: Path, tian_labels_file: Path | None, des_labels_file: Path | None) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    label_path = out_dir / "levtiades_labels.txt"
    lut_path = out_dir / "levtiades_lookup_table.txt"

    def read_simple_label_file(p: Path) -> Dict[int, str]:
        d = {}
        if p and p.exists():
            with open(p, 'r') as f:
                for line in f:
                    if ':' in line and not line.strip().startswith('#'):
                        k, v = line.strip().split(':', 1)
                        try:
                            d[int(k)] = v.strip()
                        except ValueError:
                            pass
        return d

    tian_labels = read_simple_label_file(tian_labels_file) if tian_labels_file else {}
    des_labels = read_simple_label_file(des_labels_file) if des_labels_file else {}

    with open(label_path, 'w') as f:
        f.write("# Levtiades Atlas Label File\n")
        f.write("# Format: ID: Region_Name [Source_Atlas]\n\n")
        f.write("# LEVINSON (1-5)\n")
        for k in sorted(LEVINSON_LABEL_NAMES.keys()):
            f.write(f"{k}: {LEVINSON_LABEL_NAMES[k]} [Levinson]\n")
        f.write("\n# TIAN (101-...)\n")
        for k in sorted(tian_labels.keys()):
            f.write(f"{k+100}: {tian_labels[k]} [Tian]\n")
        f.write("\n# DESTRIEUX (201-...)\n")
        for k in sorted(des_labels.keys()):
            f.write(f"{k+200}: {des_labels[k]} [Destrieux]\n")

    with open(lut_path, 'w') as f:
        f.write("# Levtiades Atlas Lookup Table (MRIcroGL)\n")
        f.write("# Index\tR\tG\tB\tLabel\n")
        for k in sorted(LEVINSON_LABEL_NAMES.keys()):
            r = 200 + (k * 10); g = 50 + (k * 20); b = 50
            f.write(f"{k}\t{r}\t{g}\t{b}\tLevinson:{LEVINSON_LABEL_NAMES[k]}\n")
        for k in sorted(tian_labels.keys()):
            r = 50; g = 150 + (k % 10) * 10; b = 100 + (k % 5) * 20
            f.write(f"{k+100}\t{r}\t{g}\t{b}\tTian:{tian_labels[k]}\n")
        for k in sorted(des_labels.keys()):
            r = 100 + (k % 5) * 20; g = 100 + (k % 10) * 10; b = 200 + (k % 3) * 20
            f.write(f"{k+200}\t{r}\t{g}\t{b}\tDestrieux:{des_labels[k]}\n")

    return label_path, lut_path


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
# CLI
# -----------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Levtiades builder with template-to-template registration")
    p.add_argument("--levinson-dir", type=Path, required=True, help="Folder containing Levinson components")
    p.add_argument("--tian-img", type=Path, required=True, help="Path to Tian NIfTI (either 2009cAsym or NLin6Asym)")
    p.add_argument("--tian-space", type=str, choices=["MNI152NLin2009cAsym", "MNI152NLin6Asym"], required=True)
    p.add_argument("--destrieux-img", type=Path, required=True, help="Path to volumetric Destrieux NIfTI (Nilearn)")
    p.add_argument("--destrieux-space", type=str, default="MNI152NLin2009aAsym", choices=["MNI152NLin2009aAsym"], help="Native space of volumetric Destrieux")
    p.add_argument("--tian-labels", type=Path, default=None, help="Path to Tian atlas label file (optional)")
    p.add_argument("--destrieux-labels", type=Path, default=None, help="Path to Destrieux atlas label file (optional)")
    p.add_argument("--outdir", type=Path, default=Path("levtiades_atlas"))
    p.add_argument("--target-space", type=str, default="MNI152NLin2009cAsym", choices=list(TPL_LOOKUP.keys()))
    p.add_argument("--target-res", type=int, default=2, help="Target template resolution (mm)")
    return p.parse_args()


def main():
    args = parse_args()

    # Check external deps
    check_tool_on_path("antsRegistrationSyNQuick.sh")
    check_tool_on_path("antsApplyTransforms")

    base = args.outdir
    raw_dir = base / "raw_atlases"
    work_dir = base / "work"
    aligned_dir = base / "aligned"
    final_with_dir = base / "final/with_overlaps"
    final_no_dir = base / "final/no_overlaps"
    reports_dir = base / "reports"
    qc_dir = base / "qc"

    for d in [raw_dir, work_dir, aligned_dir, final_with_dir, final_no_dir, reports_dir, qc_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print("🧠 LEVTIADES ATLAS CREATION (Refactored)")

    # 1) Combine Levinson in native space
    lev_combined = load_and_combine_levinson(args.levinson_dir, raw_dir)

    # 2) Align all to target via template→template transforms
    target_tpl, lev_tgt, tian_tgt, des_tgt = align_all_to_target(
        lev_combined,
        args.tian_img,
        args.destrieux_img,
        args.tian_space,
        args.destrieux_space,
        args.target_space,
        args.target_res,
        work_dir,
    )

    # 3) Build outputs
    flat_with_path, overlap_stats = create_with_overlaps(lev_tgt, tian_tgt, des_tgt, final_with_dir)
    hier_path, changes, final_stats = create_hierarchical(lev_tgt, tian_tgt, des_tgt, final_no_dir)

    # 4) Labels & QC
    flat_with_path, overlap_stats = create_with_overlaps(lev_aligned, tian_aligned, des_aligned, final_with_dir)
    hier_path, changes, final_stats = create_hierarchical(lev_aligned, tian_aligned, des_aligned, final_no_dir)

    # 5) Labels & QC
    label_path, lut_path = create_label_files(base / "final", args.tian_labels, args.destrieux_labels)
    create_qc_overlays(lev_aligned, tian_aligned, des_aligned, qc_dir, target_tpl)

    # 6) Simple markdown report
    report = reports_dir / "levtiades_analysis_report.md"
    with open(report, 'w') as f:
        f.write("# Levtiades Atlas Analysis Report (Refactored)\n\n")
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

    print("\n🎉 Complete! Outputs:")
    print(f"- Aligned (target grid): {aligned_dir}")
    print(f"- Final with overlaps: {final_with_dir}")
    print(f"- Final hierarchical: {final_no_dir}")
    print(f"- Labels: {label_path}")
    print(f"- Lookup table: {lut_path}")
    print(f"- QC overlays: {qc_dir}")
    print(f"- Report: {report}")


if __name__ == "__main__":
    main()
