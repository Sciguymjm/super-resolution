import argparse
import time
from subprocess import Popen

start = 257
end = start + 1
start_hour = 0
end_hour = 24
parser = argparse.ArgumentParser()
parser.add_argument('-dr', help="Dry run", action="store_true")
args = parser.parse_args()
dry_run = args.dr
for d in range(start, end):
    s = 'aws s3 sync s3://noaa-goes16/ABI-L1b-RadF/2017/{} ./goes/{} --exclude "*" --include "*M3C02*" --include "*M3C03*"'.format(d, d)
    if dry_run:
        print s
    else:
        p = Popen(s, shell=True)
        time.sleep(5)