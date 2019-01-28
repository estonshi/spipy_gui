from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtWebKit
from main_gui import Ui_MainWindow

import sys
import os
import subprocess
import glob
from ConfigParser import ConfigParser
from functools import partial

import utils
import process
import jobc
import jobview
import chosebox
import data_viewer.data_viewer as data_viewer


class SPIPY_MAIN(QtGui.QMainWindow, QtCore.QEvent):

	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)
		# setup ui
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		# read namespace
		self.namespace = utils.read_ini()
		# other attributes
		self.dirname = None
		self.datapath = None
		self.jss = None           # None, or PBS/LSF
		self.datapathtype = True  # True: dir--runs_dir--datafile  False: dir--datafile
		self.data_format = None  # see self.namespace['data_format']
		self.num_running_jobs = 0
		# process_data is table infomation, the keys are run number, and first column stores raw data path
		# , other columns are consistent with tableWidget
		self.columnCount = self.ui.tableWidget.columnCount()
		self.process_data = None
		self.rawdata_changelog = None
		self.JobCenter = None
		# tag_buffer is {assignments:{run_name:tag_remarks}, ...}
		self.tag_buffer = None
		# setup triggers
		self.ui.tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
		self.ui.comboBox_2.currentIndexChanged.connect(self.js_changed)
		self.ui.comboBox.currentIndexChanged.connect(self.assignments_changed)
		self.ui.comboBox_3.currentIndexChanged.connect(self.decomp_changed)
		self.ui.pushButton.clicked.connect(self.view_job)
		# self.ui.pushButton_2.clicked.connect(self.view_history)
		self.ui.pushButton_3.clicked.connect(partial(process.parameters_setting, self))
		self.ui.pushButton_6.clicked.connect(self.refresh_table)
		self.ui.checkBox_3.stateChanged.connect(self.autorefresh)
		self.ui.tableWidget.customContextMenuRequested.connect(self.table_menu)
		self.ui.tableWidget.cellDoubleClicked.connect(self.cell_dclicked)


	def setup(self, workpath, datapath, jss, datapathtype, format_index):
		self.jss = jss
		self.dirname = workpath
		self.datapath = datapath
		self.datapathtype = datapathtype
		self.data_format = self.namespace['data_format'][format_index]
		# setup job center
		self.JobCenter = jobc.JobCenter(self.jss, self.dirname, self.data_format, self)
		# load table
		self.process_data = utils.load_table(os.path.join(self.dirname, self.namespace['project_structure'][0]))
		# load table change log, if there exists
		self.rawdata_changelog = utils.load_changelog(os.path.join(self.dirname, self.namespace['project_structure'][0]))
		# set up tag_buffer
		self.tag_buffer = {}
		for assm in self.namespace['process_assignments']:
			self.tag_buffer[assm] = {}
		# write jss to UI
		if self.jss is not None:
			self.ui.comboBox_2.addItem(self.jss)
		# setup all tabWidgets
		# setup process
		for assm in self.namespace['process_assignments']:
			self.ui.comboBox.addItem(assm)
		self.ui.tableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
		self.ui.label_73.setText( utils.fmt_process_status(self.data_format) )
		self.ui.pushButton_2.setVisible(False)
		# setup classify
		for decp in self.namespace['classify_decomp']:
			self.ui.comboBox_3.addItem(decp)
		self.ui.lineEdit.setText(os.path.join(os.path.join(self.dirname, \
			self.namespace['project_structure'][0]), self.namespace['process_HF']))
		self.ui.lineEdit_2.setText("Hits/data")
		self.ui.widget_12.setVisible(False)
		self.ui.widget_11.setVisible(False)
		# setup merge
		for sym in self.namespace['merge_sym']:
			self.ui.comboBox_5.addItem(sym)
		# setup phasing
		for method in self.namespace['phasing_method']:
			self.ui.comboBox_9.addItem(method)
			self.ui.comboBox_10.addItem(method)
			self.ui.comboBox_11.addItem(method)
		# setup monitors
		self.table_monitor = None
		# draw table
		self.refresh_table()


	def closeEvent(self, event):
		#self.JobCenter.write_job_hub()
		utils.print2projectLog(self.dirname, "Close spipy GUI.")
		QtGui.qApp.quit()


	def js_changed(self, index):
		if self.ui.comboBox_2.itemText(index) == "PBS":
			if not utils.check_PBS():
				utils.show_message("No PBS detected !")
				self.ui.comboBox_2.setCurrentIndex(0)
			else:
				self.jss = str(self.ui.comboBox_2.currentText())
		else:
			pass
		self.JobCenter.setjss(self.jss)


	"""
		Process Tab
	"""

	#  -----------------------------------  #
	#  tag remarks format processing start  #
	#  run folder name format:
	#		.../run.tag.remarks/...
	#  ------------------------------------ #

	def get_existing_runtags(self, assignments, run_name):
		'''
		return [['tag','remarks'], ...]
		'''
		module_name = self.namespace['project_structure'][0]
		path = os.path.join(self.dirname, module_name, '%s/%s.*' % (assignments, run_name))
		tags = glob.glob(path)
		tags = [os.path.split(tmp)[-1].split('.')[1:] for tmp in tags]
		return tags


	def get_latest_runtag(self, assignments, run_name):
		'''
		return ['tag','remarks']
		'''
		module_name = self.namespace['project_structure'][0]
		path = os.path.join(self.dirname, module_name, '%s/%s.*' % (assignments, run_name))
		tags = glob.glob(path)
		latest = "--"
		time = 0
		for tag in tags:
			timestamp = os.path.getmtime(tag)
			if timestamp > time:
				time = timestamp
				latest = tag
		if latest == "--":
			return latest
		else:
			return os.path.split(latest)[-1].split('.')[1:]


	def is_existed_runtag(self, assignments, run_name, run_tag_remarks):
		try:
			tag, remarks = self.split_tag_remarks(run_tag_remarks)
		except:
			return False
		module_name = self.namespace['project_structure'][0]
		path = os.path.join(self.dirname, module_name, '%s/%s.%s.%s' % (assignments, run_name, tag, remarks))
		if os.path.isdir(path):
			return True
		else:
			return False


	def combine_tag_remarks(self, tag_remarks):
		if type(tag_remarks) == str:
			return tag_remarks
		else:
			return tag_remarks[0] + '.' + tag_remarks[1]


	def split_tag_remarks(self, tag_remarks):
		return tag_remarks.split('.')

	#  ---------------------------------  #
	#  tag remarks format processing end  #
	#  ---------------------------------  #


	def assignments_changed(self, index):
		# change combobox in table
		# refresh table ?
		self.refresh_table()


	def cell_dclicked(self, row, column):
		'''table cell double clicked
			run tag changing
		'''
		if column != 1:
			return
		assignments = str(self.ui.comboBox.currentText())
		#if assignments != self.namespace['process_HF']:
		#	return
		run_name = str(self.ui.tableWidget.item(row, 0).text())
		run_tag_remarks = self.get_existing_runtags(assignments, run_name)
		choices = []
		for tmp in run_tag_remarks:
			choices.append(self.combine_tag_remarks(tmp))
		ret = [None]
		chosebox.show_chosebox("Tags", choices, ret, "%s.%s" % (run_name, assignments))
		if ret[0] is not None:
			self.process_data[run_name][1] = choices[ret[0]]
			self.draw_table(sel_rows = [row])


	def table_menu(self, position):
		"""
		entrance to submit jobs
		"""
		# selected cells
		selected_runs = []
		selected_tag_remarks = {}
		selected_datafile = {}
		for pos in self.ui.tableWidget.selectionModel().selection().indexes():
			row = pos.row()
			run_name = str(self.ui.tableWidget.item(row, 0).text())
			if len(self.process_data[run_name][0]) == 0:
				utils.show_message("Run %s does not contain any data. Skip." % run_name)
				continue
			tag_remarks_name = str(self.ui.tableWidget.item(row, 1).text())
			selected_runs.append(run_name)
			selected_tag_remarks[run_name] = self.split_tag_remarks(tag_remarks_name)
			selected_datafile[run_name] = self.process_data[run_name][0]

		# show menu
		if len(selected_runs) > 0:
			# get assignments
			assignments = str(self.ui.comboBox.currentText())
			# show menu
			menu = QtGui.QMenu()
			a1 = menu.addAction("Run %s" % assignments)
			menu.addSeparator()
			# a2 = menu.addAction("Terminate all")
			menu_sub = menu.addMenu("Terminate")
			b = []
			if len(selected_runs) > 1:
				for assign in self.namespace['process_assignments']:
					b.append(menu_sub.addAction(assign))
				if selected_tag_remarks[selected_runs[0]][0] != "--":
					menu.addSeparator()
					a4 = menu.addAction("Open %s results in data viewer" % assignments)
			elif len(selected_runs) == 1:
				run_tag_remarks = self.get_existing_runtags(assignments, selected_runs[0])
				for tr in run_tag_remarks:
					tr_status = self.JobCenter.get_run_status(selected_runs[0], self.namespace['project_structure'][0], assignments, tr[0], tr[1])
					if tr_status == self.JobCenter.RUN:
						b.append( menu_sub.addAction("%s.%s.%s.%s" % (assignments, selected_runs[0], tr[0], tr[1])) )
				menu.addSeparator()
				if selected_tag_remarks[selected_runs[0]][0] == "darkcal":
					a4 = menu.addAction("Set as current darkcal")
				elif selected_tag_remarks[selected_runs[0]][0] != "--":
					a4 = menu.addAction("Open %s results in data viewer" % assignments)
				else:
					a4 = 0
			else:
				pass

			# exec
			action = menu.exec_(self.ui.tableWidget.mapToGlobal(position))

			# parse selection
			job_type  = self.namespace['project_structure'][0] + "/" + assignments

			if action == a1:
				utils.print2projectLog(self.dirname, "Choose %s on %s" % (assignments, str(selected_runs)))
				self.JobCenter.TableRun_showoff(job_type, selected_runs, selected_datafile, selected_tag_remarks)
			#elif action == a2:
			#	print("Terminate all jobs of %s" % str(selected_runs))
			elif len(selected_runs) == 1 and action == a4:
				if selected_tag_remarks[selected_runs[0]][0] == "darkcal":
					# re-link current-darkcal.h5
					tmp_darkfile = utils.fmt_job_dir(selected_runs[0], \
						selected_tag_remarks[selected_runs[0]][0], selected_tag_remarks[selected_runs[0]][1])
					tmp_darkfile = os.path.join(self.dirname, self.namespace['project_structure'][0], self.namespace['process_HF'], tmp_darkfile)
					try:
						tmp_darkfile = glob.glob(os.path.join(tmp_darkfile, "*darkcal.h5"))[0]
					except:
						utils.show_message("I cannot find ?.darkcal.h5 in this run. Fail to set current darkcal.")
						return
					tmp_curr_darklink = os.path.join(self.dirname, self.namespace['project_structure'][0], self.namespace['process_HF'], self.namespace['darkcal'])
					prev_dark_run = None
					if os.path.exists(tmp_curr_darklink):
						prev_dark_run = subprocess.check_output("ls -l %s | awk -F'->' '{print $2}' | tr -d ' '" % tmp_curr_darklink, shell=True)
						prev_dark_run = os.path.split(prev_dark_run.strip("\n"))[-1].split('.')[0]
					subprocess.check_call("ln -fs %s %s" % (tmp_darkfile, tmp_curr_darklink), shell=True)
					# refresh table info
					if prev_dark_run is not None:
						self.process_data[prev_dark_run][6] = "--"
					self.process_data[selected_runs[0]][6] = "Current-Darkcal"
					utils.print2projectLog(self.dirname, "Set %s as current darkcal" % selected_runs[0])
					# draw table
					self.draw_table()
				else:
					# open data viewer and add files
					tmp = utils.fmt_job_dir(selected_runs[0], \
						selected_tag_remarks[selected_runs[0]][0], selected_tag_remarks[selected_runs[0]][1])
					tmp = os.path.join(self.dirname, self.namespace['project_structure'][0], assignments, tmp, '*.h5')
					tmp = glob.glob(tmp)
					if not data_viewer.is_shown():
						data_viewer.show_data_viewer(self)
					data_viewer.add_files(tmp)
					utils.print2projectLog(self.dirname, "Add %s results of %s to data viewer." % (assignments, selected_runs[0]))
			elif len(selected_runs) == 1 and action in b:
				tmp = str(action.text()).split('.')
				jid = self.JobCenter.get_jid(tmp[0], tmp[1], tmp[2], tmp[3])
				re = utils.show_warning("Terminate job %d of %s ?" % (jid, str(selected_runs)))
				if re == 1:
					tmp = self.JobCenter.kill_job(jid)
					if tmp[0] == 1:
						utils.print2projectLog(self.dirname, "Terminate job %d of %s" % (jid, str(selected_runs)))
						utils.show_message("Job %s is successfully terminated" % str(action.text()))
					else:
						utils.print2projectLog(self.dirname, "Fail to terminate job %d of %s" % (jid, str(selected_runs)))
						utils.show_message("**FAIL** to terminate job !" % str(action.text()))
					# refresh
					self.update_table_runs()
					self.draw_table()
			elif len(selected_runs) > 1 and action in b:
				assign = str(action.text())
				all_jid = []
				for run_name in selected_runs:
					tag_remarks = self.get_existing_runtags(assign, run_name)
					for tr in tag_remarks:
						tr_status = self.JobCenter.get_run_status(run_name, self.namespace['project_structure'][0], assign, tr[0], tr[1])
						if tr_status == self.JobCenter.RUN:
							tmp_jid = self.JobCenter.run_view[utils.fmt_runview_key(assign, run_name, tr[0], tr[1])]
							all_jid.append(tmp_jid)
				re = utils.show_warning("Terminate all these %d jobs ?" % len(all_jid))
				if re == 1:
					killed = 0
					for tmp_jid in all_jid:
						killed += self.JobCenter.kill_job(jid)
					utils.print2projectLog("Terminate %d %s jobs of %s" % (killed, assign, str(selected_runs)))
					utils.show_message("Successfully terminate %d jobs" % killed)
					# refresh
					self.update_table_runs()
					self.draw_table()
			elif len(selected_runs) > 1 and action == a4:
				if not data_viewer.is_shown():
					data_viewer.show_data_viewer(self)
				for selected_run in selected_runs:
					tmp = utils.fmt_job_dir(selected_run, \
						selected_tag_remarks[selected_run][0], selected_tag_remarks[selected_run][1])
					tmp = os.path.join(self.dirname, self.namespace['project_structure'][0], assignments, tmp, '*.h5')
					tmp = glob.glob(tmp)
					data_viewer.add_files(tmp)
				utils.print2projectLog(self.dirname, "Add %s results of %s to data viewer." % (assignments, str(selected_runs)))
			else:
				pass
		else:
			menu = QtGui.QMenu()
			if self.ui.tableWidget.horizontalHeader().resizeMode(0) == QtGui.QHeaderView.Stretch:
				a1 = menu.addAction("Unfill table window")	
			else:
				a1 = menu.addAction("Fill table window")
			menu.addSeparator()
			a2 = menu.addAction("Set 'force overwrite' to %s" % str(not self.JobCenter.force_overwrite))

			action = menu.exec_(self.ui.tableWidget.mapToGlobal(position))
			if action == a1:
				if self.ui.tableWidget.horizontalHeader().resizeMode(0) == QtGui.QHeaderView.Stretch:
					self.ui.tableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
				else:
					self.ui.tableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
			elif action == a2:
				self.JobCenter.reverseForceOverwrite()
			else:
				pass


	def update_table_runs(self):
		if not os.path.isdir(self.datapath):
			utils.show_message("Data directory is invalid, please reopen the software.")
			return

		# subdir ?
		if not self.datapathtype:
			all_in_dir = utils.parse_multi_runs_nosubdir(self.datapath, self.data_format)
		else:
			all_in_dir = [f for f in os.listdir(self.datapath) if "." not in f and f[0]!="$" \
									and os.path.isdir(os.path.join(self.datapath, f))]

		prev_runs = self.process_data.keys()
		prev_runs_checked = [0] * len(prev_runs)
		run_name = ""
		run_streams_num = "0"

		# go through alll files/dirs
		# detect raw data status
		for d in all_in_dir:
			# parse run name
			if not self.datapathtype:
				tmp = d.split("?_?^=^")  # this magic code, defined in utils.parse_multi_runs_nosubdir
				run_name = tmp[0]
				run_streams_num = tmp[1]
			else:
				run_name = d
			# check avaliable
			if run_name not in prev_runs:
				# init process_data & rawdata_changelog
				self.process_data[run_name] = ['--'] * self.columnCount
				self.rawdata_changelog[run_name] = {}
				# update process_data
				if not self.datapathtype:
					self.process_data[run_name][0] = utils.parse_multi_run_streams(self.datapath, run_name, self.data_format, False)
					self.process_data[run_name][2] = self.namespace['process_status'][0] + " (%s)" % run_streams_num
				else:
					subpath = os.path.join(self.datapath, d)
					datafile = utils.parse_multi_run_streams(subpath, run_name, self.data_format)
					if len(datafile) >= 1:
						self.process_data[run_name][0] = datafile
						run_streams_num = str(len(datafile))
						self.process_data[run_name][2] = self.namespace['process_status'][0] + " (%s)" % run_streams_num
					else:
						self.process_data[run_name][0] = []
						self.process_data[run_name][2] = self.namespace['process_status'][5]
			else:
				prevdatafile = self.process_data[run_name][0]
				if not self.datapathtype:
					datafile = utils.parse_multi_run_streams(self.datapath, run_name, self.data_format, False)
					run_streams_num = str(len(datafile))
					if len(datafile) == 0:                                            # deleted
						tmp = self.process_data.pop(run_name)
						self.rawdata_changelog[run_name].update(utils.rawdata_changelog(prevdatafile, None))
					elif len( (set(datafile) | set(prevdatafile)) - (set(datafile) & set(prevdatafile)) ) != 0:           # changed
						self.process_data[run_name][2] = self.namespace['process_status'][6] + " (%s)" % run_streams_num
						self.process_data[run_name][0] = datafile
						self.rawdata_changelog[run_name].update(utils.rawdata_changelog(prevdatafile, datafile))
					else:                                                             # stays still
						self.process_data[run_name][2] = self.namespace['process_status'][0] + " (%s)" % run_streams_num
						self.process_data[run_name][0] = datafile
				else:
					subpath = os.path.join(self.datapath, d)
					datafile = utils.parse_multi_run_streams(subpath, run_name, self.data_format)
					run_streams_num = str(len(datafile))
					if len(datafile) == 0:                                            # no data
						self.process_data[run_name][0] = []
						self.process_data[run_name][2] = self.namespace['process_status'][5]
						self.rawdata_changelog[run_name].update(utils.rawdata_changelog(prevdatafile, None))
					elif len( (set(datafile) | set(prevdatafile)) - (set(datafile) & set(prevdatafile)) ) != 0:           # changed
						self.process_data[run_name][2] = self.namespace['process_status'][6] + " (%s)" % run_streams_num
						self.process_data[run_name][0] = datafile
						self.rawdata_changelog[run_name].update(utils.rawdata_changelog(prevdatafile, datafile))
					else:                                                             # stays still
						self.process_data[run_name][2] = self.namespace['process_status'][0] + " (%s)" % run_streams_num
						self.process_data[run_name][0] = datafile

				prev_runs_checked[prev_runs.index(run_name)] = 1

		for i,c in enumerate(prev_runs_checked):
			if c == 0 :
				run_name = prev_runs[i]
				tmp = self.process_data.pop(run_name)
				self.rawdata_changelog[run_name].update(utils.rawdata_changelog(tmp[0], "This run is Deleted"))

		# go through all job dir
		# detect job status
		# self.process_data[run_name][1] shows only hit-finding
		prev_runs = self.process_data.keys()
		hf_module = self.namespace['project_structure'][0]
		self.num_running_jobs = 0
		for i,run_name in enumerate(prev_runs):
			self.process_data[run_name][3:6] = ['--'] * 3
			# get tag
			# assignments = self.namespace['process_HF']
			assignments = str(self.ui.comboBox.currentText())
			if not (self.tag_buffer[assignments].has_key(run_name) and self.is_existed_runtag(assignments, run_name, self.tag_buffer[assignments][run_name])):
				tag_remarks = self.get_latest_runtag(str(assignments), run_name)
				self.process_data[run_name][1] = self.combine_tag_remarks(tag_remarks)
			else:
				self.process_data[run_name][1] = self.tag_buffer[assignments][run_name]
			# get jobs status
			for aindex in range(self.ui.comboBox.count()):
				assignments_tmp = str(self.ui.comboBox.itemText(aindex))
				# get tag from processe_data or tag_buffer or fresh data ?
				if assignments_tmp == assignments:
					tag_remarks = self.split_tag_remarks(self.process_data[run_name][1])
				else:
					try:
						tag_remarks = self.split_tag_remarks(self.tag_buffer[assignments_tmp][run_name])
					except:
						tag_remarks = self.get_latest_runtag(assignments_tmp, run_name)
				# tag_remarks is ['tag','remarks']
				if type(tag_remarks) != list or len(tag_remarks) != 2:
					continue
				job_status = self.JobCenter.get_run_status(run_name, hf_module, assignments_tmp, tag_remarks[0], tag_remarks[1])
				if job_status is None:
					job_status = "--"
				elif job_status == self.JobCenter.RUN:
					self.num_running_jobs += 1
				else:
					pass
				if assignments_tmp == self.namespace['process_HF']:
					self.process_data[run_name][3] = job_status
				elif assignments_tmp == self.namespace['process_FA']:
					self.process_data[run_name][4] = job_status
				elif assignments_tmp == self.namespace['process_FAA']:
					self.process_data[run_name][4] = job_status
				elif assignments_tmp == self.namespace['process_AP']:
					self.process_data[run_name][5] = job_status
				else:
					pass
			# get hit rate
			# output status format : see scripts/HitFinder.py
			if assignments != self.namespace['process_HF']:
				try:
					tag_remarks = self.tag_buffer[self.namespace['process_HF']][run_name]
					tag_remarks = self.split_tag_remarks(tag_remarks)
				except:
					tag_remarks = '--'
			else:
				tag_remarks = self.split_tag_remarks(self.process_data[run_name][1])
			if type(tag_remarks) != list or len(tag_remarks) < 2:
				self.process_data[run_name][6] = '--'
				continue
			elif tag_remarks[0].lower() == "darkcal":
				if self.process_data[run_name][6] != "Current-Darkcal":
					self.process_data[run_name][6] = '--'
				continue
			hf_status = os.path.join(self.dirname, hf_module, '%s/%s.%s.%s/status' % \
				(self.namespace['process_HF'], run_name, tag_remarks[0], tag_remarks[1]))
			if not os.path.isdir(hf_status):
				self.process_data[run_name][6] = '--'
				continue
			elif os.path.exists(os.path.join(hf_status, 'summary.txt')):
				summary = utils.read_status(os.path.join(hf_status, 'summary.txt'))
				thishits = int(summary['hits'])
				thisprocessed = int(summary['processed'])
				self.process_data[run_name][6] = "%.2f%% (%d/%d)" % (100*float(thishits)/(thisprocessed+1e-6), thishits, thisprocessed)
			else:
				status_files = glob.glob(os.path.join(hf_status, 'status*'))
				thishits = 0
				thisprocessed = 0
				for status_file in status_files:
					summary = utils.read_status(status_file)
					thishits += int(summary['hits'])
					thisprocessed += int(summary['processed'])
				self.process_data[run_name][6] = "%.2f%% (%d/%d)" % (100*float(thishits)/(thisprocessed+1e-6), thishits, thisprocessed)


	def draw_table(self, sel_rows = None):
		# sel_rows : [row1, row2 , ...]
		'''NOTE
		If sel_rows is not None, then only the ROWs in sel_rows will be updated.
		Please make sure no rows are added or deleted in self.process_data if sel_rows is not None ! 
		'''
		runs = self.process_data.keys()
		runs.sort()
		hits = 0
		patterns = 0
		for i,r in enumerate(runs):
			infomation = self.process_data[r]
			# cal hits and patterns
			hitinfo = utils.findnumber(infomation[6])
			if len(hitinfo) == 3:
				hits += int(hitinfo[1])
				patterns += int(hitinfo[2])
			# judge if it is selected
			if sel_rows is not None and i not in sel_rows :
				continue				
			# insert row ?
			if i >= self.ui.tableWidget.rowCount():
				self.ui.tableWidget.insertRow(i)
			# set run name
			newitem = QtGui.QTableWidgetItem(str(r))
			newitem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
			self.ui.tableWidget.setItem(i, 0, newitem)
			# set others
			for j,info in enumerate(infomation[1:self.columnCount]):
				j = j + 1
				newitem = QtGui.QTableWidgetItem(info)
				if j == 1:
					assignments = str(self.ui.comboBox.currentText())
					self.tag_buffer[assignments][r] = info
				if j in [2,3,4,5] and info != "--":
					cindex = self.namespace['process_status'].index(info.split(" ")[0])
					color = self.namespace['process_colors'][cindex]
					newitem.setBackgroundColor(QtGui.QColor(color[0], color[1], color[2], 127))
				newitem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
				self.ui.tableWidget.setItem(i, j, newitem)
		# write other ctrls
		self.ui.label_73.setText( utils.fmt_process_status(self.data_format, hits, patterns) )
		self.ui.lcdNumber.display(self.num_running_jobs)
		# logging table
		utils.logging_table(self.process_data, self.rawdata_changelog, \
				os.path.join(self.dirname, self.namespace['project_structure'][0]))


	def refresh_table(self):
		# lock button
		self.ui.pushButton_6.setEnabled(False)
		# refresh
		self.update_table_runs()
		self.draw_table()
		# utils.print2projectLog(self.dirname, "Table updated.")
		# unlock button
		self.ui.pushButton_6.setEnabled(True)


	def autorefresh(self, state):
		if state == QtCore.Qt.Checked:
			self.table_monitor = utils.TableMonitor(self.namespace['monitor_time'], self.refresh_table)
			self.refresh_table()
			self.table_monitor.start()
		else:
			self.table_monitor.stop()
			del self.table_monitor
			self.table_monitor = None



	"""
		Classify Tab
	"""

	def decomp_changed(self, index):
		if self.ui.comboBox_3.itemText(index) == self.namespace['classify_LLE']:
			self.ui.widget_11.setVisible(True)
			self.ui.widget_12.setVisible(True)
		else:
			self.ui.widget_11.setVisible(False)
			self.ui.widget_12.setVisible(False)



	def view_job(self):
		jobview.show_jobView(self)
		utils.print2projectLog(self.dirname, "Open job viewer.")


	def view_history(self):
		pass



	'''
		Merge Tab
	'''

	





if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    myapp = SPIPY_MAIN()
    myapp.setup('./','PBS')
    myapp.show()
    app.exec_()