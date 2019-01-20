from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtWebKit

import sys
import os
import glob
import subprocess
from ConfigParser import ConfigParser
from functools import partial

import utils
from jobview_gui import Ui_jobView

jv = None

class jobView(QtGui.QMainWindow, QtCore.QEvent):

	log_refresh_interval = 1000   # ms

	def __init__(self, mainwindow):
		QtGui.QWidget.__init__(self, mainwindow)
		# setup ui
		self.ui = Ui_jobView()
		self.ui.setupUi(self)
		# parents
		self.mainwindow = mainwindow
		# job buffer, {'run_name': [jid_1, jid_2 ,...], ...}
		self.run_job = {}
		# job jid that is loaded on log reader
		self.log_jid = None
		# timer id
		self.timer_id = None

		# trigger
		self.ui.treeWidget.itemDoubleClicked.connect(self.treeItem_clicked)
		self.ui.radioButton.toggled.connect(self.log_auto_refresh)
		self.ui.pushButton.clicked.connect(self.refresh_jobtree)
		self.ui.comboBox.currentIndexChanged.connect(self.change_log_type)


	def load_jobs(self, refresh_main = False):
		self.run_job.clear()
		self.ui.treeWidget.clear()
		run_view = self.mainwindow.JobCenter.run_view
		# get tree leaves
		for runview, jid in run_view.items():
			run_name = utils.split_runview_key(runview, "rn")
			if not self.run_job.has_key(run_name):
				self.run_job[run_name] = [jid]
			else:
				self.run_job[run_name].append(jid)
		# cmd history tag
		tree_item = QtGui.QTreeWidgetItem(self.ui.treeWidget)
		tree_item.setText(0, "command history")
		self.ui.treeWidget.addTopLevelItem(tree_item)
		self.ui.treeWidget.setItemExpanded(tree_item, True)
		# draw tree
		for run_name, jid_list in self.run_job.items():
			# top level
			tree_item = QtGui.QTreeWidgetItem(self.ui.treeWidget)
			tree_item.setText(0, run_name)
			tree_item.setText(1, str(len(jid_list))+" jobs")
			# second level
			for jid in jid_list:
				status = self.mainwindow.JobCenter.get_run_status_2(jid)
				# color
				cindex = self.mainwindow.namespace['process_status'].index(status.strip())
				color = self.mainwindow.namespace['process_colors'][cindex]
				# Item
				tmp = QtGui.QTreeWidgetItem(tree_item)
				tmp.setText(0, self.mainwindow.JobCenter.get_runviewkey(jid))
				tmp.setText(1, status)
				tmp.setBackgroundColor(1, QtGui.QColor(color[0], color[1], color[2], 127))
				# add
				tree_item.addChild(tmp)
			self.ui.treeWidget.addTopLevelItem(tree_item)
			self.ui.treeWidget.setItemExpanded(tree_item, True)
		# refresh mainwindow ?
		if refresh_main:
			self.mainwindow.refresh_table()

		return 1


	def timerEvent(self, event):
		self.__load_log(self.log_jid)


	def log_auto_refresh(self, istoggled):
		if self.timer_id is not None:
			self.killTimer(self.timer_id)
			self.timer_id = None
		if istoggled:
			self.timer_id = self.startTimer(jobView.log_refresh_interval)


	def refresh_jobtree(self):
		self.load_jobs(False)


	def __load_log(self, jid):
		# cmd history
		if jid == "command history":
			cmd = utils.readprojectLog(self.mainwindow.dirname)
			if cmd is None:
				utils.show_message("I cannot find 'project.log'.")
				return
			prev_text = self.ui.plainTextEdit.toPlainText()
			self.ui.plainTextEdit.insertPlainText("".join(cmd)[len(prev_text):])
			return
		# job logs
		try:
			savepath = self.mainwindow.JobCenter.jobs[jid].savepath
		except:
			utils.show_message("JID %s doesn't exist. Fail to load log." % str(jid) )
			return
		stdout = glob.glob(os.path.join(savepath, "*.out"))
		stderr = glob.glob(os.path.join(savepath, "*.err"))
		if len(stdout) == 0 or len(stderr) == 0:
			utils.show_message("Cannot find any log file in project %s" % runviewkey )
			return
		log_type = str(self.ui.comboBox.currentText())
		if "output" in log_type:
			with open(stdout[0]) as fp:
				lines = fp.readlines()
		else:
			with open(stderr[0]) as fp:
				lines = fp.readlines()
		prev_text = self.ui.plainTextEdit.toPlainText()
		self.ui.plainTextEdit.insertPlainText("".join(cmd)[len(prev_text):])


	def treeItem_clicked(self, citem, column):
		runviewkey = str(citem.text(0))
		if runviewkey == "command history":
			jid = "command history"
		else:
			jid = self.mainwindow.JobCenter.run_view[runviewkey]
		self.log_jid = jid
		self.log_auto_refresh(self.ui.radioButton.isChecked())
		self.__load_log(jid)


	def change_log_type(self):
		self.__load_log(self.log_jid)


	def closeEvent(self, event):
		global jv
		jv = None



def show_jobView(parents):
	global jv
	jv = jobView(parents)
	load_jobtree()
	jv.show()


def load_jobtree():
	global jv
	ret = None
	ret = jv.load_jobs(False)
	if ret is None:
		utils.show_message("Failed to refresh job tree in Job Viewer.")