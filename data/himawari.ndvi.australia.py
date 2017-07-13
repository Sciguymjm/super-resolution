import gdal,osr
import numpy as np
import glob,os,argparse
import matplotlib.pyplot as plt
from pylab import *

parser = argparse.ArgumentParser()
parser.add_argument('inDir', help='Input Directory')
parser.add_argument('outDir')
args = parser.parse_args()

inDir = args.inDir
outDir = args.outDir

pixelWidth = 0.01
pixelHeight = 0.01
visRows = 12000
visCols = 12000
extRows = 24000
extCols = 24000

def array2raster(newRasterfn,pixelWidth,pixelHeight,array):
  cols = array.shape[1]
  rows = array.shape[0]
  originX = 85
  originY = -60
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

flist = glo1b.glob(os.path.join(inDir,'*vis.01.fld.geoss.dat'))
print flist
for raster in flist:
  utcHour = int(os.path.basename(raster)[8:10])
  print raster,utcHour
  red = raster.replace('vis','ext')
  nir = raster.replace('.01.','.03.')
  ndvi = os.path.join(outDir,os.path.basename(raster)[:12]+'.ndvi.tif')
  ndviMVC = os.path.join(os.path.basename(raster)[:8]+'.ndvi.utc-0-6.MVC.tif')
  ndviArrayMVC = np.zeros((visRows,visCols),dtype=np.int16)
  redArray = np.fromfile(red,dtype='f4').reshape(extRows,extCols)
  nirArray = np.fromfile(nir,dtype='f4').reshape(visRows,visCols)
  redArray_aggr = redArray.reshape(visRows,2,visCols,2).mean(axis=(1,3))
  nirArray = nirArray[7000:10000,2500:7000]
  redArray_aggr = redArray_aggr[7000:10000,2500:7000]
  ndviArray = (nirArray-redArray_aggr)/(nirArray+redArray_aggr)
  ndviArray = np.nan_to_num(ndviArray)
  ndviArray = np.where(np.logical_and(ndviArray<1,ndviArray>0),ndviArray,-0.9999)
  ndviArray = ndviArray*10000
  ndviArray = ndviArray.astype('i2')
  ndviArray = ndviArray[::-1] # reverse array so the tif looks like the array
  if utcHour<6:
    ndviArrayMVC = np.maximum(ndviArray,ndviArrayMVC)
  array2raster(ndvi,pixelWidth,pixelHeight,ndviArray)
  array2raster(ndviMVC,pixelWidth,pixelHeight,ndviArrayMVC)
