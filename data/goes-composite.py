
# coding: utf-8

# # Estimation of MODIS-like Surface-Spectral Reflectance from Geostationary Satellites using Deep Neural Networks 

# ## Setup

# In[1]:

import argparse
import datetime
import glob
import os

import gdal
import numpy as np
from IPython.display import Image
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['figure.figsize'] = "8,8"
import scipy.ndimage
gdal.VersionInfo()


# In[2]:


raw_dir = "modis"
layers = ["250m 16 days composite day of the year", # doy 1st for compositing reasons
          "250m 16 days NDVI", 
          "250m 16 days NIR reflectance"] 
raw_files = glob.glob(raw_dir + '/*.hdf')


# In[3]:



fs = [f for f in raw_files if 'A2017257' in f] # set day here
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
    gdal.Warp(output, doy_modis, dstSRS='EPSG:3857')
    data = gdal.Open(output)
    doy_arr = data.ReadAsArray()



    # ## Near Infrared

    # In[8]:


    nir_layer = ""
    for dataset in datasets:
        if layers[2] in dataset[0]:
            nir_layer = dataset[0]

    file_type = nir_layer.split(' ')[3].lower()
    print nir_layer, file_type


    # In[9]:


    nir_modis = gdal.Open(nir_layer)
    nir_modis.ReadAsArray()


    # In[10]:


    output = filepath.replace('.hdf', '.' + file_type + ".tif")
    gdal.Warp(output, nir_modis, dstSRS='EPSG:3857')
    data = gdal.Open(output)
    nir_arr = data.ReadAsArray()

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

    # Find closest goes-16 times
    modis_time = filepath.split('.')[4][7:]
    _time = datetime.datetime.strptime(modis_time, "%H%M%S")
    if _time.minute % 15 > 7:
        _time += datetime.timedelta(minutes=15 - (_time.minute % 15))
    else:
        _time += datetime.timedelta(minutes=-_time.minute % 15)
    timendate = datetime.datetime.combine(date.date(), _time.time())
    timendate.strftime('%Y-%m-%d %H:%M')

    goes_dict = {}
    for day in range(timendate.timetuple().tm_yday, timendate.timetuple().tm_yday + 16):
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
        goes_dict[day] = temp
    print goes_dict, timendate


    # resize using nn
    resized_nir = scipy.ndimage.zoom(data.ReadAsArray(), data.GetGeoTransform()[1] / cxres, order=0)
    shape = resized_nir.shape
    matrix = np.zeros((shape[0], shape[1], 16))

    test_run = False
    for i, day in enumerate(goes_dict):
        if len(goes_dict[day]) > 0:
            f = goes_dict[day][0]  # veggie NIR
            output = os.path.dirname(f) + '/' + os.path.basename(f).split('.')[0] + '.tif'

            if not os.path.isfile(output):
                t = gdal.Warp(output, 'NETCDF:' + f + ':Rad', dstSRS='EPSG:3857')
                print output
            else:
                t = gdal.Open(output)
            cut = gdal.Warp('cutout.tif', t, outputBoundsSRS=srs, outputBounds=[ulx, lry, lrx, uly])
            culx, cxres, cxskew, culy, cyskew, cyres = cut.GetGeoTransform()
            arr = cut.ReadAsArray()
            assert arr.shape == shape, "{} is not equal to {}".format(arr.shape, shape)
            if test_run:
                for x in range(16):
                    matrix[:, :, x] = arr
                break
            else:
                matrix[:, :, i] = arr
    for layer in range(16):
        matrix[:, :, layer][resized_nir == -1000] = -1000

    # Resize doy array
    # resize using nn
    resized_doy = scipy.ndimage.zoom(doy_arr, data.GetGeoTransform()[1] / cxres, order=0)
    print 'Ratio: ', xres / cxres

    i, j = np.ogrid[:shape[0], :shape[1]]
    resized_doy -= doy
    resized_doy = resized_doy.clip(min=0)
    composite = matrix[i, j, resized_doy]


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