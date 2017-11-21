import argparse
import time
from subprocess import Popen

year = "2017"
month = "03"
day = "06"

parser = argparse.ArgumentParser()
parser.add_argument('-dr', help="Dry run", action="store_true")
args = parser.parse_args()
dry_run = args.dr
username = "mmage"
password = "ue3AaxCIb23I"
hMin = 6
hMax = 15
vMin = 1
vMax = 13
for h in range(hMin, hMax + 1):
    for v in range(vMin, vMax + 1):
        s = "wget -P modis/ -r -np -nH -R index.html https://e4ftl01.cr.usgs.gov/MOLT/MOD13Q1.006/2017.09.30/ --user mmage --password ue3AaxCIb23I -nd -A \"*h" + str(
            h).zfill(2) + "v" + str(v).zfill(2) + "*.hdf\""
        if dry_run:
            print s
        else:
            p = Popen(s, shell=True)
            time.sleep(5)