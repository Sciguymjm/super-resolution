# Do composite using modis
import glob
import os
from datetime import datetime

import numpy as np
import xarray

testing = False

width = 4800
height = 4800

hwidth = 12000
hheight = 12000

modis_list = glob.glob(os.path.join("modis", "*MOD09A1_*composite day*.nc"))
modis_ndvi_list = glob.glob(os.path.join("modis", "*MOD09A1_*EVI*.nc"))
himawari_doy = []
# turn himawari dates into day of year
himawari_list = glob.glob(os.path.join("himawari", "*evi.tif.npy"))
for h in himawari_list:
    a = np.load(h)
    himawari_doy.append(
        (datetime.strptime(h.split("\\")[-1].split("/")[-1].split(".")[0], "%Y%m%d%H%M").timetuple().tm_yday, a))
himawari_doy = sorted(himawari_doy, key=lambda x: x[0])
base = himawari_doy[0][0]
himawari_ndvi = np.zeros((12000, 12000, 16))
i = 0
for t in himawari_doy:
    if testing:
        himawari_ndvi[:, :, i] = i
        i += 1
        continue
    if t[1] is None:
        continue
    print t[1].shape
    if t[0] - base >= 16:
        break  # we dont want to go past the 16th day of this cycle
    himawari_ndvi[:, :, t[0] - base] = t[1]
size = 1112
for f in modis_list:
    ds = xarray.open_dataset(f)
    doy = int(f.split("_")[1][5:8])
    top_left = (
        int(float(f.split("_")[5])) / 2,
        int(float(f.split("_")[6].split(".")[0])) / 2)  # TODO: make sure rounding is correct?
    ds -= doy  # normalize the day to 0
    i, j = np.ogrid[top_left[0]:top_left[0] + 4800, top_left[1]: top_left[1] + 4800]
    himawari_composite = himawari_ndvi.clip(min=0)[i, j, ds.day_of_year.clip(min=0).values]
    # himawari_composite[(himawari_composite < 0) | (himawari_composite == 9999)] = np.nan
    # himawari_composite = himawari_ndvi.isel_points(x=np.arange(2400), y=np.arange(2400), t=ds.day_of_year.clip(min=0))
    h_da = xarray.DataArray(himawari_composite, coords=[range(4800), range(4800)], dims=["x", "y"])
    h_ds = xarray.Dataset(dict(ndvi=h_da))
    h_ds.to_netcdf(
        f.split("/")[0] + "/himawari_" + "_".join(f.split("/")[1].split("_")[3:]) + f.split("/")[1].split("_")[
            1] + ".nc")
