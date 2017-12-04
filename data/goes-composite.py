# coding: utf-8

# # Estimation of MODIS-like Surface-Spectral Reflectance from Geostationary Satellites using Deep Neural Networks 

# ## Setup

# In[1]:

import datetime
import glob
import os
import gc

import gdal
import matplotlib
import numpy as np

matplotlib.rcParams['figure.figsize'] = "8,8"
import scipy.ndimage

def proc(day):
    goes_selected = sorted(glob.glob('goes/{}/{}/O*C03*.nc'.format(day, timendate.hour)))
    if len(goes_selected) < 1:
        os.system(
            'aws s3 sync s3://noaa-goes16/ABI-L1b-RadF/2017/{}/ goes/{}/ --exclude "*" --include "*M3C03_*2017{}{}*"'.format(
                day, day, day,
                timendate.strftime('%H%M')))
    goes_selected = sorted(glob.glob('goes/{}/{}/O*C03*.nc'.format(day, timendate.hour)))
    temp = []
    for i, fi in enumerate(goes_selected):
        f = os.path.basename(fi)
        gtime = f[34:38]
        ftime = datetime.datetime.strptime(gtime, '%H%M')
        if ftime.hour == timendate.hour and ftime.minute == timendate.minute:
            temp.append(fi)
    return day, temp


def warp_goes(r):
    i, day = r
    if len(goes_dict[day]) > 0:
        f = goes_dict[day][0]  # veggie NIR
        output = os.path.dirname(f) + '/' + os.path.basename(f).split('.')[0] + '.tif'

        if not os.path.isfile(output):
            t = gdal.Warp(output, 'NETCDF:' + f + ':Rad', dstSRS='EPSG:3857')
            print (output)


if __name__ == '__main__':

    raw_dir = "modis"
    layers = ["250m 16 days composite day of the year",  # doy 1st for compositing reasons
              "250m 16 days NDVI",
              "250m 16 days NIR reflectance"]
    raw_files = glob.glob(raw_dir + '/*.hdf')

    # In[3]:



    fs = [f for f in raw_files if 'A2017273' in f]  # set day here
    day_of_year = int(fs[0].split('.')[4][4:7])

    # In[4]:
    for filepath in fs:

        ds = gdal.Open(filepath, gdal.GA_ReadOnly)
        datasets = ds.GetSubDatasets()
        datasets[:2]

        # ## Day of Year

        # In[5]:


        doy_layer = ""
        for dataset in datasets:
            if layers[0] in dataset[0]:
                doy_layer = dataset[0]
        file_type = doy_layer.split(' ')[3].lower()
        doy_layer, file_type

        # In[6]:


        doy_modis = gdal.Open(doy_layer)

        # In[7]:


        output = filepath.replace('.hdf', '.' + file_type + ".tif")
        gdal.Warp(output, doy_modis, dstSRS='EPSG:3857', xRes=1000, yRes=1000, resampleAlg='near')
        data = gdal.Open(output)
        doy_arr = data.ReadAsArray()

        # ## Near Infrared

        # In[8]:


        nir_layer = ""
        for dataset in datasets:
            if layers[2] in dataset[0]:
                nir_layer = dataset[0]

        file_type = nir_layer.split(' ')[3].lower()
        print (nir_layer, file_type)

        # In[9]:

        nir_modis = gdal.Open(nir_layer)
        nir = nir_modis.ReadAsArray()

        # In[10]:


        output = filepath.replace('.hdf', '.' + file_type + ".tif")
        gdal.Warp(output, nir_modis, dstSRS='EPSG:3857', xRes=1000, yRes=1000, resampleAlg='near')
        data = gdal.Open(output)
        nir_arr = data.ReadAsArray()
        print (nir.shape, nir_arr.shape)
        # In[11]:


        ulx, xres, xskew, uly, yskew, yres = data.GetGeoTransform()
        lrx = ulx + (data.RasterXSize * xres)
        lry = uly + (data.RasterYSize * yres)
        srs = data.GetProjection()

        # In[12]:
        # t = gdal.Warp('test5.tif', 'NETCDF:goes/257/18/OR_ABI-L1b-RadF-M3C02_G16_s20172571800379_e20172571811146_c20172571811182.nc:Rad', dstSRS='EPSG:3857')
        cut = gdal.Warp('cutout.tif', gdal.Open('test5.tif'), outputBoundsSRS=srs, outputBounds=[ulx, lry, lrx, uly])
        culx, cxres, cxskew, culy, cyskew, cyres = cut.GetGeoTransform()
        # ## GOES-16 NIR

        # In[13]:


        doy = int(filepath.split('.')[1][5:])
        year = int(filepath.split('.')[4][0:4])
        date = datetime.datetime(year, 1, 1) + datetime.timedelta(doy - 1)

        offsets = {
            '00': 240,
            '01': 120,
            '02': 80,
            '03': 60,
            '04': 51,
            '05': 45,
            '06': 42,
            '07': 40,
            '08': 40,
            '09': 40,
            '10': 40,
            '11': 42,
            '12': 45,
            '13': 51,
            '14': 60,
            '15': 80,
            '16': 120,
            '17': 240
        }

        # Find closest goes-16 times
        modis_time = filepath.split('.')[4][7:]
        # _time = datetime.datetime.strptime(modis_time, "%H%M%S") + datetime.timedelta(hours=5)
        _time = datetime.time(19, 15, 0)  # UTC
        ft = filepath.split('.')[2]
        h = ft[1:3]
        v = ft[4:6]
        # _time += datetime.timedelta(minutes=offsets[v] * int(h))
        #
        # if _time.minute % 15 > 7:
        #     _time += datetime.timedelta(minutes=15 - (_time.minute % 15))
        # else:
        #     _time += datetime.timedelta(minutes=-_time.minute % 15)
        timendate = datetime.datetime.combine(date.date(), _time)
        timendate.strftime('%Y-%m-%d %H:%M')
        result = []
        for x in list(range(timendate.timetuple().tm_yday, timendate.timetuple().tm_yday + 16)):
            result.append(proc(x))
        goes_dict = {x: y for x, y in result}
        test_run = False
        for x in enumerate(goes_dict):
            warp_goes(x)

        ratio = data.GetGeoTransform()[1] / cxres

        # resize using nn
        # resized_nir = scipy.ndimage.zoom(data.ReadAsArray(), ratio, order=0)
        # shape = resized_nir.shape
        gc.collect()
        shape = nir_arr.shape
        print ("matrix shape", shape)
        matrix = np.zeros((shape[0], shape[1], 16))

        for r in enumerate(goes_dict):
            i, day = r
            if len(goes_dict[day]) > 0:
                f = goes_dict[day][0]  # veggie NIR
                output = os.path.dirname(f) + '/' + os.path.basename(f).split('.')[0] + '.tif'
                t = gdal.Open(output)
                if not os.path.isfile(output):
                    t = gdal.Warp(output, 'NETCDF:' + f + ':Rad', dstSRS='EPSG:3857')
                    print (output)
                else:
                    t = gdal.Open(output)
                dst_filename = 'cutout.tif'
                os.remove(dst_filename)
                dst = gdal.GetDriverByName('GTiff').Create(dst_filename, data.RasterXSize, data.RasterYSize, 1, gdal.GDT_Float32)
                dst.SetGeoTransform(data.GetGeoTransform())
                dst.SetProjection(data.GetProjection())
                gdal.ReprojectImage(t, dst, t.GetProjection(), data.GetProjection(), gdal.GRA_NearestNeighbour)
                del dst
                # cut = gdal.Warp('cutout.tif', t, outputBoundsSRS=srs, outputBounds=[ulx, lry, lrx, uly])
                cut = gdal.Open('cutout.tif')
                culx, cxres, cxskew, culy, cyskew, cyres = cut.GetGeoTransform()
                arr = cut.ReadAsArray()
                print (day, np.sum(arr == 0))
                assert arr.shape == shape, "{} is not equal to {}".format(arr.shape, shape)
                if test_run:
                    for x in range(16):
                        matrix[:, :, x] = arr
                    continue
                else:
                    matrix[:, :, i] = arr
        for layer in range(16):
            matrix[:, :, layer][nir_arr == -1000] = -1000

        # Resize doy array
        # resize using nn
        # resized_doy = scipy.ndimage.zoom(doy_arr, ratio, order=0)
        i, j = np.ogrid[:shape[0], :shape[1]]
        doy_arr -= doy
        doy_arr = doy_arr.clip(min=0)
        # assert doy_arr.max() == 15 # prevent off by one errors
        composite = matrix[i, j, doy_arr]


        def array_to_raster_w_source(dst_filename, array, source):
            """Array > Raster
            Save a raster from a C order array using another dataset as source.

            :param array: ndarray
            """
            driver = gdal.GetDriverByName('GTiff')

            dataset = driver.Create(
                dst_filename,
                array.shape[1],
                array.shape[0],
                1,
                gdal.GDT_Float32)

            dataset.SetGeoTransform(source.GetGeoTransform())
            dataset.GetRasterBand(1).WriteArray(array)
            dataset.GetRasterBand(1).SetNoDataValue(-1000)  ##if you want these values transparent
            dataset.SetGeoTransform(source.GetGeoTransform())
            dataset.SetProjection(source.GetProjection())
            dataset.FlushCache()  # Write to disk.


        fn = 'composite/{}/{}.tif'.format(doy, filepath.split('.')[2])
        if not os.path.exists(os.path.dirname(fn)):
            os.makedirs(os.path.dirname(fn))
        array_to_raster_w_source(fn, composite, cut)  # use the cutout for proper resolution
    os.system(
        'gdal_merge.py -n -1000 -a_nodata -1000 -of GTiff -o composite/{}/composite-{}.tif composite/{}/h*.tif'.format(doy, doy, doy))
