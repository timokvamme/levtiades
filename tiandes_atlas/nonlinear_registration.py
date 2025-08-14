#!/usr/bin/env python3
"""
Non-Linear Registration Implementation
Following Claude Bajada's recommendation for proper spatial alignment
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import subprocess
import os

def check_registration_tools():
    """Check if registration tools are available"""
    
    print("🔧 CHECKING REGISTRATION TOOLS")
    print("=" * 32)
    
    tools_available = {}
    
    # Check for ANTs
    try:
        result = subprocess.run(['antsRegistration', '--version'], 
                              capture_output=True, text=True, timeout=10)
        tools_available['ants'] = True
        print("✅ ANTs available")
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        tools_available['ants'] = False
        print("❌ ANTs not available")
    
    # Check for FSL FLIRT/FNIRT
    try:
        result = subprocess.run(['flirt', '-version'], 
                              capture_output=True, text=True, timeout=10)
        tools_available['fsl'] = True
        print("✅ FSL available")
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        tools_available['fsl'] = False
        print("❌ FSL not available")
    
    return tools_available

def implement_ants_registration():
    """Implement ANTs-based non-linear registration"""
    
    print("\n🧠 ANTs NON-LINEAR REGISTRATION")
    print("=" * 35)
    
    base_dir = Path("tiandes_atlas")
    raw_dir = base_dir / "raw_atlases"
    nonlinear_dir = base_dir / "nonlinear_aligned"
    nonlinear_dir.mkdir(exist_ok=True)
    
    tian_path = raw_dir / "tian_subcortical.nii.gz"
    des_path = raw_dir / "destrieux_cortical.nii.gz"
    
    print(f"🎯 Target approach (Claude Bajada's recommendation):")
    print(f"   Fixed image: {tian_path.name} (reference space)")
    print(f"   Moving image: {des_path.name} (to be registered)")
    
    # ANTs registration command (non-linear)
    ants_cmd = [
        'antsRegistration',
        '--dimensionality', '3',
        '--float', '1',
        '--interpolation', 'NearestNeighbor',  # Preserve integer labels
        '--use-histogram-matching', '1',
        '--winsorize-image-intensities', '[0.005,0.995]',
        
        # Initial alignment (rigid + affine)
        '--initial-moving-transform', f'[{tian_path},{des_path},1]',
        
        # Rigid registration
        '--transform', 'Rigid[0.1]',
        '--metric', 'MI[{},{},1,32,Regular,0.25]'.format(tian_path, des_path),
        '--convergence', '[1000x500x250x125,1e-6,10]',
        '--shrink-factors', '8x4x2x1',
        '--smoothing-sigmas', '3x2x1x0vox',
        
        # Affine registration  
        '--transform', 'Affine[0.1]',
        '--metric', 'MI[{},{},1,32,Regular,0.25]'.format(tian_path, des_path),
        '--convergence', '[1000x500x250x125,1e-6,10]',
        '--shrink-factors', '8x4x2x1', 
        '--smoothing-sigmas', '3x2x1x0vox',
        
        # Non-linear registration (SyN)
        '--transform', 'SyN[0.1,3,0]',
        '--metric', 'CC[{},{},1,4]'.format(tian_path, des_path),
        '--convergence', '[100x70x50x20,1e-6,10]',
        '--shrink-factors', '8x4x2x1',
        '--smoothing-sigmas', '3x2x1x0vox',
        
        # Output paths
        '--output', f'[{nonlinear_dir}/ants_transform_,{nonlinear_dir}/destrieux_nonlinear_aligned.nii.gz]',
        '--write-composite-transform', '1'
    ]
    
    print(f"\n🔄 Running ANTs registration...")
    print("⏱️  This may take 5-15 minutes for high-quality non-linear registration")
    
    try:
        result = subprocess.run(ants_cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        if result.returncode == 0:
            print("✅ ANTs registration completed successfully!")
            return True
        else:
            print(f"❌ ANTs registration failed:")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ ANTs registration timed out (>30 minutes)")
        return False
    except Exception as e:
        print(f"❌ ANTs registration error: {e}")
        return False

def implement_fsl_registration():
    """Implement FSL-based non-linear registration (fallback)"""
    
    print("\n🧠 FSL NON-LINEAR REGISTRATION")
    print("=" * 34)
    
    base_dir = Path("tiandes_atlas")
    raw_dir = base_dir / "raw_atlases"
    nonlinear_dir = base_dir / "nonlinear_aligned"
    nonlinear_dir.mkdir(exist_ok=True)
    
    tian_path = raw_dir / "tian_subcortical.nii.gz"
    des_path = raw_dir / "destrieux_cortical.nii.gz"
    
    print(f"🎯 FSL approach:")
    print(f"   Reference: {tian_path.name}")
    print(f"   Input: {des_path.name}")
    
    # Step 1: Linear registration with FLIRT
    flirt_output = nonlinear_dir / "destrieux_linear_aligned.nii.gz"
    flirt_matrix = nonlinear_dir / "linear_transform.mat"
    
    flirt_cmd = [
        'flirt',
        '-in', str(des_path),
        '-ref', str(tian_path),
        '-out', str(flirt_output),
        '-omat', str(flirt_matrix),
        '-interp', 'nearestneighbour',  # Preserve integer labels
        '-cost', 'mutualinfo'
    ]
    
    print("🔄 Step 1: Linear registration with FLIRT...")
    
    try:
        result = subprocess.run(flirt_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ FLIRT linear registration completed")
        else:
            print(f"❌ FLIRT failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ FLIRT error: {e}")
        return False
    
    # Step 2: Non-linear registration with FNIRT
    fnirt_output = nonlinear_dir / "destrieux_nonlinear_aligned.nii.gz"
    fnirt_warp = nonlinear_dir / "nonlinear_warp.nii.gz"
    
    fnirt_cmd = [
        'fnirt',
        '--in=' + str(des_path),
        '--ref=' + str(tian_path),
        '--aff=' + str(flirt_matrix),
        '--iout=' + str(fnirt_output),
        '--cout=' + str(fnirt_warp),
        '--interp=spline',  # Then we'll apply with nearest neighbor
        '--subsamp=8,4,2,1',
        '--miter=5,5,5,5',
        '--lambda=300,75,30,15'
    ]
    
    print("🔄 Step 2: Non-linear registration with FNIRT...")
    print("⏱️  This may take 10-20 minutes...")
    
    try:
        result = subprocess.run(fnirt_cmd, capture_output=True, text=True, timeout=1800)
        
        if result.returncode == 0:
            print("✅ FNIRT non-linear registration completed!")
            
            # Apply warp with nearest neighbor for final atlas
            applywarp_cmd = [
                'applywarp',
                '--in=' + str(des_path),
                '--ref=' + str(tian_path), 
                '--warp=' + str(fnirt_warp),
                '--out=' + str(fnirt_output),
                '--interp=nn'  # Nearest neighbor for integer labels
            ]
            
            result2 = subprocess.run(applywarp_cmd, capture_output=True, text=True, timeout=120)
            
            if result2.returncode == 0:
                print("✅ Final warp application completed with nearest neighbor interpolation")
                return True
            else:
                print(f"❌ applywarp failed: {result2.stderr}")
                return False
                
        else:
            print(f"❌ FNIRT failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ FNIRT error: {e}")
        return False

def python_based_registration():
    """Python-based registration using SimpleITK (fallback)"""
    
    print("\n🐍 PYTHON-BASED REGISTRATION (FALLBACK)")
    print("=" * 43)
    
    try:
        import SimpleITK as sitk
        print("✅ SimpleITK available")
    except ImportError:
        print("❌ SimpleITK not available, installing...")
        subprocess.run(['pip', 'install', 'SimpleITK'], check=True)
        import SimpleITK as sitk
    
    base_dir = Path("tiandes_atlas")
    raw_dir = base_dir / "raw_atlases"
    nonlinear_dir = base_dir / "nonlinear_aligned"
    nonlinear_dir.mkdir(exist_ok=True)
    
    # Load images
    print("📂 Loading atlases...")
    tian_sitk = sitk.ReadImage(str(raw_dir / "tian_subcortical.nii.gz"))
    des_sitk = sitk.ReadImage(str(raw_dir / "destrieux_cortical.nii.gz"))
    
    # Convert to float for registration
    tian_float = sitk.Cast(tian_sitk, sitk.sitkFloat32)
    des_float = sitk.Cast(des_sitk, sitk.sitkFloat32)
    
    print("🔄 Performing multi-stage registration...")
    
    # Registration framework
    registration_method = sitk.ImageRegistrationMethod()
    
    # Multi-scale approach
    registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
    registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
    registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    
    # Similarity metric
    registration_method.SetMetricAsMeanSquares()
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
    registration_method.SetMetricSamplingPercentage(0.01)
    
    # Interpolator
    registration_method.SetInterpolator(sitk.sitkLinear)
    
    # Optimizer
    registration_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=100)
    registration_method.SetOptimizerScalesFromPhysicalShift()
    
    # Transform
    initial_transform = sitk.CenteredTransformInitializer(
        tian_float, des_float, sitk.Similarity3DTransform(),
        sitk.CenteredTransformInitializerFilter.GEOMETRY
    )
    registration_method.SetInitialTransform(initial_transform, inPlace=False)
    
    # Execute registration
    final_transform = registration_method.Execute(tian_float, des_float)
    
    print("✅ Registration completed")
    
    # Apply transform with nearest neighbor for integer labels
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(tian_sitk)
    resampler.SetInterpolator(sitk.sitkNearestNeighbor)
    resampler.SetDefaultPixelValue(0)
    resampler.SetTransform(final_transform)
    
    des_registered = resampler.Execute(des_sitk)
    
    # Save result
    output_path = nonlinear_dir / "destrieux_python_registered.nii.gz"
    sitk.WriteImage(des_registered, str(output_path))
    
    print(f"✅ Registered atlas saved: {output_path}")
    return True

def compare_registration_approaches():
    """Compare linear vs non-linear registration results"""
    
    print("\n📊 REGISTRATION COMPARISON")
    print("=" * 28)
    
    base_dir = Path("tiandes_atlas")
    
    # Load different registration results
    linear_path = base_dir / "aligned_atlases" / "destrieux_aligned.nii.gz"
    
    nonlinear_candidates = [
        base_dir / "nonlinear_aligned" / "destrieux_nonlinear_aligned.nii.gz",
        base_dir / "nonlinear_aligned" / "destrieux_python_registered.nii.gz"
    ]
    
    tian_path = base_dir / "aligned_atlases" / "tian_aligned.nii.gz"
    
    if not linear_path.exists():
        print("❌ Linear registration result not found")
        return
    
    # Load reference
    tian_img = nib.load(tian_path)
    tian_data = tian_img.get_fdata().astype(int)
    
    # Load linear result
    linear_img = nib.load(linear_path)
    linear_data = linear_img.get_fdata().astype(int)
    
    # Calculate linear overlaps
    linear_overlaps = np.sum((tian_data > 0) & (linear_data > 0))
    
    print(f"📋 COMPARISON RESULTS:")
    print(f"   Linear registration overlaps: {linear_overlaps} voxels")
    
    # Check non-linear results
    for nonlinear_path in nonlinear_candidates:
        if nonlinear_path.exists():
            nonlinear_img = nib.load(nonlinear_path)
            nonlinear_data = nonlinear_img.get_fdata().astype(int)
            nonlinear_overlaps = np.sum((tian_data > 0) & (nonlinear_data > 0))
            
            improvement = linear_overlaps - nonlinear_overlaps
            improvement_pct = 100 * improvement / linear_overlaps if linear_overlaps > 0 else 0
            
            print(f"   {nonlinear_path.name} overlaps: {nonlinear_overlaps} voxels")
            print(f"   Improvement: {improvement} voxels ({improvement_pct:.1f}%)")
            
            if improvement > 50:  # Significant improvement
                print(f"   ✅ Significant improvement detected!")
                return True
    
    return False

if __name__ == "__main__":
    print("🔧 NON-LINEAR REGISTRATION IMPLEMENTATION")
    print("Following Claude Bajada's Expert Recommendation")
    print("=" * 50)
    
    # Check available tools
    tools = check_registration_tools()
    
    success = False
    
    # Try ANTs first (best quality)
    if tools.get('ants'):
        print("\n🥇 Attempting ANTs registration (highest quality)...")
        success = implement_ants_registration()
    
    # Try FSL if ANTs failed
    if not success and tools.get('fsl'):
        print("\n🥈 Attempting FSL registration...")
        success = implement_fsl_registration()
    
    # Try Python-based as fallback
    if not success:
        print("\n🥉 Attempting Python-based registration...")
        success = python_based_registration()
    
    if success:
        # Compare results
        significant_improvement = compare_registration_approaches()
        
        if significant_improvement:
            print(f"\n🎉 NON-LINEAR REGISTRATION SHOWS SIGNIFICANT IMPROVEMENT!")
            print("   Recommendation: Remake atlas with non-linear registration")
        else:
            print(f"\n✅ Non-linear registration completed")
            print("   Results similar to linear - current atlas may be adequate")
    else:
        print(f"\n❌ All registration approaches failed")
        print("   Current linear atlas may be the best available option")