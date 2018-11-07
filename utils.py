from PyQt4 import QtGui
from PyQt4 import QtCore

import sys
import os
import subprocess
import shlex
import re
import random
import time
import threading
from ConfigParser import ConfigParser
import json


information = {"report_bug" : "You run into a bug. But it's not your mistake, report it to shiyc12@csrc.ac.cn",\
			}


class TableMonitor(threading.Thread):

	def __init__(self, interval, func):
		threading.Thread.__init__(self)
		self.interval = interval
		self.stopflag = threading.Event()
		self.func = func

	def run(self):
		while not self.stopflag.wait(self.interval):
			self.func()

	def stop(self):
		self.stopflag.set()


def fmt_process_status(dataformat, hits = None, patterns = None):
	h = "---"
	p = "---"
	hr = "---"
	if type(hits) == int and type(patterns) == int:
		h = hits
		p = patterns
		if patterns > 0:
			hr = float(h)/float(p)
		else:
			hr = 0
		hr = "%.2f" % hr
	
	status = "Raw-Data  :  %s     Hits  :  %s     Patterns  :  %s     Hit-Rate  :  %s" %(dataformat, str(h), str(p), hr)
	return status


def extract_tag(assignments, tagfilename):
	return tagfilename.split(assignments+"_")[-1].split('.ini')[0]



def print2projectLog(rootdir, message):
	nowtime = time.ctime()
	st = "[INFO](%s) : %s\n" % (nowtime, message)
	with open(os.path.join(rootdir, "project.log"), 'a+') as f:
		f.write(st)


def rawdata_changelog(prev, now):
	nowtime = time.ctime()
	update = {}
	update[nowtime] = [prev, now]
	return update


def show_message(message):
	msgBox = QtGui.QMessageBox()
	msgBox.setTextFormat(QtCore.Qt.RichText)
	msgBox.setIcon(QtGui.QMessageBox.Critical)
	msgBox.setText(message)
	msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
	ret = msgBox.exec_()
	if ret == QtGui.QMessageBox.Ok:
		return 1



def show_warning(message):
	msgBox = QtGui.QMessageBox()
	msgBox.setTextFormat(QtCore.Qt.RichText)
	msgBox.setIcon(QtGui.QMessageBox.Warning)
	msgBox.setText(message)
	msgBox.addButton(QtGui.QPushButton('NO'), QtGui.QMessageBox.NoRole)
	msgBox.addButton(QtGui.QPushButton('YES'), QtGui.QMessageBox.YesRole)
	ret = msgBox.exec_()
	# ret == 1 -> YES ; ret == 0 -> NO
	return ret


def check_PBS():
	cmd = "command -v qsub qstat pestat"
	cmds = shlex.split(cmd)
	try:
		tmp = subprocess.check_output(cmds)
		return True
	except:
		return False


def check_datadir(datadir, fmt_ind, all_fmts, subDir):
	"""
	return code:
		[0, 0]   : no semingly data files found
		[1, -1]  : format is correct, subDir is wrong
		[str, 1] : format is wrong (return guessed format), subDir is correct
		[str, -1]: format is wrong (return guessed format), subDir is wrong
		[1, 1]   : test pass 
		[-1, -1] : error
	"""

	def check_subDir(dirs, fmt_ind, all_fmts):
		check_dir_num = min(10,len(dirs))
		for i in range(len(all_fmts)):
			count[i] = 0
		for i in range(check_dir_num):
			thisdir = random.choice(dirs)
			thisfiles_sub = [f.split(".")[-1].lower() for f in os.listdir(thisdir)\
										 if os.path.isfile(os.path.join(thisdir,f))]
			for i in range(len(all_fmts)):
				if thisfiles_sub.count(all_fmts[i]) > 0:
					count[i] += 1
			dirs.remove(thisdir)
		if count[fmt_ind] >= 1:
			# yes, secondary dirs
			return 1
		elif max(count) == 0:
			# empty
			return 0
		else:
			# data format problem
			return all_fmts[count.index(max(count))]


	allpath = [f for f in os.listdir(datadir) if f[0]!="." and f[0]!="$"]
	if len(allpath) == 0:
		return [0, 0]

	allfiles_ext = [f.split(".")[-1].lower() for f in allpath \
					if os.path.isfile(os.path.join(datadir,f))]
	alldirs = [os.path.join(datadir,d) for d in allpath if \
					os.path.isdir(os.path.join(datadir,d))]

	if subDir == False:
		# format is correct ?
		count = [0] * len(all_fmts)
		for i in range(len(all_fmts)):
			count[i] = allfiles_ext.count(all_fmts[i])
		most = count.index(max(count))
		if max(count) == 0:   # subDir incorrect
			if len(alldirs) == 0:   # empty
				return [0, 0]
			else:
				tmp = check_subDir(alldirs, fmt_ind, all_fmts)
				if tmp == 0:        # empty
					return [0, 0]
				elif tmp == 1:      # format correct
					return [1, -1]
				else:               # format incorrect
					return [tmp, -1]
		elif most == fmt_ind:  # subDir correct, format correct
			return [1, 1]
		else:                  # subDir correct, format incorrect
			return [all_fmts[most], 1]
	else:
		# format is correct ?
		count = [0] * len(all_fmts)
		for i in range(len(all_fmts)):
			count[i] = allfiles_ext.count(all_fmts[i])
		most = count.index(max(count))
		"""
		if max(count) == 0:   # subDir correct
			if len(alldirs) == 0:   # empty
				return [0, 0]
			else:
				tmp = check_subDir(alldirs, fmt_ind, all_fmts)
				if tmp == 0:        # empty
					return [0, 0]
				elif tmp == 1:      # format correct
					return [1, 1]
				else:               # format incorrect
					return [tmp, 1]
		elif most == fmt_ind:  # subDir incorrect, format correct
			return [1, -1]
		else:                  # subDir incorrect, format incorrect
			return [all_fmts[most], -1]
		"""
		if len(alldirs) == 0:     # no dir
			if max(count) == 0:   # empty
				return [0, 0]
			elif most == fmt_ind: # format correct, subDir incorrect
				return [1, -1]
			else:                 # format incorrect, subDir incorrect
				return [all_fmts[most], -1]
		else:
			tmp = check_subDir(alldirs, fmt_ind, all_fmts)
			if tmp == 0:            # no data in folder
				if max(count) == 0:
					return [0, 0]   # empty
				elif most == fmt_ind:
					return [1, -1]  # format correct, subDir incorrect
				else:
					return [all_fmts[most], -1]   # format incorrect, subDir incorrect
			elif tmp == 1:          # format correct, subDir correct
				return [1, 1]
			else:                   # format incorrect, subDir correct
				return [tmp, 1]
		


def parse_multi_runs(path, dataformat):
	# xtc file name format :
	# https://confluence.slac.stanford.edu/display/PSDM/Data+Formats
	all_files = [f for f in os.listdir(path) if f[0]!='.']
	if dataformat.lower() == "xtc":
		runs_multi = [findnumber(r)[1] for r in all_files if \
							os.path.isfile(os.path.join(path, r)) \
							and r.split('.')[-1].lower() == dataformat.lower()]
	else:
		runs_multi = [r for r in all_files if \
							os.path.isfile(os.path.join(path, r)) \
							and r.split('.')[-1].lower() == dataformat.lower()]
	runs = list(set(runs_multi))
	counts = [runs_multi.count(run) for run in runs]
	runs = [runs[i]+"#%d" % counts[i] for i in range(len(runs))]
	return runs


def parse_multi_run_streams(path, runname, dataformat):
	# xtc file name format :
	# https://confluence.slac.stanford.edu/display/PSDM/Data+Formats
	all_files = [f for f in os.listdir(path) if f[0]!='.']
	if dataformat.lower() == "xtc":
		run_num = findnumber(runname)[0]
		streams = [os.path.join(path,s) for s in all_files if os.path.isfile(os.path.join(path, s)) \
					and s.split('.')[-1].lower() == dataformat.lower() and findnumber(s)[1] == run_num]
	else:
		streams = [os.path.join(path,s) for s in all_files if os.path.isfile(os.path.join(path, s)) \
					and s.split('.')[-1].lower() == dataformat.lower()]
	return streams


def write_config(file, dict, mode='w'):
	if mode=='w' and os.path.exists(file):
		os.remove(file)
	config = ConfigParser()
	config.read(file)
	sections = config.sections()
	for key, val in dict.items():
		if key not in sections:
			config.add_section(key)
		for k,v in val.items():
			config.set(key, k, v)
	f = open(file, 'w')
	config.write(f)
	f.close()


def read_config(file, item=None):
	config = ConfigParser()
	config.read(file)
	if item is not None:
		return config.get(item[0], item[1])
	else:
		return config


def findnumber(string):
	return re.findall(r"\d+\.?\d*", string)


def logging_table(info_dict, changelog_dict, processdir):
	path = os.path.join(processdir, 'table.info')
	with open(path, 'w') as outfile:
		json.dump(info_dict, outfile)
	path = os.path.join(processdir, 'table.change')
	with open(path, 'w') as outfile:
		json.dump(changelog_dict, outfile)


def load_changelog(processdir):
	path = os.path.join(processdir, 'table.change')
	info = {}
	if os.path.isfile(path):
		try:
			with open(path, 'r') as readfile:
				info = json.load(readfile)
		except:
			pass
	return info


def read_ini():
	conf = ConfigParser()
	conf.read("app_namespace.ini")
	namespace = {}
	namespace['ini'] = conf.get('start', 'appini')
	namespace['log'] = conf.get('start', 'applog')
	namespace['project_structure'] = conf.get('start', 'project_structure').split(',')
	namespace['project_ini'] = conf.get('start', 'project_ini').split(':')
	namespace['JSS_support'] = conf.get('start', 'JSS_support').split(',')
	namespace['monitor_time'] = conf.getfloat('start', 'monitor_time')
	namespace['config_head'] = conf.get('start', 'config_head')
	namespace['data_format'] = conf.get('start', 'data_format').split(',')
	namespace['process_assignments'] = conf.get('process', 'assignments').split(',')
	namespace['process_status'] = conf.get('process', 'status').split(',')
	namespace['process_pat_per_job'] = conf.getint('process', 'pat_per_job')
	namespace['max_jobs_per_file'] = conf.getint('process', 'max_jobs_per_file')
	process_colors = conf.get('process', 'colors').split(',')
	namespace['process_colors'] = [[0,0,0]]*len(process_colors)
	for i,cl in enumerate(process_colors):
		tmp = cl.split('.')
		namespace['process_colors'][i] = [int(tmp[0]),int(tmp[1]),int(tmp[2])]
	namespace['darkcal'] = conf.get('process', 'darkcal')
	namespace['classify_decomp'] = conf.get('classify', 'decomp').split(',')
	namespace['merge_sym'] = conf.get('merge', 'sym').split(',')
	namespace['phasing_method'] = conf.get('phasing', 'method').split(',')
	# now add function nickname
	namespace['process_HF'] = conf.get('process', 'HF')
	namespace['process_FA'] = conf.get('process', 'FA')
	namespace['process_FAA'] = conf.get('process', 'FAA')
	namespace['process_AP'] = conf.get('process', 'AP')
	namespace['process_DEC'] = "decomp"
	namespace['process_TSNE'] = "tsne"
	namespace['process_MRG'] = "merge"
	namespace['process_PHS'] = "phasing"
	namespace['classify_SVD'] = conf.get('classify', 'SVD')
	namespace['classify_LLE'] = conf.get('classify', 'LLE')
	namespace['classify_SPEM'] = conf.get('classify', 'SPEM')
	namespace['classify_TSNE'] = conf.get('classify', 'TSNE')
	namespace['phasing_RAAR'] = conf.get('phasing', 'RAAR')
	namespace['phasing_DM'] = conf.get('phasing', 'DM')
	namespace['phasing_ERA'] = conf.get('phasing', 'ERA')
	namespace['merge_ICOSYM'] = conf.get('merge', 'ICOSYM')
	return namespace

