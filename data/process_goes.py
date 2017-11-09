import os
import glob


files = glob.glob('goes/*/*/O*.nc')
def run(fi):
    os.system('gdalwarp -t_srs "EPSG:3857" NETCDF:{}:Rad {}'.format(fi, os.path.dirname(
        fi) + '/' + os.path.basename(fi).split('.')[0] + '.tif'))
print files
from multiprocessing.dummy import Pool as ThreadPool
pool = ThreadPool(4)
# results = pool.map(run, files)
fi = files[0]
print 'gdalwarp -t_srs "EPSG:3857" NETCDF:{}:Rad {}'.format(fi, os.path.dirname(
        fi) + '/' + os.path.basename(fi).split('.')[0] + '.tif')