import glob
from subprocess import call

# gdalwarp -overwrite -t_srs EPSG:3857 -r near -multi -dstnodata -9999 -of GTiff "HDF4_EOS:EOS_GRID:\"MOD13Q1.A2016209.h29v05.005.2016226031232.hdf\":MODIS_Grid_16DAY_250m_500m_VI:250m 16 days NDVI" out.tif
flist = glob.glob("modis/*.hdf")


def split_hdf(layer_name, layer_id):
    call(
        "gdalwarp -overwrite -t_srs EPSG:3857 -tr 1000 1000 -tap -r near -multi -dstnodata -9999 -of GTiff \"HDF4_EOS:EOS_GRID:\\\"" + f + "\\\":MODIS_Grid_16DAY_250m_500m_VI:250m 16 days " + layer_name + "\" " +
        f.split("/")[0] + "/warped-" + layer_id + "-" + f.split("/")[1].replace("hdf", "tif"), shell=True)

for f in flist:
    split_hdf("NDVI", "ndvi")
    split_hdf("EVI", "evi")
    split_hdf("NIR reflectance", "nir")
    split_hdf("composite day of the year", "cdoy")
call("rm modis/merged.tiff", shell=True)
call("gdalwarp -tr 1000 1000 -tap --config GDAL_CACHEMAX 3000 -wm 3000 modis/warped-*ndvi*225*.tif modis/ndvi-225.tif", shell=True)
call("gdalwarp -tr 1000 1000 -tap --config GDAL_CACHEMAX 3000 -wm 3000 modis/warped-*cdoy*225*.tif modis/cdoy-225.tif", shell=True)