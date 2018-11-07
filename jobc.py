from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtWebKit

import sys
import os
import glob
import subprocess
import threading
import json
import random
import Queue

import utils
from run_gui import Ui_Run_Dialog

"""
job struct, should contain:
	assignments
	run_name
	run_tag
	config
	pid
	status
	savepath
	stime
"""
class ajob:

	def __init__(self, thetype, run_name, run_tag, config, pid, status, savepath, stime):
		self.assignments = thetype
		self.run_name = run_name
		self.run_tag = run_tag
		self.config = config
		self.pid = pid
		self.status = status
		self.savepath = savepath
		self.submit_time = stime



class JobCenter(QtGui.QDialog, QtCore.QEvent):

	# job status
	SUB = ""
	RUN = ""
	ERR = ""
	FIN = ""
	TER = ""
	JOBQMAX = 10000

	def __init__(self, jss, project_root):
		QtGui.QWidget.__init__(self)
		# setup ui
		self.ui = Ui_Run_Dialog()
		self.ui.setupUi(self)
		# dict, structure is "jid : ajob"
		self.jobs = {}
		# dict, {run_name : jid}
		self.run_view = {}
		# dict, store jid of waiting jobs, submitted jobs and returned jobs
		self.job_queue = {'waiting':Queue.Queue(JobCenter.JOBQMAX), \
		'submitted':Queue.Queue(JobCenter.JOBQMAX), 'returned':Queue.Queue(JobCenter.JOBQMAX)}

		self.jss = jss
		self.rootdir = project_root
		self.namespace = utils.read_ini()
		JobCenter.SUB = self.namespace['process_status'][7]
		JobCenter.RUN = self.namespace['process_status'][1]
		JobCenter.ERR = self.namespace['process_status'][3]
		JobCenter.FIN = self.namespace['process_status'][2]
		JobCenter.TER = self.namespace['process_status'][4]
		# job hub file
		self.load_job_hub()
		# triggers
		# self.ui.comboBox.currentIndexChanged.connect(self.tag_changed)
		self.connect(self.ui.pushButton, QtCore.SIGNAL(("clicked()")), self.darkcal_dir)
		self.connect(self.ui.pushButton_3, QtCore.SIGNAL(("clicked()")), self.run)
		self.connect(self.ui.pushButton_2, QtCore.SIGNAL(("clicked()")), self.cancel)


	def get_config_path(self, module, assignments, tagname=None):
		if tagname is None:
			return glob.glob(os.path.join(os.path.join(self.rootdir, module), 'config/%s_*' % assignments))
		else:
			return glob.glob(os.path.join(os.path.join(self.rootdir, module), 'config/%s_%s.ini' % (assignments, tagname)))


	def extract_tag(self, tagfilename):
		return tagfilename.split("_")[-1].split('.ini')[0]


	def write_job_hub(self):
		with open(os.path.join(self.rootdir, "JobHub.txt"), 'a+') as f:
			for jid in self.jobs.keys():
				job = self.jobs[jid]
				f.write("\n")
				f.write("jid         = %s \n" % str(jid))
				f.write("assignments = %s \n" % a.assignments)
				f.write("run_name    = %s \n" % a.run_name)
				f.write("run_tag     = %s \n" % a.run_tag)
				f.write("config      = %s \n" % a.config)
				f.write("status      = %s \n" % a.status)
				f.write("savepath    = %s \n" % a.savepath)
				f.write("submission  = %s \n" % a.submit_time)


	def load_job_hub(self):
		if not os.path.exists(os.path.join(self.rootdir, "JobHub.txt")):
			f = open(os.path.join(self.rootdir, "JobHub.txt"), 'w')
			f.close()
		else:
			jid = None
			with open(os.path.join(self.rootdir, "JobHub.txt"), 'r') as f:
				for line in f.readlines():
					line = line.strip('\n')
					if "jid" in line:
						jid = int(line.split("=")[-1].strip())
						self.jobs[jid] = ajob(None, None, None, None, None, None, None, None)
					elif "assignments" in line:
						self.jobs[jid].assignments = line.split("=")[-1].strip()
					elif "run_name" in line:
						self.jobs[jid].run_name = line.split("=")[-1].strip()
						self.run_view[run_name] = jid
					elif "run_tag" in line:
						self.jobs[jid].run_tag = line.split("=")[-1].strip()
					elif "config" in line:
						self.jobs[jid].config = line.split("=")[-1].strip()
					elif "status" in line:
						self.jobs[jid].status = line.split("=")[-1].strip()
					elif "savepath" in line:
						self.jobs[jid].savepath = line.split("=")[-1].strip()
					elif "submission" in line:
						self.jobs[jid].submission = line.split("=")[-1].strip()
					else:
						pass



	"""
		Events of table's pop-window ,
		from TableRun_showoff()
	"""


	def TableRun_showoff(self, job_type, run_names):
		# only 'Process' module needs to call this function
		# job_type:
		#	(e.g.) Process/Hit-Finding

		module, assg = job_type.split('/')
		# add param tag
		if self.namespace['process_HF'] == assg:
			self.ui.comboBox.addItem("darkcal")
		params_tags = self.get_config_path(module, assg)
		for tag in params_tags:
			self.ui.comboBox.addItem(os.path.split(tag)[-1])

		for run_name in run_names:
			# generate an id
			while True:
				jid = random.randint(100000, 1000000)
				if not self.jobs.has_key(jid):
					break

			jobdir = os.path.join(self.rootdir, job_type, run_name)
			self.jobs[jid] = ajob(assg, run_name, None, None, None, JobCenter.SUB, jobdir, None)
			
			# hit-finding has darkcal
			if assg == self.namespace['process_HF']:
				darkcal_file = os.path.join(jobdir, self.namespace['darkcal'])
				if os.path.exists(darkcal_file):
					self.ui.lineEdit_2.setText(darkcal_file)
				else:
					self.ui.lineEdit_2.setText("404 Not Found.  browser-->")
			else:
				self.ui.lineEdit_2.setVisible(False)
			# push in job_queue['waiting']
			self.job_queue['waiting'].put(jid)
	
		# show modal
		self.setWindowTitle("Run %s" % assg)
		self.setModal(True)
		self.show()
		


	def darkcal_dir(self):
		h5file = str(QtGui.QFileDialog(self).getOpenFileName(None, "Select darkcal (h5) file to open", "", "DARKCAL (*.h5)"))
		self.ui.lineEdit_2.setText(h5file)


	def run(self):
		# TODO
		# update self.run_view
		# update run_tag, config, pid, stime in self.jobs
		self.close()
		pass


	def cancel(self):
		while not self.job_queue['waiting'].empty():
			jid = self.job_queue['waiting'].get()
			tmp = self.jobs.pop(jid)
			del tmp
		self.close()


	"""
		End of this part
	"""


	def update_status(self, run_name=None):
		# TODO
		# update job status
		utils.print2projectLog(self.rootdir, "Job center updated")
		pass


	def get_run_status(self, run_name, assg, tag):
		# get status of job of run
		if not self.run_view.has_key(run_name):
			return None
		jids = self.run_view[run_name]
		for jid in jids:
			if self.jobs[jid].assignments == assg and self.jobs[jid].run_tag == tag:
				return self.jobs[jid].status


	def packSubmit(self, config_dict):
		# choose correct code blocks to run according to the given job type
		if job_type == self.namespace['process_HF']:
			# hit-finding
			runtime = {}
			runtime['run_name'] = job_name
