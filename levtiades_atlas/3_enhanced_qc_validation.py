#!/usr/bin/env python3
"""
Step 3: Enhanced QC and Validation for Levtiades Atlas
======================================================

Creates comprehensive quality control visualizations and validation reports
specifically designed for expert review (e.g., Claude Bajada's requirements).

This script generates:
1. Registration quality assessments with before/after comparisons
2. Overlap analysis visualizations
3. Centroid validation with statistical analysis
4. Expert-review ready QC images and reports

Run after Step 2 (2_levtiades_to_mni2009c.py) to generate validation materials.
"""

import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics import silhouette_score

def enhanced_qc_analysis():
    """Generate comprehensive QC analysis for expert review"""

    print("🔍 ENHANCED QC & VALIDATION ANALYSIS")
    print("=" * 50)

    base_dir = Path(".")
    validation_dir = base_dir / "qc_validation"
    qc_dir = validation_dir / "qc_overlays"
    centroid_dir = validation_dir / "centroid_validation"
    reg_qc_dir = validation_dir / "registration_qc"

    # Create directories
    for dir_path in [qc_dir, centroid_dir, reg_qc_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # 1. Registration Quality Assessment
    print("\n📊 Step 1: Registration Quality Assessment")
    create_registration_qc(reg_qc_dir)

    # 2. Enhanced Overlap Analysis
    print("\n🎯 Step 2: Enhanced Overlap Analysis")
    create_overlap_analysis(qc_dir)

    # 3. Centroid Validation with Statistics
    print("\n📍 Step 3: Centroid Validation Analysis")
    create_centroid_analysis(centroid_dir)

    # 4. Expert Summary Report
    print("\n📝 Step 4: Expert Summary Report")
    create_expert_report(validation_dir)

    print("\n✅ Enhanced QC Analysis Complete!")
    print(f"📁 QC validation outputs: {validation_dir}")

def create_registration_qc(output_dir):
    """Create registration quality control visualizations"""

    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for aligned atlases from Step 2
    work_dir = Path("work")
    if not work_dir.exists():
        print("⚠️  Step 2 work directory not found. Run 2_levtiades_to_mni2009c.py first.")
        return

    # Look for aligned atlases
    aligned_files = {
        'levinson': work_dir / "levinson_in_target.nii.gz",
        'tian': work_dir / "tian_in_target.nii.gz",
        'destrieux': work_dir / "destrieux_in_target.nii.gz"
    }

    for name, path in aligned_files.items():
        if path.exists():
            try:
                img = nib.load(path)
                data = img.get_fdata()

                # Create basic visualization
                fig, axes = plt.subplots(2, 3, figsize=(15, 10))
                fig.suptitle(f'Registration QC: {name.title()} Atlas', fontsize=16)

                # Axial views at different levels
                mid_z = data.shape[2] // 2
                levels = [mid_z - 10, mid_z, mid_z + 10]

                for i, z in enumerate(levels):
                    if 0 <= z < data.shape[2]:
                        # Original data
                        axes[0, i].imshow(data[:, :, z].T, origin='lower', cmap='nipy_spectral')
                        axes[0, i].set_title(f'Slice {z}')
                        axes[0, i].axis('off')

                        # Binary mask
                        binary = (data[:, :, z] > 0).astype(int)
                        axes[1, i].imshow(binary.T, origin='lower', cmap='gray')
                        axes[1, i].set_title(f'Mask {z}')
                        axes[1, i].axis('off')

                plt.tight_layout()
                plt.savefig(output_dir / f'{name}_registration_qc.png', dpi=300, bbox_inches='tight')
                plt.close()

                print(f"   ✅ {name} registration QC saved")

            except Exception as e:
                print(f"   ❌ Error processing {name}: {e}")
        else:
            print(f"   ⚠️  {name} aligned atlas not found at {path}")

def create_overlap_analysis(output_dir):
    """Create detailed overlap analysis visualizations"""

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load QC overlays if they exist (Step 2 puts them in qc_validation/, not qc_overlays/)
    qc_validation_dir = Path("qc_validation")
    qc_files = list(qc_validation_dir.glob("*.nii.gz"))

    if not qc_files:
        print("   ⚠️  No QC overlay files found. Run Step 2 first.")
        return

    # Create overlap statistics table
    overlap_stats = []

    for qc_file in qc_files:
        try:
            img = nib.load(qc_file)
            data = img.get_fdata()

            # Count different overlap types
            unique_vals = np.unique(data[data > 0])
            for val in unique_vals:
                count = int((data == val).sum())
                overlap_stats.append({
                    'file': qc_file.name,
                    'overlap_type': int(val),
                    'voxel_count': count,
                    'volume_mm3': count * 8  # 2x2x2mm voxels
                })
        except Exception as e:
            print(f"   ❌ Error processing {qc_file}: {e}")

    if overlap_stats:
        df = pd.DataFrame(overlap_stats)
        df.to_csv(output_dir / "overlap_statistics.csv", index=False)

        # Create visualization
        if len(df) > 0:
            plt.figure(figsize=(12, 8))
            sns.barplot(data=df, x='overlap_type', y='volume_mm3', hue='file')
            plt.title('Atlas Overlap Analysis')
            plt.xlabel('Overlap Type')
            plt.ylabel('Volume (mm³)')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.savefig(output_dir / "overlap_analysis.png", dpi=300, bbox_inches='tight')
            plt.close()

            print("   ✅ Overlap analysis completed")

def create_centroid_analysis(output_dir):
    """Create centroid validation analysis with detailed statistics"""

    output_dir.mkdir(parents=True, exist_ok=True)

    # Look for existing centroid validation files
    centroid_files = list(output_dir.glob("*.csv"))

    if not centroid_files:
        print("   ⚠️  No centroid validation files found")
        return

    for csv_file in centroid_files:
        try:
            df = pd.read_csv(csv_file)

            if 'distance_mm' in df.columns:
                # Statistical analysis
                stats = {
                    'total_regions': len(df),
                    'mean_distance': df['distance_mm'].mean(),
                    'std_distance': df['distance_mm'].std(),
                    'max_distance': df['distance_mm'].max(),
                    'min_distance': df['distance_mm'].min(),
                    'median_distance': df['distance_mm'].median(),
                    'q95_distance': df['distance_mm'].quantile(0.95),
                    'perfect_matches': len(df[df['distance_mm'] < 1.0]),
                    'acceptable_matches': len(df[df['distance_mm'] < 2.0])
                }

                # Create visualization
                fig, axes = plt.subplots(2, 2, figsize=(15, 12))
                fig.suptitle('Centroid Validation Analysis', fontsize=16)

                # Histogram of distances
                axes[0, 0].hist(df['distance_mm'], bins=20, edgecolor='black', alpha=0.7)
                axes[0, 0].axvline(stats['mean_distance'], color='red', linestyle='--',
                                 label=f'Mean: {stats["mean_distance"]:.2f}mm')
                axes[0, 0].set_xlabel('Distance (mm)')
                axes[0, 0].set_ylabel('Count')
                axes[0, 0].set_title('Distribution of Centroid Distances')
                axes[0, 0].legend()

                # Box plot by atlas source (if available)
                if 'source' in df.columns:
                    sns.boxplot(data=df, x='source', y='distance_mm', ax=axes[0, 1])
                    axes[0, 1].set_title('Distance by Atlas Source')
                    axes[0, 1].tick_params(axis='x', rotation=45)

                # Cumulative distribution
                sorted_distances = np.sort(df['distance_mm'])
                cumulative = np.arange(1, len(sorted_distances) + 1) / len(sorted_distances)
                axes[1, 0].plot(sorted_distances, cumulative)
                axes[1, 0].axvline(1.0, color='green', linestyle='--', label='1mm threshold')
                axes[1, 0].axvline(2.0, color='orange', linestyle='--', label='2mm threshold')
                axes[1, 0].set_xlabel('Distance (mm)')
                axes[1, 0].set_ylabel('Cumulative Probability')
                axes[1, 0].set_title('Cumulative Distribution of Distances')
                axes[1, 0].legend()

                # Summary statistics text
                stats_text = f"""
                Total Regions: {stats['total_regions']}
                Mean Distance: {stats['mean_distance']:.3f} ± {stats['std_distance']:.3f} mm
                Median Distance: {stats['median_distance']:.3f} mm
                Max Distance: {stats['max_distance']:.3f} mm
                95th Percentile: {stats['q95_distance']:.3f} mm

                Perfect Matches (<1mm): {stats['perfect_matches']} ({100*stats['perfect_matches']/stats['total_regions']:.1f}%)
                Acceptable Matches (<2mm): {stats['acceptable_matches']} ({100*stats['acceptable_matches']/stats['total_regions']:.1f}%)
                """

                axes[1, 1].text(0.1, 0.9, stats_text, transform=axes[1, 1].transAxes,
                               fontsize=10, verticalalignment='top', fontfamily='monospace')
                axes[1, 1].axis('off')

                plt.tight_layout()
                plt.savefig(output_dir / f"centroid_analysis_{csv_file.stem}.png",
                           dpi=300, bbox_inches='tight')
                plt.close()

                # Save detailed statistics
                stats_df = pd.DataFrame([stats])
                stats_df.to_csv(output_dir / f"centroid_statistics_{csv_file.stem}.csv", index=False)

                print(f"   ✅ Centroid analysis for {csv_file.name} completed")

        except Exception as e:
            print(f"   ❌ Error processing {csv_file}: {e}")

def create_expert_report(output_dir):
    """Create comprehensive expert review report"""

    report_path = output_dir / "EXPERT_QC_REPORT.md"

    with open(report_path, 'w') as f:
        f.write("# Levtiades Atlas - Expert QC Report\n\n")
        f.write("**Generated for Expert Review (Claude Bajada)**\n\n")
        f.write("## Overview\n\n")
        f.write("This report provides comprehensive quality control analysis for the Levtiades Atlas ")
        f.write("creation pipeline, including registration quality, overlap analysis, and centroid validation.\n\n")

        f.write("## Directory Structure\n\n")
        f.write("```\n")
        f.write("qc_validation/\n")
        f.write("├── registration_qc/     # Registration quality control images\n")
        f.write("├── qc_overlays/         # Overlap analysis and visualizations\n")
        f.write("├── centroid_validation/ # Centroid accuracy analysis\n")
        f.write("└── EXPERT_QC_REPORT.md  # This report\n")
        f.write("```\n\n")

        f.write("## Key Quality Metrics\n\n")
        f.write("### 1. Template-to-Template Registration\n")
        f.write("- **Method**: ANTs SyN registration between MNI template spaces\n")
        f.write("- **Quality Check**: Visual inspection of aligned atlases in `registration_qc/`\n")
        f.write("- **Expected**: Smooth, anatomically plausible transformations\n\n")

        f.write("### 2. Atlas Overlap Analysis\n")
        f.write("- **Hierarchical Priority**: Levinson > Tian > Destrieux\n")
        f.write("- **Overlap Statistics**: Detailed in `qc_overlays/overlap_statistics.csv`\n")
        f.write("- **Expected**: Minimal overlaps, primarily at anatomical boundaries\n\n")

        f.write("### 3. Centroid Validation\n")
        f.write("- **Metric**: Euclidean distance between original and final region centroids\n")
        f.write("- **Threshold**: <2mm acceptable, <1mm excellent\n")
        f.write("- **Analysis**: Statistical summaries in `centroid_validation/`\n\n")

        f.write("## Expert Review Checklist\n\n")
        f.write("- [ ] Registration quality: Check `registration_qc/*.png` for anatomical plausibility\n")
        f.write("- [ ] Overlap patterns: Review `qc_overlays/overlap_analysis.png` for expected boundaries\n")
        f.write("- [ ] Centroid accuracy: Verify `centroid_validation/*_analysis.png` shows <95% regions <2mm\n")
        f.write("- [ ] Template alignment: Confirm proper MNI2009c space alignment\n")
        f.write("- [ ] Hierarchical priority: Verify brainstem nuclei (Levinson) take precedence\n\n")

        f.write("## Recommendations\n\n")
        f.write("1. **Registration Quality**: If registration QC shows distortions, consider:\n")
        f.write("   - Adjusting ANTs registration parameters\n")
        f.write("   - Using alternative template-to-template transforms\n\n")

        f.write("2. **Centroid Validation**: If >5% regions show >2mm error:\n")
        f.write("   - Investigate specific regions with large errors\n")
        f.write("   - Consider region-specific registration refinement\n\n")

        f.write("3. **Overlap Analysis**: Unexpected overlaps may indicate:\n")
        f.write("   - Registration inaccuracies\n")
        f.write("   - Need for atlas boundary refinement\n\n")

        f.write("---\n\n")
        f.write("**Report Generated**: Step 3 Enhanced QC Pipeline\n")
        f.write("**For**: Expert neuroimaging review and validation\n")

    print(f"   ✅ Expert report saved: {report_path}")

if __name__ == "__main__":
    try:
        enhanced_qc_analysis()
    except Exception as e:
        print(f"❌ Error in QC analysis: {e}")
        print("   Ensure Steps 1 and 2 have been completed successfully")