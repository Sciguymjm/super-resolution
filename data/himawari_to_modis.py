# Do composite using modis
import glob
import os
from datetime import datetime

import gdal
import numpy as np
import xarray

width = 2400
height = 2400

modis_list = glob.glob(os.path.join("modis", "*MOD09A1_*composite day*.nc"))
modis_ndvi_list = glob.glob(os.path.join("modis", "*MOD09A1_*NDVI*.nc"))
himawari_doy = []
# turn himawari dates into day of year
himawari_list = glob.glob(os.path.join("himawari", "*ndvi.tif"))
for h in himawari_list:
    dataset = gdal.Open(h, gdal.GA_ReadOnly)
    a = dataset.GetRasterBand(1).ReadAsArray()
    himawari_doy.append((datetime.strptime(h.split("\\")[-1].split(".")[0], "%Y%m%d%H%M").timetuple().tm_yday, a))
himawari_ndvi = np.zeros((width, height))
print modis_list
for f in modis_list:
    ds = xarray.open_dataset(f)
