import os
import re
from os import listdir
from os.path import isfile, join

import numpy as np
import xarray as xr
from pyhdf.SD import SD, SDC
# MCD43B3, MOD09A1
from pyhdf.error import HDF4Error

raw_dir = "modis"
netcdf_dir = "modis"

layers = ["250m 16 days EVI", "250m 16 days NDVI", "250m 16 days NIR reflectance",
          "250m 16 days composite day of the year"]
raw_files = [join(raw_dir, fpath) for fpath in listdir(raw_dir) if
             isfile(join(raw_dir, fpath)) and fpath.endswith(".hdf")]
for fpath in raw_files:
    n = fpath.split(".")[2]
    h = int(n[1:3])
    v = int(n[4:6])
    ncol, nrow = 2400, 2400
    data = []
    hdfFile = SD(fpath, SDC.READ)  # read hdf file to var

    # do size calculations
    str = hdfFile.attributes()['StructMetadata.0']
    ulx, uly = [float(i) / 1000.0 for i in re.findall(r"UpperLeftPointMtrs=\(([0-9\.]+)\,([0-9\.]+)\)", str)[0]]
    lrx, lry = [float(i) / 1000.0 for i in re.findall(r"LowerRightMtrs=\(([0-9\.]+)\,([0-9.]+)\)", str)[0]]
    xstep = (lrx - ulx) / nrow
    ystep = (uly - lry) / ncol
    xs = lrx + np.arange(0, 4800) * xstep
    ys = lry + np.arange(0, 4800) * ystep
    for layer in layers:
        sds = hdfFile.select(layer)  # select dataset from hdf file
        try:
            scale_factor, scale_factor_err, add_offset, add_offset_err, calibrated_nt = sds.getcal()
        except HDF4Error:
            print "error getting scale factor, setting to 1"
            scale_factor = 1

        tp = sds[:] * scale_factor  # scale factor
        dr = xr.DataArray(tp, coords=[xs, ys], dims=["x", "y"])
        ds = xr.Dataset(dict(sur_refl_b02=dr))
        ds.to_netcdf(os.path.join(netcdf_dir, "MOD09A1_%s_%i_%i.nc" % (layer, h, v)))
        print "Processed", layer, v, h
