
import numpy as np
import os
from src.utils import plotting
from src.utils import reading
from src.utils import preprocessing
import random
from glob import glob
import matplotlib.pyplot as plt
import SimpleITK as sitk

## Loading
# wp = os.environ['LUNG_PATH']
# OUTPUT_FOLDER  = wp + 'data/preproc_luna/*.npz'  # Test DSB
# OUTPUT_FOLDER  = wp + 'data/preproc_dsb/*.npz'  # Test luna
# OUTPUT_FOLDER = '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/preproc_dsb/*.npz'
# OUTPUT_FOLDER = '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/preproc_luna/*.npz'


## carga luna orginal
OF = '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/luna/subset9/*.mhd'
patient_files = glob(OF)
patient = sitk.ReadImage(patient_files[20])
patient = sitk.GetArrayFromImage(patient) #indexes are z,y,x
plt.imshow(patient[40])
plt.show()

x = []
z = []
for p in patient_files:
    patient = sitk.ReadImage(p)
    x.append(patient.GetSpacing()[1])
    z.append(patient.GetSpacing()[2])
    print str(patient.GetSpacing()[0]) + ',' + str(patient.GetSpacing()[1]) + ',' + str(patient.GetSpacing()[2])

plt.hist(x, bins=80)
plt.show()

plt.hist(z, bins=80)
plt.show()

from skimage import draw

img = np.zeros((100, 100), dtype=np.uint8)
rr, cc = draw.circle(50,50,50)
img[rr,cc] = 1

plt.imshow(img)
plt.show()


## carga DSB original
OF = '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/sample_images'
patient_files = os.listdir(OF)
patient = preprocessing.get_pixels_hu(reading.load_scan(os.path.join(OF, patient_files[0])))
plt.imshow(patient[50])
plt.show()

plt.hist(patient[40].flatten(), bins=80)
plt.show()

x = []
z = []
for p in patient_files:
    px = reading.load_scan(os.path.join(OF, p))
    spacing = reading.dicom_get_spacing(px)
    x.append(spacing[1])
    z.append(spacing[0])


plt.hist(x, bins=80)
plt.show()

plt.hist(z, bins=80)
plt.show()


# carga npz
OUTPUT_FOLDER = '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/preproc_dsb/*.npz'
OUTPUT_FOLDER = '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/preproc_luna/*.npz'
proc_file = glob(OUTPUT_FOLDER)  # patients from subset1
p = np.load(proc_file[4])['arr_0']  # abrir archivo
sample = random.choice(proc_file)
p = np.load(sample)['arr_0']  # abrir archivo
p.shape




# 3d sliding plot
plotting.cube_show_slider(p[0])  # image
plotting.cube_show_slider(p[1])  # lung mask
plotting.cube_show_slider(p[2])  # nodule mask (if exists)


# histogram
plt.hist(p[0,100].flatten(), bins=80)
plt.show()

# study nodules mask
for i in range(p[2].shape[0]):
    if np.max(p[2,i])!=0:
        print i

plotting.plot_mask(p[0,58], p[2,58])



## Detect bad segmentation
for p in proc_file:
    p = sample
    print 'Testing %s' % p
    data = np.load(p)['arr_0']  # abrir archivo

    total = 0
    for i in range(data.shape[1]):
        print i
        if np.sum(data[1,i])>0:
            total = 1
            break

    if total==0:
        print p


## Show segmentations
plots = np.zeros((len(proc_file),800,800))
for i,p in enumerate(proc_file):
    print i
    data = np.load(p)['arr_0']  # abrir archivo
    nslice = data.shape[1]/2
    plots[i] = data[1,nslice]
print 'Fin!'
plotting.multiplot(plots)
plt.imshow(plots[13])
plt.show()

x = []
np.array(proc_file)[[2,3,5,10,13,18,19,20]]


x = [ '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/preproc_luna/luna_109002525524522225658609808059.npz',
       '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/preproc_luna/luna_111172165674661221381920536987.npz',
       '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/preproc_luna/luna_124154461048929153767743874565.npz',
       '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/preproc_luna/luna_130438550890816550994739120843.npz',
       '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/preproc_luna/luna_138080888843357047811238713686.npz',
       '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/preproc_luna/luna_146429221666426688999739595820.npz',
       '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/preproc_luna/luna_154677396354641150280013275227.npz',
       '/Users/mingot/Projectes/kaggle/ds_bowl_lung/data/preproc_luna/luna_187451715205085403623595258748.npz']

for n in x:
    id = n.split('_')[-1].replace('.npz','')
    print '1.3.6.1.4.1.14519.5.2.1.6279.6001.' + id + '.mhd'
