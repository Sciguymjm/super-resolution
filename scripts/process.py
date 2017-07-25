import tensorflow as tf
import numpy as np
import glob
import xarray as xr

def process(imgs):
	parts = []
	print vars(imgs[0])
	for i in imgs:
		for r in range(0, 4800, 100):
			for c in range(0, 4800, 100):
				parts.append(i.values[r:r+100, c:c+100])
	print parts

data = []

if __name__ == "__main__":
	h_files = glob.glob("../data/modis/himawari_*.nc")
	m_files = glob.glob("../data/modis/MOD*.nc")
	print h_files, m_files
	for f in h_files:	
		ds = xr.open_dataset(f)
		data.append(ds)
	process(data)
