import glob

import gdal
import os

tilesize = 100
flist = glob.glob("composite/*.tif")
for f in flist:
    a = gdal.Open(f, gdal.GA_ReadOnly)
    width, height = a.ReadAsArray().shape
    for i in range(0, width, tilesize):
        for j in range(0, height, tilesize):
            opt = gdal.TranslateOptions(width=tilesize, height=tilesize, srcWin=(i, j, tilesize, tilesize))
            gdal.Translate(os.path.join("tiles", str(i) + "_" + str(j) + ".tif"), a, options=opt)
