from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'pygui'))

from configparser import ConfigParser
from functools import partial

import utils
from menu_jobctl_gui import Ui_Dialog as jobctl_Dialog


class _MyMenu(QtWidgets.QDialog, QtCore.QEvent):

    menu_types = ["jobctl"]

    def __init__(self, menu_type, workpath, params):
        QtWidgets.QWidget.__init__(self)
        self.workpath = workpath
        self.params = params
        # setup ui
        if str(menu_type) == _MyMenu.menu_types[0]:
            # jobctl
            self.ui = jobctl_Dialog()
            self.ui.setupUi(self)
            self.menu_type = 0
            self.ui.buttonBox.accepted.connect(self.jobctl_OK)
            self.ui.buttonBox.rejected.connect(self.jobctl_Cancel)
            # write value
            try:
                proj_conf = utils.read_config(os.path.join(self.workpath, self.params['ini']))
            except Exception as err:
                utils.show_message("Fail to load project initial file !", str(err))
            try:
                pat_per_job = int(proj_conf.get(self.params['project_ini'][0], self.params['project_ini'][1].split(',')[4]))
                self.ui.spinBox_2.setValue(pat_per_job)
                max_jobs = int(proj_conf.get(self.params['project_ini'][0], self.params['project_ini'][1].split(',')[5]))
                self.ui.spinBox.setValue(max_jobs)
                monitor_time = int(proj_conf.get(self.params['project_ini'][0], self.params['project_ini'][1].split(',')[6]))
                self.ui.spinBox_3.setValue(monitor_time)
            except:
                utils.show_warning("project initial file is incomplete !")
        else:
            utils.show_message("Menu type %s is invalid !" % str(menu_type))
            self.close()

    def jobctl_OK(self):
        # reset appini
        max_jobs = self.ui.spinBox.value()
        pat_per_job = self.ui.spinBox_2.value()
        monitor_time = self.ui.spinBox_3.value()
        inifile = os.path.join(self.workpath, self.params['ini'])
        config_name = self.params['project_ini'][0]
        config_item = self.params['project_ini'][1].split(',')
        try:
            utils.write_config(inifile, \
                        {config_name : \
                        {config_item[4] : pat_per_job, \
                        config_item[5] : max_jobs, \
                        config_item[6] : monitor_time}}, \
                        mode="a")
            utils.show_message("Save successfully !")
            utils.print2projectLog(self.workpath, \
                "Modify project configuration : %s = %d, %s = %d, %s = %d" \
                % (config_item[4], pat_per_job, config_item[5], max_jobs, config_item[6], monitor_time))
        except Exception as err:
            utils.show_message("Fail to save !", str(err))

    def jobctl_Cancel(self):
        self.close()


def jobctl(workpath, namespace):
    mymenu = _MyMenu(_MyMenu.menu_types[0], workpath, namespace)
    mymenu.setModal(True)
    mymenu.exec_()