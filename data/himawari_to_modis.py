# Do composite using modis
import glob
import os
from datetime import datetime

import gdal
from subprocess import Popen
import numpy as np
from osgeo import osr

testing = False

width = 4800 / 2
height = 4800 / 2

hwidth = 12000
hheight = 12000
modis_ndvi_file = glob.glob(os.path.join("modis", "ndvi*.tif"))[0]  # merged file
modis_cdoy_file = glob.glob(os.path.join("modis", "cdoy*.tif"))[0]  # merged file
# modis_list = glob.glob(os.path.join("modis", "*cdoy*MOD13Q1*.tif"))
# modis_ndvi_list = glob.glob(os.path.join("modis", "*ndvi*MOD13Q1*.tif"))
himawari_doy = []
# turn himawari dates into day of year
himawari_list = glob.glob(os.path.join("himawari", "warped-*ndvi.tif"))
for h in himawari_list:
    out = gdal.BuildVRT("out.vrt", [h, modis_ndvi_file, modis_cdoy_file])
    gdal.Translate( "himawari/output-" + h.split("/")[1], out)
    #Popen("gdal_merge.py -init \"-9999\" -separate -of GTiff -o himawari/output-" + h.split("/")[1] + " " + modis_ndvi_file + " " + modis_cdoy_file, shell=True).wait()
for h in himawari_list:
    a = gdal.Open(h)
    himawari_doy.append(
        (datetime.strptime(h.split("\\")[-1].split("/")[-1].split(".")[0].split("-")[1],
                           "%Y%m%d%H%M").timetuple().tm_yday, a))
himawari_doy = sorted(himawari_doy, key=lambda x: x[0])
base = himawari_doy[0][0]
h_shape = himawari_doy[0][1].ReadAsArray().shape
layers = 16
himawari_ndvi = np.zeros((h_shape[0], h_shape[1], 4))
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
    himawari_ndvi[:, :, t[0] - base] = t[1].ReadAsArray()
# open warped modis array
m_ds = gdal.Open(modis_cdoy_file)
shape = m_ds.ReadAsArray().shape  # read shape to form ogrid
i, j = np.ogrid[:shape[0], :shape[1]]
modis_data = m_ds.ReadAsArray().clip(min=0)
himawari_composite = himawari_ndvi[i, j, modis_data]
driver = gdal.GetDriverByName('GTiff')
outRaster = driver.Create("composite-" + modis_ndvi_file, shape[0], shape[1], 1, gdal.GDT_Int16)
outRaster.SetGeoTransform(m_ds.GetGeoTransform())
outband = outRaster.GetRasterBand(1)
outband.SetNoDataValue(-9999)
outband.WriteArray(himawari_composite)
outRasterSRS = osr.SpatialReference()
outRasterSRS.ImportFromEPSG(3857)
outRaster.SetProjection(outRasterSRS.ExportToWkt())
outband.FlushCache()
