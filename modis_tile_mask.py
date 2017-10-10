import glob
import os
# MCD43B3, MOD09A1
import gdal

originX = 85  # starting longitude
originY = -60  # starting latitude
pixelWidth = 0.01
pixelHeight = 0.01


def main():
    raw_dir = "data\modis"
    netcdf_dir = "data\modis"

    layers = ["250m 16 days EVI", "250m 16 days NDVI", "250m 16 days NIR reflectance",
              "250m 16 days composite day of the year"]
    raw_files = glob.glob(raw_dir + '\*.hdf')
    for filepath in raw_files:
        ds = gdal.Open(filepath, gdal.GA_ReadOnly)
        datasets = ds.GetSubDatasets()
        # print ds.GetMetadata()
        tempndvi = gdal.Open(datasets[0][0])
        output = filepath + "-test.tif"
        gdal.Warp(output, tempndvi, dstSRS='EPSG:3857', xRes=1000, yRes=1000, targetAlignedPixels=True)
        ndvi = gdal.Open(output, gdal.GA_ReadOnly)
        ulx, xres, xskew, uly, yskew, yres = ndvi.GetGeoTransform()
        lrx = ulx + (ndvi.RasterXSize * xres)
        lry = uly + (ndvi.RasterYSize * yres)
        print "ulx {} uly {} lrx {} lry {}".format(ulx, uly, lrx, lry)
        hw = gdal.Open(r'data\himawari\201608020030.ndvi.tif', gdal.GA_ReadOnly)
        # Do the needful
        temp_hw = 'hw.tif'
        gdal.Warp(temp_hw, hw, srcSRS='EPSG:4326', dstSRS='EPSG:3857')
        gdal.Warp(output+'-test-3.tif', temp_hw, outputBoundsSRS='EPSG:3857', outputBounds=[ulx, lry, lrx, uly], xRes=1000, yRes=1000)
        # gdal.Translate(output + '-test-2.tif', temp_hw, projWin=[ulx, uly, lrx, lry], projWinSRS='EPSG:3857', xRes=1000, yRes=1000)
        # gdal.TranslateOptions()
        break

if __name__ == '__main__':
    main()
