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
hMin = 23
hMax = 32
vMin = 3
vMax = 13
for h in range(hMin, hMax + 1):
    for v in range(vMin, vMax + 1):
        s = "wget -P modis/ -r -np -nH -R index.html https://e4ftl01.cr.usgs.gov/MOLT/MOD13Q1.005/2016.08.12/ --user mmage --password ue3AaxCIb23I -nd -A \"*h" + str(
            h).zfill(2) + "v" + str(v).zfill(2) + "*.hdf\""
        if dry_run:
            print s
        else:
            p = Popen(s, shell=True)
            time.sleep(5)
