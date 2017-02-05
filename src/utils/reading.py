import numpy as np
import pandas as pd
import dicom
import os
import scipy.ndimage
import matplotlib.pyplot as plt
import SimpleITK as sitk

from skimage import measure, morphology
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def list_final_subfolders(path, maxDepth = 10):
    """
    recursively list all subfolders that do not have.
    WARNING: not cyclic folders, please!
    """
    if maxDepth == 0:
        raise Exception('Error reading %s, reached maximal recursion level')
    
    files = [os.path.join(path,o) for o in os.listdir(path) if os.path.isdir(os.path.join(path,o))]
    if files:
        return reduce(operator.__add__, ( list_final_subfolders(f, maxDepth - 1) for f in files), [])
    else:
        return [ path ]
    
    

def read_patient_lidc(path):
    """
    @param path: path of the patients DCOMS

    Reads a patient that has potentially more than one DICOM study (not always CT).
    Gives warning and discards one,  if two CT explorations are found.
    Some patient have only radiography, so they are discarded as well.
    """
    
    #1st, obtain all the folders.
    possiblePatientsFolders = list_final_subfolders(path)
    patient_ct_explorations = []
    for p in possiblePatientsFolders:
        dcms = load_scan(p)
        if dcms:
            patient_ct_explorations.append(dcms)
                   
    #Check if there is more than one dcms, 
    if not patient_ct_explorations:
        raise Exception('No CT exploration found - (normal in LIDC)')
    elif len(patient_ct_explorations) > 1:
        print ' Warning: more than one CT exploration found. Discarding all but the first one.'
        
    patient_data = patient_ct_explorations[0]
    return patient_data

def load_scan(patient_path):
    """Given a patient path, returns an array of scans from the DICOM files. Check that the files are dicoms, and the modality is CT"""
    slices = filter(lambda s: s.endswith('.dcm'), os.listdir(patient_path))
    slices = [dicom.read_file(os.path.join(patient_path,s)) for s in slices]
    
    #Check that the modality is CT
    if not slices or slices[0].Modality != 'CT':
        return []
    slices.sort(key = lambda x: int(x.InstanceNumber))
    try:
        slice_thickness = np.abs(slices[0].ImagePositionPatient[2] - slices[1].ImagePositionPatient[2])
    except:
        slice_thickness = np.abs(slices[0].SliceLocation - slices[1].SliceLocation)
        
    for s in slices:
        s.SliceThickness = slice_thickness
        
    return slices

    
def scan2imgs(scans):
    """Convert scans to array of pixel images."""
    imgs = np.stack([s.pixel_array for s in scans])
    imgs = imgs.astype(np.int16)
    imgs = np.array(imgs, dtype=np.int16)
    return imgs


def get_pixels_hu(slices):
    """Given an array of slices from the DICOM, returns and array of images, correcting pixel values."""
    image = np.stack([s.pixel_array for s in slices])
    # Convert to int16 (from sometimes int16), 
    # should be possible as values should always be low enough (<32k)
    image = image.astype(np.int16)

    # Set outside-of-scan pixels to 0
    # The intercept is usually -1024, so air is approximately 0
    image[image == -2000] = 0
    
    # Convert to Hounsfield units (HU)
    intercept = slices[0].RescaleIntercept
    slope = slices[0].RescaleSlope
    
    if slope != 1:
        image = slope * image.astype(np.float64)
        image = image.astype(np.int16)
        
    image += np.int16(intercept)
    
    return np.array(image, dtype=np.int16)
    
    
def resample(image, scan, new_spacing=[1,1,1]):
    # Determine current pixel spacing
    spacing = map(float, ([scan[0].SliceThickness] + scan[0].PixelSpacing))
    spacing = np.array(list(spacing))

    resize_factor = spacing / new_spacing
    new_real_shape = image.shape * resize_factor
    new_shape = np.round(new_real_shape)
    real_resize_factor = new_shape / image.shape
    new_spacing = spacing / real_resize_factor
    
    image = scipy.ndimage.interpolation.zoom(image, real_resize_factor)
    
    return image, new_spacing
    

def load_slices_from_mhd(img_file):
    itk_img = sitk.ReadImage(img_file)
    img_array = sitk.GetArrayFromImage(itk_img) #indexes are z,y,x
    return img_array
    


