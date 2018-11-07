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
		self.jss = None
		self.datapathtype = True  # True: dir--runs_dir--datafile  False: dir--datafile
		self.data_format = None  # see self.namespace['data_format']
		# process_data is table infomation, the keys are run number, and first column stores raw data path
		# , other columns are consistent with tableWidget
		self.columnCount = self.ui.tableWidget.columnCount()
		self.process_data = {}
		self.JobCenter = None
		# setup triggers
		self.ui.tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
		self.ui.comboBox_2.currentIndexChanged.connect(self.js_changed)
		self.ui.comboBox.currentIndexChanged.connect(self.assignments_changed)
		self.ui.comboBox_3.currentIndexChanged.connect(self.decomp_changed)
		self.ui.pushButton.clicked.connect(self.view_job)
		self.ui.pushButton_2.clicked.connect(self.view_log)
		self.ui.pushButton_3.clicked.connect(partial(process.parameters_setting, self))
		self.ui.pushButton_6.clicked.connect(self.refresh_table)
		self.ui.checkBox_3.stateChanged.connect(self.autorefresh)
		self.ui.tableWidget.customContextMenuRequested.connect(self.table_menu)


	def setup(self, workpath, datapath, jss, datapathtype, format_index):
		self.jss = jss
		self.dirname = workpath
		self.datapath = datapath
		self.datapathtype = datapathtype
		self.data_format = self.namespace['data_format'][format_index]
		# setup job center
		self.JobCenter = jobc.JobCenter(self.jss, self.dirname)
		# load table change log, if there exists
		self.rawdata_changelog = utils.load_changelog(os.path.join(self.dirname, self.namespace['project_structure'][0]))
		# write jss to UI
		if self.jss is not None:
			self.ui.comboBox_2.addItem(self.jss)
		# setup all tabWidgets
		# setup process
		for assm in self.namespace['process_assignments']:
			self.ui.comboBox.addItem(assm)
		self.ui.tableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
		self.ui.label_73.setText( utils.fmt_process_status(self.data_format) )
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


	def closeEvent(self, event):
		QtGui.qApp.quit()


	def js_changed(self, index):
		if self.ui.comboBox_2.itemText(index) == "PBS":
			if not utils.check_PBS():
				utils.show_message("No PBS detected !")
				self.ui.comboBox_2.setCurrentIndex(0)
			else:
				self.jss = self.ui.comboBox_2.currentText()
		else:
			pass


	"""
		Process Tab
	"""

	# run folder name format:
	#	.../run.tag.remarks/...

	def get_existing_runtags(self, assignments, run_name):
		module_name = self.namespace['project_structure'][0]
		path = os.path.join(self.dirname, module_name, '%s/%s.*' % (assignments, run_name))
		tags = glob.glob(path)
		tags = [os.path.split(tmp)[-1].split(run_name+'.')[-1] for tmp in tags]
		return tags


	def get_latest_runtag(self, assignments, run_name):
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
		return os.path.split(latest)[-1].split(run_name+'.')[-1]


	def assignments_changed(self, index):
		# change combobox in table
		# refresh table ?
		self.refresh_table()


	def table_menu(self, position):
		"""
		entrance to submit jobs
		"""
		# refresh job status in JC
		self.JobCenter.update_status()

		# selected cells
		selected_runs = []
		selected_tags = []
		for pos in self.ui.tableWidget.selectionModel().selection().indexes():
			row = pos.row()
			run_name = self.ui.tableWidget.item(row, 0).text()
			tag_name = self.ui.tableWidget.item(row, 1).text()
			selected_runs.append(str(run_name))
			selected_tags.append(str(tag_name))
		if len(selected_runs) > 0:
			# get assignments
			assignments = str(self.ui.comboBox.currentText())
			# show menu
			menu = QtGui.QMenu()
			a1 = menu.addAction("Run %s" % assignments)
			menu.addSeparator()
			a2 = menu.addAction("Terminate all")
			menu_sub = menu.addMenu("Terminate")
			b = []
			if len(selected_runs) > 1:
				for assgn in self.namespace['process_assignments']:
					b.append(menu_sub.addAction(assgn))
			elif len(selected_runs) == 1:
				if self.JobCenter.run_view.has_key(selected_runs[0]): 
					for jid in self.JobCenter.run_view[selected_runs[0]]:
						assignments = self.JobCenter.jobs[jid].assignments
						b.append( menu_sub.addAction(str(jid) + " : %s" % assignments) )
				menu.addSeparator()
				if selected_tags[0] == "darkcal":
					a4 = menu.addAction("Set as current darkcal")
				elif selected_tags[0] != "--":
					a4 = menu.addAction("View %s" % assignments)
				else:
					a4 = 0
			else:
				pass

			# exec
			action = menu.exec_(self.ui.tableWidget.mapToGlobal(position))

			# parse selection
			# TODO : submit job to job center
			job_type  = self.namespace['project_structure'][0] + "/" + assignments

			if action == a1:
				utils.print2projectLog(self.dirname, "Choose %s on %s" % (assignments, str(selected_runs)))
				self.JobCenter.TableRun_showoff(job_type, selected_runs)
			elif action == a2:
				print("Terminate all jobs of %s" % str(selected_runs))
			elif len(selected_runs) == 1 and action == a4:
				if selected_tags[0] == "darkcal":
					print("Set %s as current darkcal" % selected_runs[0])
				else:
					print("View %s results of %s" % (assignments, selected_runs[0]))
			elif len(selected_runs) == 1 and action in b:
				jid = int( str(action.text()).split(':')[0] )
				print("Terminate job %d of %s" % (jid, str(selected_runs)))
			elif len(selected_runs) > 1 and action in b:
				assgn = action.text()
				print("Terminate %s of %s" % (assgn, str(selected_runs)))
			else:
				pass
		else:
			menu = QtGui.QMenu()
			if self.ui.tableWidget.horizontalHeader().resizeMode(0) == QtGui.QHeaderView.Stretch:
				a1 = menu.addAction("Unfill table window")
				action = menu.exec_(self.ui.tableWidget.mapToGlobal(position))
				if action == a1:
					self.ui.tableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
				else:
					pass
			elif self.ui.tableWidget.horizontalHeader().resizeMode(0) == QtGui.QHeaderView.Interactive:
				a1 = menu.addAction("Fill table window")
				action = menu.exec_(self.ui.tableWidget.mapToGlobal(position))
				if action == a1:
					self.ui.tableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
				else:
					pass


	def update_table_runs(self):
		if not os.path.isdir(self.datapath):
			utils.show_message("Data directory is invalid, please reopen the software.")
			return

		# subdir ?
		if not self.datapathtype:
			all_in_dir = utils.parse_multi_runs(self.datapath, self.data_format)
		else:
			all_in_dir = [f for f in os.listdir(self.datapath) if f[0]!="." and f[0]!="$" \
									and os.path.isdir(os.path.join(self.datapath, f))]

		prev_runs = self.process_data.keys()
		prev_runs_checked = [0] * len(prev_runs)
		run_name = ""
		run_streams_num = "0"

		# go through alll files/dirs
		for d in all_in_dir:
			# parse run name
			if not self.datapathtype:
				tmp = utils.findnumber(d)
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
					self.process_data[run_name][0] = utils.parse_multi_run_streams(self.datapath, run_name, self.data_format)
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
					datafile = utils.parse_multi_run_streams(self.datapath, run_name, self.data_format)
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

		# update status of job center
		self.JobCenter.update_status()

		for i,c in enumerate(prev_runs_checked):
			if c == 0 :
				run_name = prev_runs[i]
				tmp = self.process_data.pop(run_name)
				self.rawdata_changelog[run_name].update(utils.rawdata_changelog(tmp[0], "This run is Deleted"))
			else:
				run_name = prev_runs[i]
				assignments = self.ui.comboBox.currentText()
				latest_tag = self.get_latest_runtag(str(assignments), run_name)
				self.process_data[run_name][1] = latest_tag
				# job status
				job_status = self.JobCenter.get_run_status(run_name, assignments, latest_tag)
				if job_status is None:
					continue
				if assignments == self.namespace['process_HF']:
					self.process_data[run_name][3] = job_status
				elif assignments == self.namespace['process_FA']:
					self.process_data[run_name][4] = job_status
				elif assignments == self.namespace['process_FAA']:
					self.process_data[run_name][4] = job_status
				elif assignments == self.namespace['process_AP']:
					self.process_data[run_name][5] = job_status
				else:
					pass



	def draw_table(self):
		runs = self.process_data.keys()
		runs.sort()
		assignments = self.ui.comboBox.currentText()
		hits = 0
		patterns = 0
		for i,r in enumerate(runs):
			infomation = self.process_data[r]
			# insert row ?
			if i >= self.ui.tableWidget.rowCount():
				self.ui.tableWidget.insertRow(i)
			# set run name
			newitem = QtGui.QTableWidgetItem(str(r))
			newitem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
			self.ui.tableWidget.setItem(i, 0, newitem)
			# set others
			for j,info in enumerate(infomation[1:self.columnCount]):
				j = j+1
				newitem = QtGui.QTableWidgetItem(info)
				if j == 2:
					cindex = self.namespace['process_status'].index(info.split(" ")[0])
					color = self.namespace['process_colors'][cindex]
					newitem.setBackgroundColor(QtGui.QColor(color[0], color[1], color[2], 127))
				newitem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
				self.ui.tableWidget.setItem(i, j, newitem)
			# cal hits and patterns
			hitinfo = utils.findnumber(infomation[6])
			if len(hitinfo) == 3:
				hits += int(hitinfo[1])
				patterns += int(hitinfo[2])
		self.ui.label_73.setText( utils.fmt_process_status(self.data_format, hits, patterns) )



	def refresh_table(self):
		# lock button
		self.ui.pushButton_6.setEnabled(False)
		# refresh
		self.update_table_runs()
		self.draw_table()
		utils.logging_table(self.process_data, self.rawdata_changelog, \
				os.path.join(self.dirname, self.namespace['project_structure'][0]))
		utils.print2projectLog(self.dirname, "Table updated.")
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
		print "view job"


	def view_log(self):
		print "view log"





if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    myapp = SPIPY_MAIN()
    myapp.setup('./','PBS')
    myapp.show()
    app.exec_()