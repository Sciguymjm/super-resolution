import glob
import numpy as np
# MCD43B3, MOD09A1
import datetime
import time
import gdal
import os

originX = 85  # starting longitude
originY = -60  # starting latitude
pixelWidth = 0.01
pixelHeight = 0.01


def process(ds, filepath, layer, layerfilepath):
    print filepath, layerfilepath
    # print ds.GetMetadata()
    tempndvi = gdal.Open(layerfilepath)
    output = filepath + layer + "-test.tif"
    gdal.Warp(output, tempndvi, dstSRS='EPSG:3857', xRes=1000, yRes=1000, targetAlignedPixels=True)
    if "composite" not in layer:
        file_type = layer.split(' ')[3].lower()
        modis_doy = int(filepath.split('.')[1][5:])
        modis_year = int(filepath.split('.')[4][0:4])
        date = datetime.datetime(modis_year, 1, 1) + datetime.timedelta(modis_doy - 1)

        # Find closest himawari times
        modis_time = filepath.split('.')[4][7:]
        _time = datetime.datetime.strptime(modis_time, "%H%M%S")
        if _time.minute % 10 >= 5:
            _time += datetime.timedelta(minutes=10 - _time.minute % 10)
        else:
            _time += datetime.timedelta(minutes=-_time.minute % 10)
        timendate = datetime.datetime.combine(date.date(), _time.time())
        himawari_download_files = [(timendate + datetime.timedelta(days=i)).strftime("%Y%m%d%H%M.*.dat".format(file_type)) for i in range(16)]
        for h in himawari_download_files:
            os.system('aws s3 sync s3://himawari-nex/radiance/ data/himawari/ --exclude "*" --include "{}" --recursive'.format(h))
            print h
        os.system('python process_himawari.py data/himawari data/himawari')
        himawari_files = ['data/himawari/' + (timendate + datetime.timedelta(days=i)).strftime("%Y%m%d%H%M.{}.dat".format(file_type)) for i in range(16)]
        assert all([os.path.isfile(f) for f in himawari_files]) # make sure all the files are present before proceeding
        matrix = np.zeros((12000, 12000, 16)) # create the array
        for f in himawari_files:
            modis_refl_warped = gdal.Open(output, gdal.GA_ReadOnly)
            ulx, xres, xskew, uly, yskew, yres = modis_refl_warped.GetGeoTransform()
            lrx = ulx + (modis_refl_warped.RasterXSize * xres)
            lry = uly + (modis_refl_warped.RasterYSize * yres)
            print "ulx {} uly {} lrx {} lry {}".format(ulx, uly, lrx, lry)
            himawari_unwarped = gdal.Open(f, gdal.GA_ReadOnly)
            # Do the needful
            himawari_warped = 'hw.tif'
            gdal.Warp(himawari_warped, himawari_unwarped, srcSRS='EPSG:4326', dstSRS='EPSG:3857')
            himawari_cutout = output + '-test-2.tif'
            gdal.Warp(himawari_cutout, himawari_warped, outputBoundsSRS='EPSG:3857', outputBounds=[ulx, lry, lrx, uly],
                      xRes=1000, yRes=1000)

    # gdal.Translate(output + '-test-2.tif', temp_hw, projWin=[ulx, uly, lrx, lry], projWinSRS='EPSG:3857', xRes=1000, yRes=1000)
    # gdal.TranslateOptions()


def main():
    raw_dir = "data/modis"
    netcdf_dir = "data/modis"

    layers = ["250m 16 days EVI", "250m 16 days NDVI", "250m 16 days NIR reflectance",
              "250m 16 days composite day of the year"]
    raw_files = glob.glob(raw_dir + '/*.hdf')
    for filepath in raw_files:
        ds = gdal.Open(filepath, gdal.GA_ReadOnly)
        datasets = ds.GetSubDatasets()
        for layer in layers:
            for dataset in datasets:
                if layer in dataset[0]:
                    process(ds, filepath, layer, dataset[0])
        break


if __name__ == '__main__':
    main()
