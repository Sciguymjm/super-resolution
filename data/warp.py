from subprocess import call
import glob

# gdalwarp -overwrite -t_srs EPSG:3857 -r near -multi -dstnodata -9999 -of GTiff 201608020030.ndvi.tif out2.tif
flist = glob.glob("himawari/*.tif")

for f in flist:
    call("gdalwarp -overwrite -t_srs EPSG:3857 -r near -multi -dstnodata -9999 -of GTiff "  + f + " " + f.split("/")[0] + "/warped-" + f.split("/")[1], shell=True)