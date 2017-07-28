# Do composite using modis
import glob
import os
from datetime import datetime

import gdal
import numpy as np
from osgeo import gdal as osgd
from osgeo import osr

testing = False

width = 4800 / 2
height = 4800 / 2

hwidth = 12000
hheight = 12000

modis_list = glob.glob(os.path.join("modis", "*cdoy*MOD13Q1*.tif"))
modis_ndvi_list = glob.glob(os.path.join("modis", "*ndvi*MOD13Q1*.tif"))
himawari_doy = []
# turn himawari dates into day of year
himawari_list = glob.glob(os.path.join("himawari", "warped-*ndvi.tif"))
for h in himawari_list:
    a = gdal.Open(h)
    himawari_doy.append(
        (datetime.strptime(h.split("\\")[-1].split("/")[-1].split(".")[0].split("-")[1],
                           "%Y%m%d%H%M").timetuple().tm_yday, a))
himawari_doy = sorted(himawari_doy, key=lambda x: x[0])
base = himawari_doy[0][0]
# himawari_ndvi = np.ndarray(shape=himawari_doy[0][1].ReadAsArray().shape + (16,))
for f in modis_list:
    m_ds = gdal.Open(f)  # open warped modis array
    shape = m_ds.ReadAsArray().shape  # read shape to form ogrid
    modis_data = m_ds.ReadAsArray().clip(min=0)
    ulx, xres, xskew, uly, yskew, yres = m_ds.GetGeoTransform()  # calculate top left and bottom right
    lrx = ulx + (m_ds.RasterXSize * xres)
    lry = uly + (m_ds.RasterYSize * yres)
    h_cutout = np.zeros((shape[0], shape[1], 16))  # this is for all of the himawari cutouts
    for i, h in enumerate(himawari_doy):
        gdal.Warp("temp.tif", h[1], options=osgd.WarpOptions(outputBounds=(ulx, lry, lrx, uly)))  # warp to file
        # read file to array, since im not sure how the 'destarray' function works in Warp
        h_cutout[:, :, i] = gdal.Open("temp.tif").ReadAsArray().astype(dtype="int")
    i, j = np.ogrid[:shape[1], :shape[0]]
    himawari_composite = h_cutout[i, j, modis_data]
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create("composite-" + f, shape[0], shape[1], 1, gdal.GDT_Int16)
    outRaster.SetGeoTransform(m_ds.GetGeoTransform())
    outband = outRaster.GetRasterBand(1)
    outband.SetNoDataValue(-9999)
    outband.WriteArray(himawari_composite)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(3857)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()
