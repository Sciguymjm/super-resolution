# Do composite using modis
import glob
import os
from datetime import datetime

import gdal
import numpy as np
import xarray

testing = False

width = 4800
height = 4800

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
	himawari_doy.append((datetime.strptime(h.split("\\")[-1].split("/")[-1].split(".")[0], "%Y%m%d%H%M").timetuple().tm_yday, a))
base = himawari_doy[0][0]
himawari_ndvi = np.zeros((width, height, 16))
i = 0
for t in himawari_doy:
	if testing:
		himawari_ndvi[:, :, i] = i
		i+=1
		continue
	if t[1] is None:
		continue
	himawari_ndvi[:, :, t[0] - base] = t[1][:width, :height]
	print t[1][0, 0]

for f in modis_list:
	ds = xarray.open_dataset(f)
	doy = int(f.split("_")[1][5:8])
	ds -= doy  # normalize the day to 0
	himawari_composite = np.zeros((width, height, 1))
	himawari_composite = himawari_ndvi[range(4800), range(4800), ds.day_of_year.clip(min=0).values]
	print ds.day_of_year.clip(min=0).values
	himawari_composite[(himawari_composite == -9999) | (himawari_composite == 9999)] = np.nan 
	# himawari_composite = himawari_ndvi.isel_points(x=np.arange(2400), y=np.arange(2400), t=ds.day_of_year.clip(min=0))
	h_da = xarray.DataArray(himawari_composite, coords=[range(4800), range(4800)], dims=["x", "y"])
	h_ds = xarray.Dataset(dict(ndvi=h_da))
	h_ds.to_netcdf(f.split("/")[0] + "/himawari_" + "_".join(f.split("/")[1].split("_")[3:]) + f.split("/")[1].split("_")[1] +".nc")
