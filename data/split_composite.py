import glob
import os

import gdal

# gdal_translate -a_nodata -1000 -projwin -15425753.6385 11024335.6624 -3467661.98227 -6556434.85207 C:/Users/Mr/PycharmProjects/superresolution/data/composite/273/composite-273.tif test.tif
#                                            x1            y1              x2            y2
x1 = -15425753.6385
y1 = 11024335.6624
x2 = -3467661.98227
y2 = -6556434.85207
doy = 273
tilesize = 100 * 1000  # meters


def parse_filelist(string, prefix=''):
    flist = glob.glob(string)
    for f in flist:
        folder = os.path.join('tiles', str(doy))
        if not os.path.isdir(folder):
            os.makedirs(folder)
        a = gdal.Open(f, gdal.GA_ReadOnly)
        width, height = a.ReadAsArray().shape
        for i in range(int(x1), int(x2), tilesize):
            for j in range(int(y1), int(y2), -tilesize):
                fn = os.path.join("tiles", os.path.join(str(doy), prefix + '_' + str(i) + "_" + str(j) + ".tif"))
                # opt = gdal.TranslateOptions(width=tilesize, height=tilesize, srcWin=(i, j, tilesize, tilesize))
                os.system(
                    'gdal_translate -a_nodata -1000 -projwin {} {} {} {} {} {}'.format(i, j, i + tilesize, j - tilesize,
                                                                                       f, fn))


# parse_filelist("composite/{}/composite-*.tif".format(doy, doy), "g")
parse_filelist("modis/273-composite.tif", "m")
