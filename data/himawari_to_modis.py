# Do composite using modis
import glob
import os
from datetime import datetime

import gdal
import numpy as np
from osgeo import osr

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-sl", help="Stack layers", action="store_true")
parser.add_argument("-t", help="Test - do not load data, only use placeholders", action="store_true")
args = parser.parse_args()
stack_layers = args.sl
testing = args.t

modis_ndvi_file = glob.glob(os.path.join("modis", "ndvi*.tif"))[0]  # merged file
modis_cdoy_file = glob.glob(os.path.join("modis", "cdoy*.tif"))[0]  # merged file
himawari_doy = []
if stack_layers:
    himawari_list = glob.glob(os.path.join("himawari", "warped-*ndvi.tif"))
    for h in himawari_list:
        options = gdal.BuildVRTOptions(separate=True)
        out = gdal.BuildVRT("out.vrt", [h, modis_ndvi_file, modis_cdoy_file], options=options)
        gdal.Translate("himawari/output-" + h.split("/")[1], out)
# turn himawari dates into day of year
merged_list = glob.glob(os.path.join("himawari", "output-*.tif"))
for h in merged_list:
    a = gdal.Open(h)
    himawari_doy.append(
        (datetime.strptime(h.split("\\")[-1].split("/")[-1].split(".")[0].split("-")[2],
                           "%Y%m%d%H%M").timetuple().tm_yday, a))
modis_ndvi = himawari_doy[0][1].GetRasterBand(2).ReadAsArray()  # bands: himawari, modis, modis_doy
modis_doy = himawari_doy[0][1].GetRasterBand(3).ReadAsArray()
himawari_doy = sorted(himawari_doy, key=lambda x: x[0])
base = himawari_doy[0][0]
h_shape = himawari_doy[0][1].GetRasterBand(1).ReadAsArray().shape
layers = 16
himawari_ndvi = np.zeros((h_shape[0], h_shape[1], layers))
i = 0
for t in himawari_doy:
    if testing:
        himawari_ndvi[:, :, i] = i
        i += 1
        continue
    if t[1] is None:
        continue
    if t[0] - base >= layers:
        break  # we dont want to go past the 16th day of this cycle
    himawari_ndvi[:, :, t[0] - base] = t[1].GetRasterBand(1).ReadAsArray()
# open warped modis array
shape = modis_doy.shape  # read shape to form ogrid
i, j = np.ogrid[:shape[0], :shape[1]]
modis_doy = modis_doy.clip(min=0) # TODO: mask himawari properly
himawari_composite = himawari_ndvi[i, j, modis_doy]
driver = gdal.GetDriverByName('GTiff')
outRaster = driver.Create("composite-" + modis_ndvi_file, shape[0], shape[1], 1, gdal.GDT_Int16)
outRaster.SetGeoTransform(himawari_doy[0][1].GetRasterBand(2).GetGeoTransform())
outband = outRaster.GetRasterBand(1)
outband.SetNoDataValue(-9999)
outband.WriteArray(himawari_composite)
outRasterSRS = osr.SpatialReference()
outRasterSRS.ImportFromEPSG(3857)
outRaster.SetProjection(outRasterSRS.ExportToWkt())
outband.FlushCache()
