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
from param_setting_gui import Ui_Settings


class Process_Settings(QtGui.QMainWindow, QtCore.QEvent):

	param = {}


	def __init__(self, mainwindow):
		QtGui.QWidget.__init__(self, mainwindow)
		# setup ui
		self.ui = Ui_Settings()
		self.ui.setupUi(self)
		# parents
		self.mainwindow = mainwindow
		# get namespace
		self.namespace = utils.read_ini()
		self.module_name = self.namespace['project_structure'][0]
		self.assignments = self.mainwindow.ui.comboBox.currentText()
		# init Tag
		tags = glob.glob(self.get_config_path(self.assignments, None))
		"""
		if self.assignments == self.namespace['process_HF']:
			tags.append("darkcal.ini")
		"""
		if len(tags)>0:
			self.ui.comboBox.addItem("")
			tags = [tmp.split('/')[-1] for tmp in tags]
			for tag in tags:
				self.ui.comboBox.addItem(self.extract_tag(tag))
		self.ui.comboBox.setCurrentIndex(0)
		self.ui.comboBox.currentIndexChanged.connect(self.selectionchange)
		# bind save button
		self.connect(self.ui.pushButton_4, QtCore.SIGNAL(("clicked()")), self.save)
		self.connect(self.ui.pushButton_5, QtCore.SIGNAL(("clicked()")), self.close)
		# setup ui & parameters
		self.initui(self.assignments)


	def get_config_path(self, assignments, tagname=None):
		if tagname is None:
			return os.path.join(os.path.join(self.mainwindow.dirname, self.module_name), 'config/%s_*' % assignments)
		else:
			return os.path.join(os.path.join(self.mainwindow.dirname, self.module_name), 'config/%s_%s.ini' % (assignments, tagname))


	def extract_tag(self, tagfilename):
		return tagfilename.split(self.assignments+"_")[-1].split('.ini')[0]


	def initui(self, assignments):
		# init tag
		if assignments in Process_Settings.param.keys():
			self.ui.lineEdit_5.setText( Process_Settings.param[assignments][str(self.ui.label_9.text())] )

		# init other widgets according to assignments
		if assignments == self.namespace['process_HF']:
			# set text
			self.setWindowTitle("Hit-Finding Parameters")
			self.ui.label.setText("Data Dir")
			self.ui.label_5.setText("Data-path in cxi/h5")
			self.ui.widget_2.setVisible(False)
			#self.ui.label_2.setText("Dark calibration (.h5)")
			self.ui.label_4.setText("Mask (.npy)")
			self.ui.label_3.setText("ROI Radii Range")
			self.ui.label_6.setText("Chi-square Cut-off")
			self.ui.spinBox_3.setValue(10)
			#self.ui.widget_7.setVisible(False)
			self.ui.label_7.setText("Downsampling")
			self.ui.spinBox_4.setMinimum(1)
			self.ui.widget_8.setVisible(False)
			self.ui.checkBox.setVisible(False)
			self.ui.checkBox_2.setText("Save hits")
			self.ui.checkBox_2.setCheckState(QtCore.Qt.Checked)
			self.ui.lineEdit.setText(self.mainwindow.datapath)
			# set trigger
			#self.connect(self.ui.pushButton_2, QtCore.SIGNAL(("clicked()")), partial(self.cxi_file, 2))
			self.connect(self.ui.pushButton_3, QtCore.SIGNAL(("clicked()")), partial(self.npy_file, 3))
			self.connect(self.ui.pushButton, QtCore.SIGNAL(("clicked()")), self.data_dir)
			self.ui.checkBox_2.stateChanged.connect(self.downsampling)
			# set/read Process_Settings.param
			if assignments in Process_Settings.param.keys():
				# this assignment has been set, show it
				self.ui.lineEdit.setText( Process_Settings.param[assignments][str(self.ui.label.text())] )
				self.ui.lineEdit_4.setText( Process_Settings.param[assignments][str(self.ui.label_5.text())] )
				#self.ui.lineEdit_2.setText( Process_Settings.param[assignments][str(self.ui.label_2.text())] )
				self.ui.lineEdit_3.setText( Process_Settings.param[assignments][str(self.ui.label_4.text())] )
				self.ui.spinBox.setValue( Process_Settings.param[assignments][str(self.ui.label_3.text())][0] )
				self.ui.spinBox_2.setValue( Process_Settings.param[assignments][str(self.ui.label_3.text())][1] )
				self.ui.spinBox_3.setValue( Process_Settings.param[assignments][str(self.ui.label_6.text())] )
				self.ui.spinBox_4.setValue( Process_Settings.param[assignments][str(self.ui.label_7.text())] )
				self.ui.checkBox_2.setCheckState( Process_Settings.param[assignments][str(self.ui.checkBox_2.text())] )
		elif assignments == self.namespace['process_FA']:
			# set text
			self.setWindowTitle("Fix-Artifacts Parameters")
			self.ui.label.setText("Data Dir")
			self.ui.label_5.setText("Data-path in cxi/h5")
			self.ui.label_2.setText("Mask (.npy)")
			self.ui.label_4.setText("Artifacts (.npy)")
			self.ui.label_3.setText("Estimate Center(x,y)")
			self.ui.widget_6.setVisible(False)
			self.ui.widget_7.setVisible(False)
			self.ui.widget_8.setVisible(False)
			self.ui.checkBox.setVisible(False)
			self.ui.lineEdit.setText(os.path.join(self.mainwindow.dirname, self.module_name))
			# set triiger
			self.connect(self.ui.pushButton, QtCore.SIGNAL(("clicked()")), self.data_dir)
			self.connect(self.ui.pushButton_2, QtCore.SIGNAL(("clicked()")), partial(self.npy_file, 2))
			self.connect(self.ui.pushButton_3, QtCore.SIGNAL(("clicked()")), partial(self.npy_file, 3))
			# set/read Process_Settings.param
			if assignments in Process_Settings.param.keys():
				# this assignment has been set, show it
				self.ui.lineEdit.setText( Process_Settings.param[assignments][str(self.ui.label.text())] )
				self.ui.lineEdit_4.setText( Process_Settings.param[assignments][str(self.ui.label_5.text())] )
				self.ui.lineEdit_2.setText( Process_Settings.param[assignments][str(self.ui.label_2.text())] )
				self.ui.lineEdit_3.setText( Process_Settings.param[assignments][str(self.ui.label_4.text())] )
				self.ui.spinBox.setValue( Process_Settings.param[assignments][str(self.ui.label_3.text())][0] )
				self.ui.spinBox_2.setValue( Process_Settings.param[assignments][str(self.ui.label_3.text())][1] )
				self.ui.checkBox_2.setCheckState( Process_Settings.param[assignments][str(self.ui.checkBox_2.text())] )
		elif assignments == self.namespace['process_FAA']:
			# set text
			self.setWindowTitle("Fix-Artifacts-auto Parameters")
			self.ui.label.setText("Data Dir")
			self.ui.label_5.setText("Data-path in cxi/h5")
			self.ui.label_2.setText("Mask (.npy)")
			self.ui.widget_4.setVisible(False)
			self.ui.widget_3.setVisible(False)
			self.ui.label_6.setText("Volume of bins")
			self.ui.spinBox_3.setValue(100)
			self.ui.spinBox_3.setMinimum(50)
			self.ui.spinBox_3.setMaximum(1000)
			self.ui.widget_7.setVisible(False)
			#self.ui.label_7.setText("nJobs (per data file)")
			#self.ui.spinBox_4.setMinimum(1)
			self.ui.widget_8.setVisible(False)
			self.ui.checkBox.setVisible(False)
			self.ui.lineEdit.setText(os.path.join(self.mainwindow.dirname, self.namespace['project_structure'][1]))
			# set triiger
			self.connect(self.ui.pushButton, QtCore.SIGNAL(("clicked()")), self.data_dir)
			self.connect(self.ui.pushButton_2, QtCore.SIGNAL(("clicked()")), partial(self.npy_file, 2))
			# set/read Process_Settings.param
			if assignments in Process_Settings.param.keys():
				# this assignment has been set, show it
				self.ui.lineEdit.setText( Process_Settings.param[assignments][str(self.ui.label.text())] )
				self.ui.lineEdit_4.setText( Process_Settings.param[assignments][str(self.ui.label_5.text())] )
				self.ui.lineEdit_2.setText( Process_Settings.param[assignments][str(self.ui.label_2.text())] )
				self.ui.spinBox_3.setValue( Process_Settings.param[assignments][str(self.ui.label_6.text())] )
				#self.ui.spinBox_4.setValue( Process_Settings.param[assignments][str(self.ui.label_7.text())] )
				self.ui.checkBox_2.setCheckState( Process_Settings.param[assignments][str(self.ui.checkBox_2.text())] )
		elif assignments == self.namespace['process_AP']:
			# set text
			self.setWindowTitle("adu2Photon Parameters")
			self.ui.label.setText("Data Dir")
			self.ui.label_5.setText("Data-path in cxi/h5")
			self.ui.label_2.setText("Mask (.npy)")
			self.ui.widget_4.setVisible(False)
			self.ui.widget_3.setVisible(False)
			self.ui.widget_6.setVisible(False)
			self.ui.widget_7.setVisible(False)
			#self.ui.label_7.setText("nJobs (per data file)")
			#self.ui.spinBox_4.setMinimum(1)
			self.ui.label_8.setText("Photon percent")
			self.ui.lineEdit.setText(os.path.join(self.mainwindow.dirname, self.module_name))
			# set triiger
			self.connect(self.ui.pushButton, QtCore.SIGNAL(("clicked()")), self.data_dir)
			self.connect(self.ui.pushButton_2, QtCore.SIGNAL(("clicked()")), partial(self.npy_file, 2))
			# set/read Process_Settings.param
			if assignments in Process_Settings.param.keys():
				# this assignment has been set, show it
				self.ui.lineEdit.setText( Process_Settings.param[assignments][str(self.ui.label.text())] )
				self.ui.lineEdit_4.setText( Process_Settings.param[assignments][str(self.ui.label_5.text())] )
				self.ui.lineEdit_2.setText( Process_Settings.param[assignments][str(self.ui.label_2.text())] )
				#self.ui.spinBox_4.setValue( Process_Settings.param[assignments][str(self.ui.label_7.text())] )
				self.ui.doubleSpinBox.setValue( Process_Settings.param[assignments][str(self.ui.label_8.text())] )
				self.ui.checkBox.setCheckState( Process_Settings.param[assignments][str(self.ui.checkBox.text())] )
				self.ui.checkBox_2.setCheckState( Process_Settings.param[assignments][str(self.ui.checkBox_2.text())] )
		else:
			self.setWindowTitle("Booommmmb !")
			self.ui.widget.setVisible(False)
			self.ui.widget_2.setVisible(False)
			self.ui.widget_3.setVisible(False)
			self.ui.widget_4.setVisible(False)
			self.ui.widget_5.setVisible(False)
			self.ui.widget_6.setVisible(False)
			self.ui.widget_7.setVisible(False)
			self.ui.widget_8.setVisible(False)
			self.ui.widget_9.setVisible(False)
			# show messages
			self.ui.label_temp = QtGui.QLabel(self.ui.widget_10)
			self.ui.label_temp.setText("Wrong assignment.\n"+utils.information['report_bug'])
			self.ui.horizontalLayout_10.addWidget(self.ui.label_temp)
			# bind save button with close event
			self.ui.pushButton_4.setText("Roger That.")
			self.connect(self.ui.pushButton_4, QtCore.SIGNAL(("clicked()")), self.close)
			return


	def data_dir(self):
		datapath = str(QtGui.QFileDialog(self).getExistingDirectory())
		if len(datapath) > 0:
			self.ui.lineEdit.setText(datapath)


	def cxi_file(self, i):
		cxifile = str(QtGui.QFileDialog(self).getOpenFileName(None, "Select h5/cxi file to open", "", "DATA (*.h5 *.cxi)"))
		if i==2:
			self.ui.lineEdit_2.setText(cxifile)
		elif i==3:
			self.ui.lineEdit_3.setText(npyfile)


	def npy_file(self, i):
		npyfile = str(QtGui.QFileDialog(self).getOpenFileName(None, "Select npy file to open", "", "DATA (*.npy)"))
		if i==2:
			self.ui.lineEdit_2.setText(npyfile)
		elif i==3:
			self.ui.lineEdit_3.setText(npyfile)


	def downsampling(self, state):
		if state == QtCore.Qt.Checked:
			self.ui.widget_7.setVisible(True)
		else:
			self.ui.widget_7.setVisible(False)


	def selectionchange(self):
		tagname = self.ui.comboBox.currentText()
		self.ui.lineEdit_5.setText(tagname)
		if len(tagname) == 0:
			return

		config_file = self.get_config_path(self.assignments, tagname)
		config = utils.read_config(config_file)
		if self.assignments == self.namespace['process_HF']:
			self.ui.lineEdit.setText( config.get( self.namespace['config_head'], str(self.ui.label.text()) ) )
			self.ui.lineEdit_4.setText( config.get( self.namespace['config_head'], str(self.ui.label_5.text()) ) )
			#self.ui.lineEdit_2.setText( config.get( self.namespace['config_head'], str(self.ui.label_2.text()) ) )
			self.ui.lineEdit_3.setText( config.get( self.namespace['config_head'], str(self.ui.label_4.text()) ) )
			spinboxv = utils.findnumber( config.get( self.namespace['config_head'], str(self.ui.label_3.text()) ) )
			self.ui.spinBox.setValue( int(spinboxv[0]) )
			self.ui.spinBox_2.setValue( int(spinboxv[1]) )
			self.ui.spinBox_3.setValue( int( config.get( self.namespace['config_head'], str(self.ui.label_6.text()) ) ) )
			self.ui.spinBox_4.setValue( int( config.get( self.namespace['config_head'], str(self.ui.label_7.text()) ) ) )
			self.ui.checkBox_2.setCheckState( int( config.get( self.namespace['config_head'], str(self.ui.checkBox_2.text()) ) ) )
		elif self.assignments == self.namespace['process_FA']:
			self.ui.lineEdit.setText( config.get( self.namespace['config_head'], str(self.ui.label.text()) ) )
			self.ui.lineEdit_4.setText( config.get( self.namespace['config_head'], str(self.ui.label_5.text()) ) )
			self.ui.lineEdit_2.setText( config.get( self.namespace['config_head'], str(self.ui.label_2.text()) ) )
			self.ui.lineEdit_3.setText( config.get( self.namespace['config_head'], str(self.ui.label_4.text()) ) )
			spinboxv = utils.findnumber( config.get( self.namespace['config_head'], str(self.ui.label_3.text()) ) )
			self.ui.spinBox.setValue( int(spinboxv[0]) )
			self.ui.spinBox_2.setValue( int(spinboxv[1]) )
			self.ui.checkBox_2.setCheckState( int( config.get( self.namespace['config_head'], str(self.ui.checkBox_2.text()) ) ) )
		elif self.assignments == self.namespace['process_FAA']:
			self.ui.lineEdit.setText( config.get( self.namespace['config_head'], str(self.ui.label.text()) ) )
			self.ui.lineEdit_4.setText( config.get( self.namespace['config_head'], str(self.ui.label_5.text()) ) )
			self.ui.lineEdit_2.setText( config.get( self.namespace['config_head'], str(self.ui.label_2.text()) ) )
			self.ui.spinBox_3.setValue( int( config.get( self.namespace['config_head'], str(self.ui.label_6.text()) ) ) )
			#self.ui.spinBox_4.setValue( int( config.get( self.namespace['config_head'], str(self.ui.label_7.text()) ) ) )
			self.ui.checkBox_2.setCheckState( int( config.get( self.namespace['config_head'], str(self.ui.checkBox_2.text()) ) ) )
		elif self.assignments == self.namespace['process_AP']:
			self.ui.lineEdit.setText( config.get( self.namespace['config_head'], str(self.ui.label.text()) ) )
			self.ui.lineEdit_4.setText( config.get( self.namespace['config_head'], str(self.ui.label_5.text()) ) )
			self.ui.lineEdit_2.setText( config.get( self.namespace['config_head'], str(self.ui.label_2.text()) ) )
			#self.ui.spinBox_4.setValue( int( config.get( self.namespace['config_head'], str(self.ui.label_7.text()) ) ) )
			self.ui.doubleSpinBox.setValue( float( config.get( self.namespace['config_head'], str(self.ui.label_8.text()) ) ) )
			self.ui.checkBox.setCheckState( int( config.get( self.namespace['config_head'], str(self.ui.checkBox.text()) ) ) )
			self.ui.checkBox_2.setCheckState( int( config.get( self.namespace['config_head'], str(self.ui.checkBox_2.text()) ) ) )


	def save(self):
		tagname = self.ui.lineEdit_5.text()
		if len(tagname) == 0:
			utils.show_message("'Tag' should not be blank !")
			return
		elif '.' in tagname:
			utils.show_message("Please do not use '.' (dot) in tag name !")
			return

		if self.assignments not in Process_Settings.param.keys():
			Process_Settings.param[self.assignments] = {}
		Process_Settings.param[self.assignments][str(self.ui.label_9.text())] = str(self.ui.lineEdit_5.text())
		Process_Settings.param[self.assignments][str(self.ui.checkBox_2.text())] = self.ui.checkBox_2.checkState()

		if self.assignments == self.namespace['process_HF']:
			Process_Settings.param[self.assignments][str(self.ui.label.text())] = str(self.ui.lineEdit.text())
			Process_Settings.param[self.assignments][str(self.ui.label_5.text())] = str(self.ui.lineEdit_4.text())
			#Process_Settings.param[self.assignments][str(self.ui.label_2.text())] = str(self.ui.lineEdit_2.text())
			Process_Settings.param[self.assignments][str(self.ui.label_4.text())] = str(self.ui.lineEdit_3.text())
			Process_Settings.param[self.assignments][str(self.ui.label_3.text())] = [self.ui.spinBox.value(), self.ui.spinBox_2.value()]
			Process_Settings.param[self.assignments][str(self.ui.label_6.text())] = self.ui.spinBox_3.value()
			Process_Settings.param[self.assignments][str(self.ui.label_7.text())] = self.ui.spinBox_4.value()
		elif self.assignments == self.namespace['process_FA']:
			Process_Settings.param[self.assignments][str(self.ui.label.text())] = str(self.ui.lineEdit.text())
			Process_Settings.param[self.assignments][str(self.ui.label_5.text())] = str(self.ui.lineEdit_4.text())
			Process_Settings.param[self.assignments][str(self.ui.label_2.text())] = str(self.ui.lineEdit_2.text())
			Process_Settings.param[self.assignments][str(self.ui.label_4.text())] = str(self.ui.lineEdit_3.text())
			Process_Settings.param[self.assignments][str(self.ui.label_3.text())] = [self.ui.spinBox.value(), self.ui.spinBox_2.value()]
		elif self.assignments == self.namespace['process_FAA']:
			Process_Settings.param[self.assignments][str(self.ui.label.text())] = str(self.ui.lineEdit.text())
			Process_Settings.param[self.assignments][str(self.ui.label_5.text())] = str(self.ui.lineEdit_4.text())
			Process_Settings.param[self.assignments][str(self.ui.label_2.text())] = str(self.ui.lineEdit_2.text())
			Process_Settings.param[self.assignments][str(self.ui.label_6.text())] = self.ui.spinBox_3.value()
			#Process_Settings.param[self.assignments][str(self.ui.label_7.text())] = self.ui.spinBox_4.value()
		elif self.assignments == self.namespace['process_AP']:
			Process_Settings.param[self.assignments][str(self.ui.label.text())] = str(self.ui.lineEdit.text())
			Process_Settings.param[self.assignments][str(self.ui.label_5.text())] = str(self.ui.lineEdit_4.text())
			Process_Settings.param[self.assignments][str(self.ui.label_2.text())] = str(self.ui.lineEdit_2.text())
			#Process_Settings.param[self.assignments][str(self.ui.label_7.text())] = self.ui.spinBox_4.value()
			Process_Settings.param[self.assignments][str(self.ui.label_8.text())] = self.ui.doubleSpinBox.value()
			Process_Settings.param[self.assignments][str(self.ui.checkBox.text())] = self.ui.checkBox.checkState()

		# save ini
		config_file = self.get_config_path(self.assignments, tagname)
		utils.write_config(config_file, {self.namespace['config_head']:Process_Settings.param[self.assignments]},'w')
		self.close()


def parameters_setting(mainapp):
	settings = Process_Settings(mainapp)
	settings.show()














if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    myapp = Process_Settings("Hit-Finding")
    myapp.show()
    app.exec_()