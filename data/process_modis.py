import datetime as dt
import os
from os import listdir
from os.path import isfile, join

import numpy as np
import xarray as xr
from pyhdf.SD import SD, SDC
# MCD43B3, MOD09A1
# process bounding coordinates from txt file
name = "sn_bound_10deg.txt"
bounds = []
with open(name, "r") as fpath:
    lines = fpath.read().split("\r")
    for l in lines:
        if "0" in l and "n" not in l:
            arr = []
            for num in l.split("  ")[1:]:
                if num is not "":
                    arr.append(float(num))
            bounds.append(arr)

raw_dir = "modis"
netcdf_dir = "modis"
raw_files = [join(raw_dir, fpath) for fpath in listdir(raw_dir) if isfile(join(raw_dir, fpath)) and fpath.endswith(".hdf")]
for fpath in raw_files:
    # Bounds: http://modis-land.gsfc.nasa.gov/pdf/sn_bound_10deg.txt
    n = fpath.split(".")[2]
    h = int(n[1:3])
    v = int(n[4:6])
    bound = [b for b in bounds if b[0] == v and b[1] == h][0]
    latmin, latmax = bound[4], bound[5]
    lonmin, lonmax = bound[2], bound[3]
    ncol, nrow = 1200, 1200
    data = []
    dates = []
    latstep = 1. * (latmax - latmin) / nrow
    lonstep = 1. * (lonmax - lonmin) / ncol
    lats = latstep * np.arange(nrow) + latmin
    lons = lonstep * np.arange(ncol) + lonmin

    year = int(fpath.split('.')[1][1:5])
    dayofyear = int(fpath.split('.')[1][5:8])
    date = dt.datetime(year, 1, 1) + dt.timedelta(days=dayofyear - 1)
    # if False:# prev_year != year:
    #     tp_data = np.concatenate(daytemps, axis=2)
    #     tp_data[tp_data == 0] = np.nan
    #     dr = xr.DataArray(tp_data, coords=[lats, lons, dates], dims=['lat', 'lon', 'time'])
    #     ds = xr.Dataset(dict(LST_Day_1km=dr))
    #     ds.to_netcdf(os.path.join(netcdf_dir, "MCD43B3_%i.nc" % prev_year))
    #     daytemps = []
    #     dates = []

    hdf = SD(fpath, SDC.READ)
    print hdf.datasets()
    tp = hdf.select("sur_refl_b02")[:] * 0.02  # scale factor
    data += [tp[:, :, np.newaxis]]
    data[data == 0] = np.nan
    dr = xr.DataArray(data, coords={'lat': lats,'lon': lons})
    ds = xr.Dataset(dict(sur_refl_b02=dr))
    ds.to_netcdf(os.path.join(netcdf_dir, "MOD09A1_%i_%i.nc" % (h, v)))
