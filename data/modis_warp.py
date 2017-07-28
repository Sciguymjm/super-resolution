from subprocess import call
import glob

# gdalwarp -overwrite -t_srs EPSG:3857 -r near -multi -dstnodata -9999 -of GTiff "HDF4_EOS:EOS_GRID:\"MOD13Q1.A2016209.h29v05.005.2016226031232.hdf\":MODIS_Grid_16DAY_250m_500m_VI:250m 16 days NDVI" out.tif
flist = glob.glob("modis/*.hdf")

for f in flist:
    call("gdalwarp -overwrite -t_srs EPSG:3857 -r near -multi -dstnodata -9999 -of GTiff \"HDF4_EOS:EOS_GRID:\\\"" + f + "\\\":MODIS_Grid_16DAY_250m_500m_VI:250m 16 days NDVI\" " + f.split("/")[0] + "/warped-ndvi-" + f.split("/")[1].replace("hdf", "tif"), shell=True)
    call("gdalwarp -overwrite -t_srs EPSG:3857 -r near -multi -dstnodata -9999 -of GTiff \"HDF4_EOS:EOS_GRID:\\\"" + f + "\\\":MODIS_Grid_16DAY_250m_500m_VI:250m 16 days EVI\" " + f.split("/")[0] + "/warped-evi-" + f.split("/")[1].replace("hdf", "tif"), shell=True)
    call("gdalwarp -overwrite -t_srs EPSG:3857 -r near -multi -dstnodata -9999 -of GTiff \"HDF4_EOS:EOS_GRID:\\\"" + f + "\\\":MODIS_Grid_16DAY_250m_500m_VI:250m 16 days NIR reflectance\" " + f.split("/")[0] + "/warped-nir-" + f.split("/")[1].replace("hdf", "tif"), shell=True)
    call("gdalwarp -overwrite -t_srs EPSG:3857 -r near -multi -dstnodata -9999 -of GTiff \"HDF4_EOS:EOS_GRID:\\\"" + f + "\\\":MODIS_Grid_16DAY_250m_500m_VI:250m 16 days composite day of the year\" " + f.split("/")[0] + "/warped-cdoy-" + f.split("/")[1].replace("hdf", "tif"), shell=True)