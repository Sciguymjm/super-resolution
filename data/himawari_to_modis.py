# Do composite using modis
import glob
import os
from datetime import datetime

import gdal
import numpy as np
import xarray

width = 2400
height = 2400

hwidth = 12000
hheight = 12000
modis_list = glob.glob(os.path.join("modis", "*MOD09A1_*composite day*.nc"))
modis_ndvi_list = glob.glob(os.path.join("modis", "*MOD09A1_*NDVI*.nc"))
himawari_doy = []
# turn himawari dates into day of year
himawari_list = glob.glob(os.path.join("himawari", "*ndvi.tif"))
for h in himawari_list:
    dataset = gdal.Open(h, gdal.GA_ReadOnly)
    a = dataset.GetRasterBand(1).ReadAsArray()
    himawari_doy.append((datetime.strptime(h.split("\\")[-1].split(".")[0], "%Y%m%d%H%M").timetuple().tm_yday, a))
base = himawari_doy[0][0]
himawari_ndvi = np.zeros((hwidth, hheight, len(himawari_doy)))
for t in himawari_doy:
    himawari_ndvi[:, :, t[0] - base] = t[1]
himawari_ndvi = xarray.DataArray(himawari_ndvi, dims=['x', 'y', 't'])
for f in modis_list:
    ds = xarray.open_dataset(f)
    doy = int(f.split("_")[1][5:8])
    ds -= doy  # normalize the day to 0
    himawari_composite = himawari_ndvi.isel(x=np.arange(2400), y=np.arange(2400), t=ds.day_of_year.clip(min=0))
    h_ds = xarray.Dataset(dict(ndvi=himawari_composite))
    h_ds.to_netcdf("himawari_" + f)
