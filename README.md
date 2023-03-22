# Ultrasound_L3D_to_mrb
Ultrasound: conversion from l3d file to mrb 3D Slicer file
This converts all .l3d files in a folder 

## Requirements:

- Python 2.7
- [3D Slicer 5.02](https://www.slicer.org/) or above 

## Steps:

1.	Download:   
  -	UMICH_l3d_to_mhd_raw.py
  -	Slicer_US_translation_with_loop.txt
  
2.	Run .py file: change line 173 to the appropriate file location (it can take several minutes per file for it to convert)

4.	Open 3D Slicer, copy code from Slicer_US_translation_with_loop.txt to 3D Slicer python interface (it can take several minutes per file for it to convert)

5.	In 3D Slicer: the ultrasound views are not aligned with the MRI standard. To do that, transform the file in the Transforms (See Tutorial transform US planes into the native MRI planes.pdf):
  -	Create linear transform
  -	Change:
    - LR to 90
    - PA to 90
  - Harden transform

