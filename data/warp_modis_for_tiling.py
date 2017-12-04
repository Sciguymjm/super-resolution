import glob
import os

import gdal


layers = ["250m 16 days NIR reflectance"]
fs = glob.glob('modis/*273*.hdf')
for f in fs:
    ds = gdal.Open(f, gdal.GA_ReadOnly)
    datasets = ds.GetSubDatasets()
    layer = ""
    for dataset in datasets:
        if layers[0] in dataset[0]:
            layer = dataset[0]
    gdal.Warp(f + '.tile.tif', layer, dstSRS='EPSG:3857', xRes=500, yRes=500)