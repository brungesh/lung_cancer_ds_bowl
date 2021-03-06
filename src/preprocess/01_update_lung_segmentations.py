# update lung segmentations from the specified
import os
import numpy as np
from time import time
from utils import lung_segmentation, plotting
import matplotlib.pyplot as plt


wp = os.environ['LUNG_PATH']
INPUT_PATH = '/mnt/hd2/preprocessed5'  # INPUT_PATH = wp + 'data/preprocessed5_sample'  '/mnt/hd2/preprocessed5'
OUTPUT_PATH = '/mnt/hd2/preprocessed5_ls'
filenames = os.listdir(INPUT_PATH)

filenames = [
'dsb_ebd601d40a18634b100c92e7db39f585.npz',
'dsb_08528b8817429d12b7ce2bf444d264f9.npz',
'dsb_d8a0ebe575539c2357c2365cdf0229a0.npz',
'dsb_043ed6cb6054cc13804a3dca342fa4d0.npz',
'dsb_4b2f615f5498ee9d935b0229a2e6bb19.npz',
# z:
'dsb_8c63c8ebd684911de92509a8a703d567.npz',
'dsb_380eb569a5750648434cc8ae8da4a0a9.npz',
'dsb_b8bb02d229361a623a4dc57aa0e5c485.npz',
'dsb_5f4e23c0f76cd00aaaa6e03744bbc362.npz',
'dsb_7367ede966b44c6dce30b83345785671.npz',
'dsb_c713ec80637677965806579fce0b7dca.npz'
]







## MULTIPROCESSING -------------------------------------------------------------------------------------------

import multiprocessing


def calc_segmentation(filename):
    print "Computing %s" % filename
    p = np.load(os.path.join(INPUT_PATH, filename))['arr_0']
    p[1] = lung_segmentation.segment_lungs(p[0],fill_lung=True,method='thresholding2')
    np.savez_compressed(os.path.join(OUTPUT_PATH, filename), p)

pool = multiprocessing.Pool(4)
tstart = time()
pool.map(calc_segmentation, filenames)
print time() - tstart



## SINGLE THREAD -------------------------------------------------------------------------------------------


# for idx, filename in enumerate(filenames):
#     tstart00 = time()
#
#     print "Patient %s (%d/%d)" % (filename, idx, len(filenames))
#
#     tstart = time()
#     p = np.load(os.path.join(INPUT_PATH, filename))['arr_0']
#     # print "Loading time:", time() - tstart
#
#     tstart = time()
#     new_lung = lung_segmentation.segment_lungs(p[0],fill_lung=True,method='thresholding2')
#     p[1] = new_lung
#     # print "Segmenting time:", time() - tstart
#
#     tstart = time()
#     np.savez_compressed(os.path.join(OUTPUT_PATH, filename), p)
#     # print "Storing time:", time() - tstart
#
#     print "Total time:", time() - tstart00

# p1 = np.load(os.path.join(INPUT_PATH, filename))['arr_0']
# p2 = np.load(os.path.join(OUTPUT_PATH, filename))['arr_0']
#
#
# plt.imshow(p1[1,70])
# plt.show()
# plt.imshow(p2[1,70])
# plt.show()

