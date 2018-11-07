import spipy
from mpi4py import MPI
import sys
import os
import json
import h5py
from ConfigParser import ConfigParser
import re
import time
import numpy as np

comm = MPI.COMM_WORLD
mpi_rank = comm.Get_rank()
mpi_size = comm.Get_size()


def findnumber(string):
	return re.findall(r"\d+\.?\d*", string)

def avg_polling(myarr, factor, ignoredim=0):
	# 3D data avg pooling, along the first dimension
	# crop edges if the shape is not a multiple of factor
	if ignoredim > 0: myarr = myarr.swapaxes(0,ignoredim)
	zs,ys,xs = myarr.shape
	crarr = myarr[:,:ys-(ys % int(factor)),:xs-(xs % int(factor))]
	dsarr = np.mean(np.concatenate([[crarr[:,i::factor,j::factor] 
		for i in range(factor)] 
		for j in range(factor)]), axis=0)
	if ignoredim > 0: dsarr = dsarr.swapaxes(0,ignoredim)
	return dsarr


if __name__ == '__main__':
	"""
	python HF.py [runtime.json] [config.ini]
	* runtime.json should contain : 
		dataset : paths of input data files, list
		darkcal : path of dark calibration, str
		job_num : number of jobs for every data file, list
		pat_num : number of patterns in every data file, list
		save_path : path (dir) for saving results, str
		run_name  : name of this run, str
	"""

	runtime_json = sys.argv[1]
	config_ini   = sys.argv[2]
	with open(config_json, 'r') as fp:
		runtime = json.load(runtime_json)
	config = ConfigParser()
	config.read(config_ini)
	# read runtime param
	data_files = runtime['dataset']
	# read config param
	sec     = config.sections()[0]
	inh5    = config.get(sec, 'data-path in cxi/h5')
	roi     = findnumber(config.get(sec, 'roi radii range'))
	chi_cut = config.getint('chi-square cut-off')
	save_hits  = config.getint(sec, 'save_hits')
	if save_hits > 0:
			downsampling = config.getint(sec, 'downsampling')

	# center, radii_range
	center = np.array(mask.shape)/2
	radii_range = [center[0], center[1], int(roi[0]), int(roi[1])]

	# broadcast data
	if mpi_rank == 0:

		# read runtime param
		dark_file  = runtime['darkcal']
		job_num    = runtime['job_num']
		pat_num    = runtime['pat_num']
		save_path  = runtime['save_path']
		run_name   = runtime['run_name']
		# read config param
		sec = config.sections()[0]
		mask_file  = config.get(sec, 'mask (.npy)')

		# load mask
		if os.path.exists(mask_file):
			user_mask = np.load(mask_file)
		else:
			user_mask = None
			print("Mask file is not given")

		# load darkcal
		darkcal_fp = h5py.File(dark_file, 'r')
		darkmask = darkcal_fp['mask'][...]
		darkbg = darkcal_fp['bg'][...]
		darkcal_fp.close()

		# combine darkmask and user mask
		if user_mask is not None:
			mask = user_mask & darkmask
		else:
			mask = darkmask

		# data broadcast
		ranki = 0
		for ind, dataf in enumerate(data_files):
			numdata = pat_num[ind]
			bins = np.linspace(0, numdata, job_num[ind]+1, dtype=int)
			for i, low in enumerate(bins[:-1]):
				datapart = [ind, low, bins[i+1]]
				comm.send([datapart, darkbg, mask], dst=ranki+i)
			ranki += job_num[ind]
			print("Submit %d jobs for hit-finding of %s" % (job_num[ind], dataf))

	datapart, background, mask = comm.recv(source=0)

	# load data
	fp = h5py.File(data_files[datapart[0]], 'r')
	data = fp[inh5][datapart[1]:datapart[2]]
	fp.close()

	# hit-finder
	label = spipy.image.preprocess.hit_find(dataset=data, background=background, radii_range=radii_range, mask=mask, cut_off=chi_cut)

	result = [datapart[0], datapart[1], datapart[2], label]

	if save_hits > 0:
		tmp = data[np.where(label==1)[0]] - background
		if downsampling > 1:
			hfhits = avg_polling(tmp, downsampling)
		else:
			hfhits = tmp

	# gather
	combined_result = comm.gather(result, root=0)
	if save_hits > 0:
		combined_hfhits = comm.gather(hfhits, root=0)

	# output
	if mpi_rank == 0:
		print("Gathering results and writing files")

		if save_hits > 0:

			combined_result = np.concatenate(combined_hfhits, axis=0)
			save_file = os.path.join(save_path, run_name+".hfhits.h5")
			fp = h5py.File(save_file, 'w')
			grp = fp.create_group("Hits")
			grp.create_dataset("data", data=combined_result, chunks=True, compression="gzip")
			grp2 = fp.create_group("Raw-Parameters")
			grp2.create_dataset("rawfiles", data=data_files)
			grp2.create_dataset("radii_range", data=radii_range)
			grp2.create_dataset("darkcal", data=dark_file)
			grp2.create_dataset("chi-square-cut", data=chi_cut)
			grp2.create_dataset("downsampling", data=downsampling)
			grp3 = fp.create_group("Middle-Output")
			grp3.create_dataset("mask", data=mask, chunks=True, compression="gzip")
			grp3.create_dataset("background", data=background, chunks=True, compression="gzip")
			fp.close()


		label_part = [None] * len(data_files)
		for i in range(len(data_files)):
			label_part[i] = np.zeros(pat_num[i], dtype=int)

		for re in combined_result:
			label_part[re[0]][re[1]:re[2]] = re[3]

		for i, df in enumerate(data_files):
			sf = os.path.splitext(os.path.split(df)[-1])[0]
			save_file = os.path.join(save_path, sf+".hflabel.dat")
			np.savetxt(save_file, label_part[i])


