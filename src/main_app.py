from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'pygui'))

import subprocess
import glob
from configparser import ConfigParser
from functools import partial

import utils
import process
import jobc
import jobview
import chosebox
import data_viewer.data_viewer as data_viewer
import job_benchmark
import menu as myMenu
from main_gui import Ui_MainWindow


class SPIPY_MAIN(QtWidgets.QMainWindow, QtCore.QEvent):

	def __init__(self, parent=None):
		QtWidgets.QWidget.__init__(self, parent)
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
		# menu
		pre_menu = self.ui.menubar.addMenu("Preference")
		pre_menu.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
		pre_menu_act1 = QtWidgets.QAction("Job Control", pre_menu)
		pre_menu_act1.setCheckable(False)
		pre_menu_act1.triggered.connect(self.set_job_control)
		pre_menu.addAction(pre_menu_act1)
		# setup triggers
		# process tab
		self.ui.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.ui.comboBox_2.currentIndexChanged.connect(self.js_changed)
		self.ui.comboBox.currentIndexChanged.connect(self.assignments_changed)
		self.ui.comboBox_3.currentIndexChanged.connect(self.decomp_changed)
		self.ui.pushButton.clicked.connect(self.view_job)
		self.ui.pushButton_3.clicked.connect(partial(process.parameters_setting, self))
		self.ui.pushButton_6.clicked.connect(self.refresh_table)
		self.ui.checkBox_3.stateChanged.connect(self.autorefresh)
		self.ui.tableWidget.customContextMenuRequested.connect(self.table_menu)
		self.ui.tableWidget.cellDoubleClicked.connect(self.cell_dclicked)
		# merge tab
		self.ui.pushButton_8.clicked.connect(self.merge_cxi_file)
		self.ui.pushButton_10.clicked.connect(self.merge_mask_file)
		self.ui.pushButton_11.clicked.connect(self.merge_bin_file)
		self.ui.pushButton_22.clicked.connect(self.merge_load_config)
		self.ui.pushButton_23.clicked.connect(self.merge_save_config)
		self.ui.pushButton_12.clicked.connect(self.run_merge)
		self.ui.pushButton_28.clicked.connect(self.merge_project)
		self.ui.pushButton_13.clicked.connect(self.merge_plot)
		# phasing tab
		self.ui.pushButton_14.clicked.connect(self.phase_input_file)
		self.ui.pushButton_15.clicked.connect(self.phase_mask_file)
		self.ui.pushButton_16.clicked.connect(self.phase_init_file)
		self.ui.pushButton_24.clicked.connect(self.phase_load_config)
		self.ui.pushButton_25.clicked.connect(self.phase_save_config)
		self.ui.pushButton_29.clicked.connect(self.phase_project)
		self.ui.pushButton_17.clicked.connect(self.run_phase)
		self.ui.pushButton_18.clicked.connect(self.phase_plot)
		# simulation tab
		self.ui.pushButton_19.clicked.connect(self.simu_input_file)
		self.ui.pushButton_20.clicked.connect(self.simu_mask_file)
		self.ui.comboBox_13.currentIndexChanged.connect(self.simu_algorithm)
		self.ui.comboBox_19.currentIndexChanged.connect(self.simu_euler_angles)
		self.ui.pushButton_26.clicked.connect(self.simu_load_config)
		self.ui.pushButton_27.clicked.connect(self.simu_save_config)
		self.ui.pushButton_32.clicked.connect(self.simu_euler_file)
		self.ui.pushButton_31.clicked.connect(self.simu_project)
		self.ui.pushButton_21.clicked.connect(self.run_simu)
		self.ui.pushButton_30.clicked.connect(self.simu_plot)
		# filtering tab
		self.ui.pushButton_33.clicked.connect(self.filter_save_manifold)
		self.ui.pushButton_5.clicked.connect(self.filter_save_tsne)
		self.ui.pushButton_4.clicked.connect(self.filter_input_file)
		self.ui.pushButton_9.clicked.connect(self.filter_mask_file)
		self.ui.pushButton_7.clicked.connect(self.filter_test_run)
		self.ui.pushButton_34.clicked.connect(self.filter_run)
		self.ui.pushButton_35.clicked.connect(self.filter_plot)


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
		self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
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
		# setup simulation
		for algorithm in self.namespace['simulation_assignments']:
			self.ui.comboBox_13.addItem(algorithm)
		self.ui.lineEdit_24.setVisible(False)
		self.ui.pushButton_32.setVisible(False)
		# setup monitors
		self.table_monitor = None
		# draw table
		self.refresh_table()


	def closeEvent(self, event):
		#self.JobCenter.write_job_hub()
		utils.print2projectLog(self.dirname, "Close spipy GUI.")
		QtWidgets.qApp.quit()

	def set_job_control(self):
		myMenu.jobctl(self.dirname, self.namespace)

	def js_changed(self, index):
		if self.ui.comboBox_2.itemText(index) == "PBS":
			if not utils.check_PBS():
				utils.show_message("No PBS detected !")
				self.ui.comboBox_2.setCurrentIndex(0)
			else:
				self.jss = str(self.ui.comboBox_2.currentText())
		elif self.ui.comboBox_2.itemText(index) == "LSF":
			if not utils.check_LSF():
				utils.show_message("No LSF detected !")
				self.ui.comboBox_2.setCurrentIndex(0)
			else:
				self.jss = str(self.ui.comboBox_2.currentText())
		else:
			return
		self.JobCenter.setjss(self.jss)


	def load_module_config(self, module_name):
		'''
			Only for Merge, Phasing and Simulation
		'''
		ret = [None]
		choices = os.path.join(self.dirname, module_name, 'config/*.ini')
		choices = glob.glob(choices)
		config_name = [os.path.split(c)[-1] for c in choices]
		chosebox.show_chosebox("config file", config_name, ret, "Configuration")
		if ret[0] is None:
			return None
		chosen = choices[ret[0]]
		return chosen


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
			menu = QtWidgets.QMenu()
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
				self.JobCenter.TableRun_showoff(job_type, selected_runs, selected_datafile, None)
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
						prev_dark_run = prev_dark_run.decode()
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
					utils.print2projectLog(self.dirname, "Terminate %d %s jobs of %s" % (killed, assign, str(selected_runs)))
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
			menu = QtWidgets.QMenu()
			if self.ui.tableWidget.horizontalHeader().sectionResizeMode(0) == QtWidgets.QHeaderView.Stretch:
				a1 = menu.addAction("Unfill table window")	
			else:
				a1 = menu.addAction("Fill table window")
			menu.addSeparator()
			a2 = menu.addAction("Set 'force overwrite' to %s" % str(not self.JobCenter.force_overwrite))

			action = menu.exec_(self.ui.tableWidget.mapToGlobal(position))
			if action == a1:
				if self.ui.tableWidget.horizontalHeader().sectionResizeMode(0) == QtWidgets.QHeaderView.Stretch:
					self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
				else:
					self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
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

		prev_runs = list(self.process_data.keys())
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
		prev_runs = list(self.process_data.keys())
		hf_module = self.namespace['project_structure'][0]
		self.num_running_jobs = 0
		for i,run_name in enumerate(prev_runs):
			self.process_data[run_name][3:6] = ['--'] * 3
			# get tag
			# assignments = self.namespace['process_HF']
			assignments = str(self.ui.comboBox.currentText())
			if not (run_name in self.tag_buffer[assignments].keys() and self.is_existed_runtag(assignments, run_name, self.tag_buffer[assignments][run_name])):
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
		runs = list(self.process_data.keys())
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
			newitem = QtWidgets.QTableWidgetItem(str(r))
			newitem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
			self.ui.tableWidget.setItem(i, 0, newitem)
			# set others
			for j,info in enumerate(infomation[1:self.columnCount]):
				j = j + 1
				newitem = QtWidgets.QTableWidgetItem(info)
				if j == 1:
					assignments = str(self.ui.comboBox.currentText())
					self.tag_buffer[assignments][r] = info
				if j in [2,3,4,5] and info != "--":
					cindex = self.namespace['process_status'].index(info.split(" ")[0])
					color = self.namespace['process_colors'][cindex]
					newitem.setBackground(QtGui.QBrush(QtGui.QColor(color[0], color[1], color[2], 127)))
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
			monitor_time = utils.read_config(file=os.path.join(self.dirname, self.namespace['ini']), \
						item=[self.namespace['project_ini'][0], self.namespace['project_ini'][1].split(',')[6]])
			self.table_monitor = utils.TableMonitor(int(monitor_time), self.refresh_table)
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


	def filter_save_manifold(self, test = False):
		if not test:
			tag_name = str(self.ui.lineEdit_16.text())
		else:
			tag_name = "buffer-ini"
		# consistent with process.py
		if len(tag_name) == 0 or '.' in tag_name or '_' in tag_name:
			utils.show_message("Please give a correct name for config file !\n Do not contain '.' or '_' in tag name.")
			return
		if not test:
			save_file = os.path.join(self.dirname, self.namespace['project_structure'][1], "config/%s_%s.ini" % (self.namespace['classify_DCPS'], tag_name))
		# # # # # # # # #
		params = {}
		params['low_cut_percent'] = self.ui.doubleSpinBox.value()
		params['method'] = "%d, %s" % (self.ui.comboBox_3.currentIndex(), self.ui.comboBox_3.currentText())
		params['LLE_method'] = "%d, %s" % (self.ui.comboBox_4.currentIndex(), self.ui.comboBox_4.currentText())
		params['LLE_neighbors'] = self.ui.spinBox_2.value()
		params['components'] = self.ui.spinBox.value()
		params['group_size'] = self.ui.spinBox_4.value()
		params['njobs'] = self.ui.spinBox_3.value()
		# write to file
		params_write = {}
		params_write[self.namespace['config_head']] = params
		if not test:
			utils.write_config(save_file, params_write)
			utils.show_message("Save successfully !\n(%s)" % save_file)
			utils.print2projectLog(self.dirname, "Save %s" % save_file)
		else:
			return params_write


	def filter_save_tsne(self, test = False):
		if not test:
			tag_name = str(self.ui.lineEdit_17.text())
		else:
			tag_name = "buffer-ini"
		# consistent with process.py
		if len(tag_name) == 0 or '.' in tag_name or '_' in tag_name:
			utils.show_message("Please give a correct name for config file !\n Do not contain '.' or '_' in tag name.")
			return
		if not test:
			save_file = os.path.join(self.dirname, self.namespace['project_structure'][1], "config/%s_%s.ini" % (self.namespace['classify_TSNE'], tag_name))
		# # # # # # # # #
		params = {}
		params['low_cut_percent'] = self.ui.doubleSpinBox_2.value()
		params['perplexity'] = self.ui.spinBox_6.value()
		params['PCA_out_dim'] = self.ui.spinBox_7.value()
		params['out_dim'] = self.ui.spinBox_5.value()
		params['theta'] = self.ui.doubleSpinBox_3.value()
		params['max_iter'] = self.ui.spinBox_8.value()
		params['group_size'] = self.ui.spinBox_9.value()
		params['njobs'] = self.ui.spinBox_10.value()
		# write to file
		params_write = {}
		params_write[self.namespace['config_head']] = params
		if not test:
			utils.write_config(save_file, params_write)
			utils.show_message("Save successfully !\n(%s)" % save_file)
			utils.print2projectLog(self.dirname, "Save %s" % save_file)
		else:
			return params_write


	def filter_input_file(self):
		cxifile = QtWidgets.QFileDialog(self).getOpenFileName(self, "Select h5/cxi file to open", "", "DATA (*.h5 *.cxi)")
		if len(cxifile[0])>0 and not os.path.exists(cxifile[0]):
			utils.show_message("The chosen file '%s' doesn't exist" % cxifile[0])
			return
		self.ui.lineEdit.setText(cxifile[0])


	def filter_mask_file(self):
		binfile = QtWidgets.QFileDialog(self).getOpenFileName(self, "Select mask file to open", "", "MASK (*.bin *.byt *.npy)")
		if len(binfile[0])>0 and not os.path.exists(binfile[0]):
			utils.show_message("The chosen file '%s' doesn't exist" % binfile[0])
			return
		self.ui.lineEdit_5.setText(binfile[0])


	def __filter_check_run(self):
		# success, return 'runtime' dict; else return None
		runtime = {}
		tmp = str(self.ui.lineEdit_2.text())
		if len(tmp) == 0:
			utils.show_message("'inh5' is empty !")
			return None
		else:
			runtime['inh5'] = tmp
		tmp = str(self.ui.lineEdit.text())
		if os.path.isfile(tmp):
			runtime['dataset'] = [tmp]
		else:
			utils.show_message("Dataset file is invalid !")
			return None
		tmp = str(self.ui.lineEdit_5.text())
		if os.path.isfile(tmp):
			runtime['mask'] = tmp
		elif tmp.lower() == "none":
			runtime['mask'] = None
		else:
			utils.show_message("Mask file is invalid !")
			return None
		# success !
		return runtime


	def filter_test_run(self):
		# get runtime
		runtime = self.__filter_check_run()
		if runtime is None:
			return
		runtime['benchmark'] = True
		# choose assignments
		assignments = self.namespace['classify_assignments']
		ret = [None]
		chosebox.show_chosebox("Assignments", assignments, ret, "Choose assignments")
		if ret[0] is None:
			return
		assignments = assignments[ret[0]]
		if assignments == self.namespace['classify_DCPS']:
			# manifold
			config = self.filter_save_manifold(test = True)
			# save path
			runtime['run_name'] = assignments
			runtime['savepath'] = os.path.join(self.dirname, self.namespace['project_structure'][1], assignments, ".buffer")
			# submit to job-testing window
			jb = job_benchmark.JobBenchmark(runtime, config, self, "Manifold Filtering")
			jb.showWindow()
		elif assignments == self.namespace['classify_TSNE']:
			# t-sne
			config = self.filter_save_tsne(test = True)
			runtime['run_name'] = assignments
			runtime['savepath'] = os.path.join(self.dirname, self.namespace['project_structure'][1], assignments, ".buffer")
			# submit to job-testing window
			jb = job_benchmark.JobBenchmark(runtime, config, self, "t-SNE Filtering")
			if jb.python_scripts is not None:
				jb.showWindow()
		else:
			pass


	def filter_run(self):
		# get runtime
		runtime = self.__filter_check_run()
		if runtime is None:
			return
		runtime['benchmark'] = False
		# choose assignments
		assignments = self.namespace['classify_assignments']
		ret = [None]
		chosebox.show_chosebox("Assignments", assignments, ret, "Choose assignments")
		if ret[0] is None:
			return
		assignments = assignments[ret[0]]
		job_type  = self.namespace['project_structure'][1] + "/" + assignments
		run_name = os.path.split(runtime['dataset'][0])[-1]
		run_name = run_name.replace(".", "")
		run_name = run_name.replace("_", "")
		datafile = runtime.pop("dataset")    # datafile is a list (contain only 1 item)!
		self.JobCenter.TableRun_showoff(job_type, [run_name], {run_name:datafile}, runtime=runtime)
		utils.print2projectLog(self.dirname, "Choose %s on %s" % (assignments, run_name))


	def filter_plot(self):
		# choose project
		path = os.path.join(self.dirname, self.namespace['project_structure'][1], '*/*.*.*' )
		path = glob.glob(path)
		project = [f.split(self.namespace['project_structure'][1])[-1].strip("/") for f in path]
		ret = [None]
		chosebox.show_chosebox("Project", project, ret, "Choose Project")
		if ret[0] is None:
			return
		proj_chosen = path[ret[0]]

		# plot
		h5file = glob.glob(os.path.join(proj_chosen, "*.h5"))
		if len(h5file) == 1:
			h5file = h5file[0]
		else:
			utils.show_message("Cannot determine which h5 file to use.",\
						 "- The project doesn't finish (successfully)\n\
						 - There are more than 1 hdf5 files in the folder")
			return
		cmd = "python %s --type 0 %s" % (os.path.join(os.path.dirname(__file__), "job_benchmark.py"), h5file)
		subprocess.check_call(cmd, shell=True)
		utils.print2projectLog(self.dirname, "Show result of %s" % project[ret[0]])




	'''
		Tool box
	'''


	def view_job(self):
		jobview.show_jobView(self)
		utils.print2projectLog(self.dirname, "Open job viewer.")


	def view_history(self):
		pass



	'''
		Merge Tab
	'''

	def merge_cxi_file(self):
		cxifile = QtWidgets.QFileDialog(self).getOpenFileName(None, "Select h5/cxi file to open", "", "DATA (*.h5 *.cxi)")
		if len(cxifile[0])>0 and not os.path.exists(cxifile[0]):
			utils.show_message("Can't find file path '%s'" % cxifile[0])
			return
		self.ui.lineEdit_3.setText(cxifile[0])
	

	def merge_mask_file(self):
		binfile = QtWidgets.QFileDialog(self).getOpenFileName(None, "Select mask file to open", "", "MASK (*.bin *.byt *.npy)")
		if len(binfile[0])>0 and not os.path.exists(binfile[0]):
			utils.show_message("Can't find file path '%s'" % binfile[0])
			return
		self.ui.lineEdit_6.setText(binfile[0])


	def merge_bin_file(self):
		binfile = QtWidgets.QFileDialog(self).getOpenFileName(None, "Select .bin file to open", "", "MODEL (*.bin *.byt)")
		if len(binfile[0])>0 and not os.path.exists(binfile[0]):
			utils.show_message("Can't find file path '%s'" % binfile[0])
			return
		self.ui.lineEdit_7.setText(binfile[0])
		

	def merge_load_config(self):
		config_file = self.load_module_config(self.namespace['project_structure'][2])
		if config_file is None:
			return
		chead = self.namespace['config_head']
		# read config
		try:
			config = utils.read_config(config_file)
			# load
			self.ui.lineEdit_6.setText(config.get(chead, "mask"))
			self.ui.lineEdit_4.setText(config.get(chead, "data-path in cxi/h5"))
			self.ui.doubleSpinBox_4.setValue(config.getfloat(chead, "clen"))
			self.ui.doubleSpinBox_5.setValue(config.getfloat(chead, "lambda"))
			self.ui.spinBox_11.setValue(config.getint(chead, "det_x"))
			self.ui.spinBox_12.setValue(config.getint(chead, "det_y"))
			self.ui.doubleSpinBox_6.setValue(config.getfloat(chead, "pix_size"))
			self.ui.spinBox_13.setValue(config.getint(chead, "beam_stop"))
			self.ui.doubleSpinBox_7.setValue(config.getfloat(chead, "ewald_rad"))
			self.ui.spinBox_17.setValue(config.getint(chead, "num_div"))
			self.ui.doubleSpinBox_9.setValue(config.getfloat(chead, "beta"))
			self.ui.doubleSpinBox_8.setValue(config.getfloat(chead, "beta_t"))
			self.ui.spinBox_15.setValue(config.getint(chead, "beta_i"))
			self.ui.spinBox_16.setValue(config.getint(chead, "scaling"))
			symm_string = config.get(chead, "symmetry")
			self.ui.comboBox_5.setCurrentIndex(int(symm_string.split(',')[0]))
			selection_string = config.get(chead, "data_selection")
			self.ui.comboBox_6.setCurrentIndex(int(selection_string.split(',')[0]))
			self.ui.lineEdit_7.setText(config.get(chead, "start_model"))
			self.ui.lineEdit_18.setText(utils.extract_tag(self.namespace['merge_emc'], config_file)+'-new')
		except Exception as err:
			utils.show_message("Error happens while loading config file !", str(err))
			return


	def merge_save_config(self):
		tag_name = str(self.ui.lineEdit_18.text())
		# consistent with process.py
		if len(tag_name) == 0 or '.' in tag_name or '_' in tag_name:
			utils.show_message("Please give a correct name for config file !\n Do not contain '.' or '_' in tag name.")
			return
		save_file = os.path.join(self.dirname, self.namespace['project_structure'][2], "config/%s_%s.ini" % (self.namespace['merge_emc'], tag_name))
		# # # # # # # # #
		params = {}
		# mask
		maskfile = str(self.ui.lineEdit_6.text())
		if maskfile.lower() == "none":
			maskfile = None
		elif os.path.isfile(maskfile) and os.path.splitext(maskfile)[-1] not in ['.npy', '.byt', '.bin']:
			utils.show_message("Please choose correct mask file (.npy .byt .bin) !")
			return
		elif not os.path.isfile(maskfile):
			re = utils.show_warning("'Mask File' is invalid, set to None, continue ?")
			if re == 1:
				maskfile = None
			else:
				return
		params["mask"] = maskfile
		# start model
		start_model = str(self.ui.lineEdit_7.text())
		if start_model.lower() == "random":
			start_model = "Random"
		elif os.path.isfile(start_model) and os.path.splitext(start_model)[-1] not in ['.byt', '.bin']:
			utils.show_message("Please choose correct start model (.byt .bin) !")
			return
		elif not os.path.isfile(start_model):
			re = utils.show_warning("'Start Model' is invalid, set to Random, continue ?")
			if re == 1:
				start_model = "Random"
			else:
				return
		# inh5
		inh5 = str(self.ui.lineEdit_4.text())
		if len(inh5) == 0:
			utils.show_message("'Data inside h5' shouldn't be empty !")
			return
		params['data-path in cxi/h5'] = inh5
		# others
		params['clen'] = self.ui.doubleSpinBox_4.value()
		params['lambda'] = self.ui.doubleSpinBox_5.value()
		params['det_x'] = self.ui.spinBox_11.value()
		params['det_y'] = self.ui.spinBox_12.value()
		params['pix_size'] = self.ui.doubleSpinBox_6.value()
		params['beam_stop'] = self.ui.spinBox_13.value()
		# if ewald_rad = 0, change to -1 when write emc config
		params['ewald_rad'] = self.ui.doubleSpinBox_7.value()
		params['num_div'] = self.ui.spinBox_17.value()
		params['beta'] = self.ui.doubleSpinBox_9.value()
		params['beta_t'] = self.ui.doubleSpinBox_8.value()
		params['beta_i'] = self.ui.spinBox_15.value()
		params['scaling'] = self.ui.spinBox_16.value()
		params['symmetry'] = "%d,%s" % (self.ui.comboBox_5.currentIndex(), str(self.ui.comboBox_5.currentText()))
		params['data_selection'] = "%d,%s" % (self.ui.comboBox_6.currentIndex(), str(self.ui.comboBox_6.currentText()))
		params['start_model'] = start_model
		# write to file
		params_write = {}
		params_write[self.namespace['config_head']] = params
		utils.write_config(save_file, params_write)
		utils.show_message("Save successfully !\n(%s)" % save_file)
		utils.print2projectLog(self.dirname, "Save %s" % save_file)


	def merge_project(self):
		path = os.path.join(self.dirname, self.namespace['project_structure'][2], self.namespace['merge_emc'], '*.*.*' )
		path = ['New Project'] + glob.glob(path)
		project = [os.path.split(f)[-1] for f in path]
		ret = [None]
		chosebox.show_chosebox("Project", project, ret, "Choose Project")
		if ret[0] is None:
			return
		proj_chosen = path[ret[0]]
		if ret[0] == 0 or not os.path.exists(proj_chosen):
			self.ui.lineEdit_8.setText("")
			self.ui.lineEdit_21.setText('New Project')
			self.ui.lineEdit_8.setReadOnly(False)
			self.ui.radioButton.setEnabled(False)
			self.ui.pushButton_13.setEnabled(False)
		else:
			self.ui.lineEdit_8.setText(utils.split_jobdir_runviewkey(project[ret[0]])['run_name'])
			self.ui.lineEdit_21.setText(project[ret[0]])
			self.ui.lineEdit_8.setReadOnly(True)
			self.ui.radioButton.setEnabled(True)
			self.ui.pushButton_13.setEnabled(True)


	def run_merge(self):
		# judge whether spipy is fully compiled
		try:
			import spipy
			spipy.info.EMC_MPI
		except:
			utils.show_message("Your spipy package are compiled without EMC module. See https://github.com/LiuLab-CSRC/spipy/wiki for details.")
			return

		# load jobcenter
		job_type = self.namespace['project_structure'][2] + '/' + self.namespace['merge_emc']
		run_name = str(self.ui.lineEdit_8.text())
		if '.' in run_name:
			utils.show_message("The dot character ('.') is not allowed in Project Name !")
			return
		data_file = str(self.ui.lineEdit_3.text())
		processes = self.ui.spinBox_14.value()
		threads = self.ui.spinBox_18.value()
		iterations = self.ui.spinBox_19.value()
		if not self.ui.radioButton.isEnabled():
			resume = False
		else:
			if self.ui.radioButton.isChecked():
				resume = True
			else:
				resume = False
		runtime = {'num_proc':processes, 'num_thread':threads, 'iters':iterations, 'resume':resume}
		if len(run_name) == 0:
			utils.show_message("Project name should not be blank !")
			return
		if not os.path.isfile(data_file):
			utils.show_message("Please choose data (HDF5) file !")
			return
		# notice again
		re = utils.show_warning("Confirm to submit this job ?\n", \
			"Job detail : %s (%s, %d iterations)\nJobs : %d (%d threads)" \
			% (job_type, run_name, iterations, processes, threads))
		if re == 1:
			self.JobCenter.TableRun_showoff(job_type, [run_name], {run_name:[data_file]}, runtime)
			utils.print2projectLog(self.dirname, "Choose %s on %s" % (self.namespace['merge_emc'], run_name))


	def merge_plot(self):
		job_info = utils.split_jobdir_runviewkey(str(self.ui.lineEdit_21.text()))
		try:
			jid = self.JobCenter.get_jid(self.namespace['merge_emc'], job_info['run_name'], job_info['tag'], job_info['remarks'])
			savepath = self.JobCenter.jobs[jid].savepath
			cmd = "cd %s;python autoplot.py" % os.path.join(savepath, job_info['run_name'])
			subprocess.check_call(cmd, shell=True)
			utils.print2projectLog(self.dirname, "Show result of %s.%s.%s.%s" % \
				(self.namespace['merge_emc'], job_info['run_name'], job_info['tag'], job_info['remarks']))
		except Exception as err:
			utils.show_message("Fail to plot result.", str(err))


	'''
		Phasing Tab
	'''

	def phase_input_file(self):
		inputfile = QtWidgets.QFileDialog(self).getOpenFileName(None, "Select .npy/.bin/.mat file to open", "", "DATA (*.npy *.bin *.mat)")
		if len(inputfile[0])>0 and not os.path.exists(inputfile[0]):
			utils.show_message("Can't find file path '%s'" % inputfile[0])
			return
		self.ui.lineEdit_9.setText(inputfile[0])


	def phase_mask_file(self):
		maskfile = QtWidgets.QFileDialog(self).getOpenFileName(None, "Select .npy file to open", "", "MASK (*.npy)")
		if len(maskfile[0])>0 and not os.path.exists(maskfile[0]):
			utils.show_message("Can't find file path '%s'" % maskfile[0])
			return
		self.ui.lineEdit_10.setText(maskfile[0])


	def phase_init_file(self):
		inputfile = QtWidgets.QFileDialog(self).getOpenFileName(None, "Select .npy/.bin/.mat file to open", "", "DATA (*.npy *.bin *.mat)")
		if len(inputfile[0])>0 and not os.path.exists(inputfile[0]):
			utils.show_message("Can't find file path '%s'" % inputfile[0])
			return
		self.ui.lineEdit_11.setText(inputfile[0])


	def phase_load_config(self):
		config_file = self.load_module_config(self.namespace['project_structure'][3])
		if config_file is None:
			return
		chead = self.namespace['config_head']
		# read config
		try:
			config = utils.read_config(config_file)
			# load
			self.ui.lineEdit_10.setText(config.get(chead, "mask"))
			tmp = config.get(chead, "dtype").split(',')[0]
			self.ui.comboBox_8.setCurrentIndex(int(tmp))
			self.ui.lineEdit_11.setText(config.get(chead, "start_model"))
			self.ui.spinBox_20.setValue(config.getint(chead, "inner_mask"))
			self.ui.spinBox_21.setValue(config.getint(chead, "outer_mask"))
			self.ui.spinBox_22.setValue(config.getint(chead, "o_o_mask"))
			tmp = config.get(chead, "iter_type_3").split(',')[0]
			self.ui.comboBox_11.setCurrentIndex(int(tmp))
			tmp = config.get(chead, "iter_type_2").split(',')[0]
			self.ui.comboBox_10.setCurrentIndex(int(tmp))
			tmp = config.get(chead, "iter_type_1").split(',')[0]
			self.ui.comboBox_9.setCurrentIndex(int(tmp))
			self.ui.spinBox_25.setValue(config.getint(chead, "iter_num_3"))
			self.ui.spinBox_24.setValue(config.getint(chead, "iter_num_2"))
			self.ui.spinBox_23.setValue(config.getint(chead, "iter_num_1"))
			self.ui.spinBox_27.setValue(config.getint(chead, "repeat"))
			self.ui.spinBox_26.setValue(config.getint(chead, "support"))
			self.ui.doubleSpinBox_14.setValue(config.getfloat(chead, "beta"))
			
			self.ui.lineEdit_19.setText(utils.extract_tag(self.namespace['phasing_PJ'], config_file)+'-new')
		except Exception as err:
			utils.show_message("Error happens while loading config file !", str(err))
			return


	def phase_save_config(self):
		tag_name = str(self.ui.lineEdit_19.text())
		# consistent with process.py
		if len(tag_name) == 0 or '.' in tag_name or '_' in tag_name:
			utils.show_message("Please give a correct name for config file ! Do not contain '.' or '_' in tag name.")
			return
		save_file = os.path.join(self.dirname, self.namespace['project_structure'][3], "config/%s_%s.ini" % (self.namespace['phasing_PJ'], tag_name))
		# # # # # # # # #
		params = {}
		# mask
		maskfile = str(self.ui.lineEdit_10.text())
		if maskfile.lower() == "none":
			maskfile = None
		elif os.path.isfile(maskfile) and os.path.splitext(maskfile)[-1] not in ['.npy']:
			utils.show_message("Please choose correct mask file (.npy) !")
			return
		elif not os.path.isfile(maskfile):
			re = utils.show_warning("'User Mask File' is invalid, set to None, continue ?")
			if re == 1:
				maskfile = None
			else:
				return
		params["mask"] = maskfile
		# start model
		start_model = str(self.ui.lineEdit_11.text())
		if start_model.lower() == "random":
			start_model = "Random"
		elif os.path.isfile(start_model) and os.path.splitext(start_model)[-1] not in ['.npy', '.bin', '.mat']:
			utils.show_message("Please choose correct initial model (.npy .bin .mat) !")
			return
		elif not os.path.isfile(start_model):
			re = utils.show_warning("'Initial Model' is invalid, set to Random, continue ?")
			if re == 1:
				start_model = "Random"
			else:
				return
		# others
		params['dtype'] = "%d,%s" % (self.ui.comboBox_8.currentIndex(), str(self.ui.comboBox_8.currentText()))
		params['start_model'] = start_model
		params['inner_mask'] = self.ui.spinBox_20.value()
		params['outer_mask'] = self.ui.spinBox_21.value()
		params['o_o_mask'] = self.ui.spinBox_22.value()
		params['iter_type_3'] = "%d,%s" % (self.ui.comboBox_11.currentIndex(), str(self.ui.comboBox_11.currentText()))
		params['iter_type_2'] = "%d,%s" % (self.ui.comboBox_10.currentIndex(), str(self.ui.comboBox_10.currentText()))
		params['iter_type_1'] = "%d,%s" % (self.ui.comboBox_9.currentIndex(), str(self.ui.comboBox_9.currentText()))
		params['iter_num_3'] = self.ui.spinBox_25.value()
		params['iter_num_2'] = self.ui.spinBox_24.value()
		params['iter_num_1'] = self.ui.spinBox_23.value()
		params['repeat'] = self.ui.spinBox_27.value()
		params['support'] = self.ui.spinBox_26.value()
		params['beta'] = self.ui.doubleSpinBox_14.value()

		# write to file
		params_write = {}
		params_write[self.namespace['config_head']] = params
		utils.write_config(save_file, params_write)
		utils.show_message("Save successfully !\n(%s)" % save_file)
		utils.print2projectLog(self.dirname, "Save %s" % save_file)


	def phase_project(self):
		path = os.path.join(self.dirname, self.namespace['project_structure'][3], self.namespace['phasing_PJ'], '*.*.*' )
		path = ['New Project'] + glob.glob(path)
		project = [os.path.split(f)[-1] for f in path]
		ret = [None]
		chosebox.show_chosebox("Project", project, ret, "Choose Project")
		if ret[0] is None:
			return
		proj_chosen = path[ret[0]]
		if ret[0] == 0 or not os.path.exists(proj_chosen):
			self.ui.lineEdit_12.setText("")
			self.ui.lineEdit_22.setText('New Project')
			self.ui.lineEdit_12.setReadOnly(False)
			self.ui.pushButton_18.setEnabled(False)
		else:
			self.ui.lineEdit_12.setText(utils.split_jobdir_runviewkey(project[ret[0]])['run_name'])
			self.ui.lineEdit_22.setText(project[ret[0]])
			self.ui.lineEdit_12.setReadOnly(True)
			self.ui.pushButton_18.setEnabled(True)


	def run_phase(self):
		# load jobcenter
		job_type = self.namespace['project_structure'][3] + '/' + self.namespace['phasing_PJ']
		run_name = str(self.ui.lineEdit_12.text())
		if '.' in run_name:
			utils.show_message("The dot character ('.') is not allowed in Project Name !")
			return
		data_file = str(self.ui.lineEdit_9.text())
		processes = self.ui.spinBox_28.value()
		# runtime
		runtime = {'num_proc':processes}
		if len(run_name) == 0:
			utils.show_message("Project name should not be blank !")
			return
		if not os.path.isfile(data_file):
			utils.show_message("Please choose data file !")
			return
		
		self.JobCenter.TableRun_showoff(job_type, [run_name], {run_name:[data_file]}, runtime)
		utils.print2projectLog(self.dirname, "Choose %s on %s" % (self.namespace['phasing_PJ'], run_name))


	def phase_plot(self):
		job_info = utils.split_jobdir_runviewkey(str(self.ui.lineEdit_22.text()))		
		try:
			jid = self.JobCenter.get_jid(self.namespace['phasing_PJ'], job_info['run_name'], job_info['tag'], job_info['remarks'])
			savepath = self.JobCenter.jobs[jid].savepath
			cmd = "cd %s;python show_result.py output.h5" % os.path.join(savepath, job_info['run_name'])
			re = subprocess.check_call(cmd, shell=True)
			utils.print2projectLog(self.dirname, "Show result of %s.%s.%s.%s" % \
				(self.namespace['phasing_PJ'], job_info['run_name'], job_info['tag'], job_info['remarks']))
		except Exception as err:
			utils.show_message("Fail to show result !", str(err))



	'''
		Simulation Tab
	'''

	def simu_input_file(self):
		inputfile = QtWidgets.QFileDialog(self).getOpenFileName(None, "Select .pdb file to open", "", "DATA (*.pdb)")
		if len(inputfile[0])>0 and not os.path.exists(inputfile[0]):
			utils.show_message("Can't find file path '%s'" % inputfile[0])
			return
		self.ui.lineEdit_13.setText(inputfile[0])


	def simu_mask_file(self):
		maskfile = QtWidgets.QFileDialog(self).getOpenFileName(None, "Select .npy file to open", "", "MASK (*.npy)")
		if len(maskfile[0])>0 and not os.path.exists(maskfile[0]):
			utils.show_message("Can't find file path '%s'" % maskfile[0])
			return
		self.ui.lineEdit_14.setText(maskfile[0])


	def simu_euler_file(self):
		eulerfile = QtWidgets.QFileDialog(self).getOpenFileName(None, "Select .txt/.dat/.eul file to open", "", "EULER (*.txt *.dat *.eul)")
		if len(eulerfile[0])>0 and not os.path.exists(eulerfile[0]):
			utils.show_message("Can't find file path '%s'" % eulerfile[0])
			return
		self.ui.lineEdit_24.setText(eulerfile[0])


	def simu_algorithm(self):
		algo = str(self.ui.comboBox_13.currentText())
		if algo == self.namespace['simulation_FFT']:
			self.ui.checkBox.setVisible(False)
			self.ui.checkBox_2.setVisible(False)
		elif algo == self.namespace['simulation_AS']:
			self.ui.checkBox.setVisible(True)
			self.ui.checkBox_2.setVisible(True)
		else:
			utils.show_message("I don't know the algorithm you choose : %s." % algo)


	def simu_euler_angles(self):
		eu_type = str(self.ui.comboBox_19.currentText())
		if eu_type.lower() == "random":
			self.ui.lineEdit_24.setVisible(False)
			self.ui.pushButton_32.setVisible(False)
		elif eu_type.lower() == "predefined":
			self.ui.lineEdit_24.setVisible(True)
			self.ui.pushButton_32.setVisible(True)
		else:
			utils.show_message("I don't know the euler angles you choose : %s." % eu_type)


	def simu_load_config(self):
		config_file = self.load_module_config(self.namespace['project_structure'][4])
		if config_file is None:
			return
		chead = self.namespace['config_head']
		assignments = utils.split_config(os.path.split(config_file)[-1])[0]
		# read config
		try:
			config = utils.read_config(config_file)
			# load
			self.ui.lineEdit_14.setText(config.get(chead, "mask"))
			self.ui.comboBox_13.setCurrentIndex(self.namespace['simulation_assignments'].index(assignments))
			self.ui.doubleSpinBox_10.setValue(config.getfloat(chead, "detd"))
			self.ui.doubleSpinBox_11.setValue(config.getfloat(chead, "lambda"))
			self.ui.doubleSpinBox_12.setValue(config.getfloat(chead, "pix_size"))
			self.ui.spinBox_30.setValue(config.getint(chead, "det_size"))
			self.ui.doubleSpinBox_13.setValue(config.getfloat(chead, "fluence"))
			self.ui.spinBox_29.setValue(config.getint(chead, "beam_stop"))
			self.ui.checkBox_4.setCheckState(config.getint(chead, "photons"))
			self.ui.checkBox_5.setCheckState(config.getint(chead, "absorption"))
			self.ui.comboBox_19.setCurrentIndex(self.ui.comboBox_19.findText(config.get(chead, "euler_type")))
			self.simu_euler_angles()
			if str(self.ui.comboBox_19.currentText()) == "predefined":
				self.ui.lineEdit_24.setText(config.get(chead, "euler_pred_file"))
			self.ui.comboBox_14.setCurrentIndex(self.ui.comboBox_14.findText(config.get(chead, "rot_order")))
			if assignments == self.namespace['simulation_AS']:
				self.ui.checkBox.setCheckState(config.getint(chead, "scatter_f"))
				self.ui.checkBox_2.setCheckState(config.getint(chead, "projection"))
			
			self.ui.lineEdit_20.setText(utils.extract_tag(assignments, config_file)+'-new')
		except Exception as err:
			utils.show_message("Error happens while loading config file !", str(err))
			return


	def simu_save_config(self):
		tag_name = str(self.ui.lineEdit_20.text())
		assignments = str(self.ui.comboBox_13.currentText())
		# consistent with process.py
		if len(tag_name) == 0 or '.' in tag_name or '_' in tag_name:
			utils.show_message("Please give a correct name for config file ! Do not contain '.' or '_' in tag name.")
			return
		save_file = os.path.join(self.dirname, self.namespace['project_structure'][4], "config/%s_%s.ini" % (assignments, tag_name))
		# # # # # # # # #
		params = {}
		# mask
		maskfile = str(self.ui.lineEdit_14.text())
		if os.path.isfile(maskfile) and os.path.splitext(maskfile)[-1] not in ['.npy']:
			utils.show_message("Please choose correct mask file (.npy) !")
			return
		elif not os.path.isfile(maskfile):
			maskfile = None
		# others
		if assignments == self.namespace['simulation_AS']:
			params['scatter_f'] = self.ui.checkBox.checkState()
			params['projection'] = self.ui.checkBox_2.checkState()
		params['euler_type'] = str(self.ui.comboBox_19.currentText())
		if params['euler_type'].lower() == "predefined":
			euler_file = str(self.ui.lineEdit_24.text())
			if not (os.path.isfile(euler_file) and os.path.splitext(euler_file)[-1] in ['.txt', '.dat', '.eul']):
				utils.show_message("Please choose correct euler angle file (.txt/.dat/.eul) !")
				return
			params['euler_pred_file'] = euler_file
		params['rot_order'] = str(self.ui.comboBox_14.currentText())
		params["mask"] = maskfile
		params['detd'] = self.ui.doubleSpinBox_10.value()
		params['lambda'] = self.ui.doubleSpinBox_11.value()
		params['pix_size'] = self.ui.doubleSpinBox_12.value()
		params['det_size'] = self.ui.spinBox_30.value()
		params['fluence'] = self.ui.doubleSpinBox_13.value()
		params['beam_stop'] = self.ui.spinBox_29.value()
		params['photons']   = self.ui.checkBox_4.checkState()
		params['absorption']= self.ui.checkBox_5.checkState()

		# write to file
		params_write = {}
		params_write[self.namespace['config_head']] = params
		utils.write_config(save_file, params_write)
		utils.show_message("Save successfully !\n(%s)" % save_file)
		utils.print2projectLog(self.dirname, "Save %s" % save_file)


	def simu_project(self):
		path = []
		project = []
		for assignments in self.namespace['simulation_assignments']:
			path.append("%s.New Project" % assignments)
			project.append("%s.New Project" % assignments)
		for assignments in self.namespace['simulation_assignments']:
			tmp = os.path.join(self.dirname, self.namespace['project_structure'][4], assignments, '*.*.*' )
			tmp = glob.glob(tmp)
			path.extend(tmp)
			project.extend(assignments+"."+os.path.split(f)[-1] for f in tmp)
		ret = [None]
		chosebox.show_chosebox("Project", project, ret, "Choose Project")
		if ret[0] is None:
			return
		proj_chosen = path[ret[0]]
		if ".New Project" in proj_chosen:
			#self.ui.lineEdit_15.setText("")
			self.ui.lineEdit_23.setText(project[ret[0]])
			self.ui.lineEdit_15.setReadOnly(False)
			self.ui.pushButton_30.setEnabled(False)
		elif not os.path.exists(proj_chosen):
			#self.ui.lineEdit_15.setText("")
			self.ui.lineEdit_23.setText("")
			self.ui.lineEdit_15.setReadOnly(False)
			self.ui.pushButton_30.setEnabled(False)
		else:
			self.ui.lineEdit_15.setText(utils.split_jobdir_runviewkey(project[ret[0]])['run_name'])
			self.ui.lineEdit_23.setText(project[ret[0]])
			self.ui.lineEdit_15.setReadOnly(True)
			self.ui.pushButton_30.setEnabled(True)


	def run_simu(self):
		# load jobcenter
		assignments = str(self.ui.lineEdit_23.text()).split(".")[0]
		if len(assignments) == 0:
			utils.show_message("Please choose a simulation project !")
			return
		run_name = str(self.ui.lineEdit_15.text())
		if '.' in run_name:
			utils.show_message("The dot character ('.') is not allowed in Project Name !")
			return
		job_type = self.namespace['project_structure'][4] + '/' + assignments
		pdb_file = str(self.ui.lineEdit_13.text())
		processes = self.ui.spinBox_33.value()
		num_pat = self.ui.spinBox_32.value()
		# runtime
		runtime = {'num_proc':processes, 'num_pattern':num_pat}
		if len(run_name) == 0:
			utils.show_message("Project name should not be blank !")
			return
		if not os.path.isfile(pdb_file):
			utils.show_message("Please choose PDB file !")
			return
		# submit
		self.JobCenter.TableRun_showoff(job_type, [run_name], {run_name:[pdb_file]}, runtime)
		utils.print2projectLog(self.dirname, "Choose %s on %s" % (assignments, run_name))


	def simu_plot(self):
		# open data viewer if it is closed
		if not data_viewer.is_shown():
			data_viewer.show_data_viewer(self)
		# load data
		job_info = utils.split_jobdir_runviewkey(str(self.ui.lineEdit_23.text()))		
		try:
			jid = self.JobCenter.get_jid(job_info['assignments'], job_info['run_name'], job_info['tag'], job_info['remarks'])
			savepath = self.JobCenter.jobs[jid].savepath
			tmp = glob.glob(os.path.join(savepath, "spipy_*_simulation*.h5"))
			data_viewer.add_files(tmp)
			utils.print2projectLog(self.dirname, "Add %s results of %s to data viewer." \
									% (job_info['assignments'], job_info['run_name']))
		except Exception as err:
			utils.show_message("Fail to show result !", str(err))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    myapp = SPIPY_MAIN()
    myapp.setup('./','PBS', None, True, 0)
    myapp.show()
    app.exec_()