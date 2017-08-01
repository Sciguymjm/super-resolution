import argparse
import glob
import os
import xarray as xr
import gdal
import numpy as np
import osr
# vis.01 - blue
# vis.02 - green
# vis.03 - nir
# ext.01 - red
parser = argparse.ArgumentParser()
parser.add_argument('inDir', help='Input Directory')
parser.add_argument('outDir', help='Output directory')
args = parser.parse_args()

inDir = args.inDir
outDir = args.outDir

pixelWidth = 0.01
pixelHeight = 0.01
visRows = 12000 * 2
visCols = 12000 * 2
extRows = 24000 * 2
extCols = 24000 * 2
# https://eospso.gsfc.nasa.gov/sites/default/files/atbd/atbd_mod13.pdf p33
modis_L = 1.0
modis_C1 = 6.0
modis_C2 = 7.5
modis_G = 2.5


# Writing to TIFF will actually improve the processing speed later on, so I'm leaving it in

def array2raster(newRasterfn, pixelWidth, pixelHeight, array):
    # xr.Dataset(dict(arr=xr.DataArray(array))).to_netcdf(newRasterfn + ".nc")
    # np.save(newRasterfn + ".npy", array)
    # return
    cols = array.shape[1]
    rows = array.shape[0]
    originX = 85 # starting longitude
    originY = -60 # starting latitude
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Int16)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.SetNoDataValue(-9999)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(4326)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


flist = glob.glob(os.path.join(inDir, '*vis.01.fld.geoss.dat'))
ndviArrayMVC = np.zeros((visRows, visCols, len(flist) / 4), dtype=np.int16)
for raster in flist:
    print raster
    if len(glob.glob(os.path.join(inDir, os.path.basename(raster)[:12] + '*.dat'))) < 4:
        continue
    if len(glob.glob(os.path.join(outDir, os.path.basename(raster)[:12] + '*.tif'))) > 2:
        continue  # we already processed this one. save us some time
    utcHour = int(os.path.basename(raster)[8:10])
    print raster, utcHour
    red = raster.replace('vis', 'ext')
    nir = raster.replace('.01.', '.03.')
    ndvi_path = os.path.join(outDir, os.path.basename(raster)[:12] + '.ndvi.tif')
    nir_path = os.path.join(outDir, os.path.basename(raster)[:12] + '.nir.tif')
    evi_path = os.path.join(outDir, os.path.basename(raster)[:12] + '.evi.tif')
    # ndviMVC = os.path.join(os.path.basename(raster)[:8] + '.ndvi.utc-0-6.MVC.tif')
    nirArray = np.fromfile(nir, dtype='f4').reshape(visRows, visCols)
    nirArray[nirArray < 0] = 0.00001
    # nirArray = nirArray[0000:10000, 0000:7000]
    # redArray_aggr = redArray_aggr[0000:10000, 0000:7000]

    array2raster(nir_path, pixelWidth, pixelHeight, nirArray)  # process nir

    # now process redArray to minimize the memory and disk usage
    redArray = np.fromfile(red, dtype='f4').reshape(extRows, extCols)
    redArray_aggr = redArray.reshape(visRows, 2, visCols, 2).mean(axis=(1, 3))
    redArray_aggr[redArray_aggr < 0] = 0.00001

    ndviArray = (nirArray - redArray_aggr) / (nirArray + redArray_aggr)
    ndviArray = np.nan_to_num(ndviArray)
    ndviArray = np.where(np.logical_and(ndviArray < 1, ndviArray > 0), ndviArray, -0.9999)
    ndviArray = ndviArray * 10000
    ndviArray = ndviArray.astype('i2')
    ndviArray = ndviArray[::-1]  # reverse array so the tif looks like the array
    array2raster(ndvi_path, pixelWidth, pixelHeight, ndviArray)

    del ndviArray  # delete ndvi array to save memory

    # load blue array
    blueArray = np.fromfile(raster, dtype='f4').reshape(visRows, visCols)
    blueArray[blueArray < 0] = 0.00001
    # compute EVI = G * (NIR - RED) / (NIR + C1 * RED - C2 * BLUE + L)
    # https://en.wikipedia.org/wiki/Enhanced_vegetation_index
    # https://eospso.gsfc.nasa.gov/sites/default/files/atbd/atbd_mod13.pdf p120 F12
    eviArray = modis_G * (nirArray - redArray_aggr) / (
        nirArray + modis_C1 * redArray_aggr - modis_C2 * blueArray + modis_L)
    eviArray = np.nan_to_num(eviArray)
    eviArray = np.where(np.logical_and(eviArray < 1, eviArray > 0), eviArray, -0.9999)
    eviArray = eviArray * 10000
    eviArray = eviArray.astype('i2')
    eviArray = eviArray[::-1]  # reverse array so the tif looks like the array

    # if utcHour < 6:
    #     ndviArrayMVC = np.maximum(ndviArray, ndviArrayMVC)
    array2raster(evi_path, pixelWidth, pixelHeight, eviArray)
    # uncomment for MVC file
    # array2raster(ndviMVC,pixelWidth,pixelHeight,ndviArrayMVC)
