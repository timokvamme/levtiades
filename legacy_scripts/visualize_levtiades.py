#!/usr/bin/env python3
"""
MRIcrogl Visualization Script for Levtiades Atlas
"""

import gl

def visualize_levtiades():
    """Visualize the Levtiades atlas components"""
    
    gl.resetdefaults()
    
    # Load atlas
    gl.overlayload('levtiades_atlas/final_atlas/no_overlaps/levtiades_hierarchical.nii.gz')
    gl.overlaycolorname(1, 'Spectrum')
    gl.opacity(1, 80)
    
    # Set view
    gl.view(1)  # Sagittal
    gl.clipazimuthelevation(0.5, 0, 120)
    
    print('Levtiades Atlas Loaded!')
    print('Red: Levinson brainstem')
    print('Green: Tian subcortical')
    print('Blue: Destrieux cortical')

if __name__ == "__main__":
    visualize_levtiades()
