# MCD43B3, MOD09A1
import argparse
import datetime
import glob
import os

import gdal
import numpy as np

originX = 85  # starting longitude
originY = -60  # starting latitude
pixelWidth = 0.01
pixelHeight = 0.01
parser = argparse.ArgumentParser()
parser.add_argument("-dl", help="Download Himawari data from S3", action="store_true")
parser.add_argument("--process", help="Process Himawari data from S3", action="store_true")
args = parser.parse_args()
mem_driver = gdal.GetDriverByName('MEM')


def array2raster(newRasterfn, pixelWidth, pixelHeight, array, code):
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
    outRasterSRS = gdal.osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(code)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

def process(filepath, layer, layerfilepath):
    file_type = layer.split(' ')[3].lower()
    print layerfilepath
    # print ds.GetMetadata()
    tempndvi = gdal.Open(layerfilepath)
    array2raster(file_type + '-test.tif', 250, 250, tempndvi.ReadAsArray(), 3857)
    output = filepath.replace('.hdf', layer + "-test.tif")
    gdal.Warp(output, tempndvi, dstSRS='EPSG:3857')
    # gdal.Warp(himawari_warped, himawari_unwarped, srcSRS='EPSG:4326', dstSRS='EPSG:3857')
    if "composite" not in layer:

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
        himawari_download_files = [
            (timendate + datetime.timedelta(days=i)).strftime("%Y%m%d%H%M.*.dat".format(file_type)) for i in range(16)]
        # os.system('python data/process_himawari.py data/himawari data/himawari')
        himawari_files = [
            'data/processed/' + (timendate + datetime.timedelta(days=i)).strftime("%Y%m%d%H%M.{}.tif".format(file_type))
            for i in range(16)]
        print himawari_files, [os.path.isfile(f) for f in himawari_files]
        file_exists = [os.path.isfile(f) for f in himawari_files]
        if args.dl:
            for exists, h in zip(file_exists, himawari_download_files):
                if not exists:
                    os.system('aws s3 sync s3://himawari-nex/radiance/ data/himawari/ --exclude "*" --include "{}"'.format(h))
                print h
        if args.process:
            os.system('python data/process_himawari.py data/himawari data/processed')
        assert all([os.path.isfile(f) for f in himawari_files])  # make sure all the files are present before proceeding

        # Reshaping modis to lower resolution
        modis_refl_warped_b = gdal.Open(output, gdal.GA_ReadOnly)
        modis_shape_before = modis_refl_warped_b.GetRasterBand(1).ReadAsArray().shape
        print modis_shape_before
        gdal.WarpOptions()
        gdal.Warp('modis.tif', modis_refl_warped_b, width=modis_shape_before[0] / 2, height=modis_shape_before[1] / 2, resampleAlg='near')

        modis_refl_warped = gdal.Open('modis.tif', gdal.GA_ReadOnly)
        ulx, xres, xskew, uly, yskew, yres = modis_refl_warped.GetGeoTransform()
        lrx = ulx + (modis_refl_warped.RasterXSize * xres)
        lry = uly + (modis_refl_warped.RasterYSize * yres)
        print "ulx {} uly {} lrx {} lry {}".format(ulx, uly, lrx, lry)
        modis_shape = modis_refl_warped.GetRasterBand(1).ReadAsArray().shape
        print modis_shape
        matrix = np.zeros((modis_shape[0], modis_shape[1], 16))  # create the array
        for i, f in enumerate(himawari_files):
            himawari_unwarped = gdal.Open(f, gdal.GA_ReadOnly)
            # Do the needful
            himawari_warped = 'hw.tif'
            gdal.Warp(himawari_warped, himawari_unwarped, srcSRS='EPSG:4326', dstSRS='EPSG:3857')
            himawari_cutout = output + '-test-2.tif'
            gdal.Warp(himawari_cutout, himawari_warped, outputBoundsSRS='EPSG:3857', outputBounds=[ulx, lry, lrx, uly])
            print "Opening layer", i
            data = gdal.Open(himawari_cutout, gdal.GA_ReadOnly)
            d = data.GetRasterBand(1).ReadAsArray()
            print "Done"
            print modis_shape, d.shape
            matrix[:, :, i] = d[:modis_shape[0], :modis_shape[1]]
        print "Opening composite doy...."
        m = gdal.Open(filepath + '250m 16 days composite day of the year-test.tif')
        print "Done."
        modis_doy_array = m.GetRasterBand(1).ReadAsArray()
        shape = modis_doy_array.shape  # read shape to form ogrid
        i, j = np.ogrid[:shape[0], :shape[1]]
        modis_doy_array -= modis_doy
        modis_doy_array = modis_doy_array.clip(min=0)
        himawari_composite = matrix[i, j, modis_doy_array]
        print "Done compositing"
        driver = gdal.GetDriverByName('GTiff')
        outRaster = driver.Create("data/processed/composite-" + ".".join(filepath.split('.')[1:4]) + file_type + '.tif',
                                  himawari_composite.shape[1], himawari_composite.shape[0], 1, gdal.GDT_Int16)
        outRaster.SetGeoTransform(modis_refl_warped.GetGeoTransform())
        outband = outRaster.GetRasterBand(1)
        outband.SetNoDataValue(-9999)
        outband.WriteArray(himawari_composite)
        outRasterSRS = gdal.osr.SpatialReference()
        outRasterSRS.ImportFromEPSG(3857)
        outRaster.SetProjection(outRasterSRS.ExportToWkt())
        outband.FlushCache()
        # gdal.Translate(output + '-test-2.tif', temp_hw, projWin=[ulx, uly, lrx, lry], projWinSRS='EPSG:3857', xRes=1000, yRes=1000)
        # gdal.TranslateOptions()


def main():
    raw_dir = "data/modis"
    netcdf_dir = "data/modis"

    layers = ["250m 16 days composite day of the year", "250m 16 days NDVI", "250m 16 days NIR reflectance"] # doy 1st
    raw_files = glob.glob(raw_dir + '/*.hdf')
    for filepath in raw_files:
        ds = gdal.Open(filepath, gdal.GA_ReadOnly)
        datasets = ds.GetSubDatasets()
        for layer in layers:
            for dataset in datasets:
                if layer in dataset[0]:
                    print dataset
                    process(filepath, layer, dataset[0])


if __name__ == '__main__':
    main()
