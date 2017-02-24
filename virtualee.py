#! /usr/bin/python2.7
# -*- coding: latin-1 -*-

"""
Desktop client to download material from eie-virtual site and keep track of recent changes
    Copyright (C) 2017 Alexander Marin <alexanderm2230@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

import keyring
import json
import os
import sys
import requests
import time
import shutil
from PySide.QtGui import *
from PySide.QtCore import *
import gui.Sign_In as sign_in_gui
import gui.Sign_In_Empleo as sign_in_empleo_gui
import gui.Virtualee as virtualee_gui
import gui.Pref as pref
import gui.About as about
import gui.Download_Progress as down_prog
import lib.scrapeie as scrapeie
import lib.verctrl as verctrl
import lib.histdocs as histdocs

#############################################################################
# needed to show icon on taskbar on Windows 7 
if os.name == 'nt':
    try:
        import ctypes

        myappid = u'Vcompany.Vproduct.Vsubproduct.2.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass


#############################################################################
# Paths definitions of resources and needed folders/files

def path_rc(relative_path):
    """
    Path wrapper, add path of tmp folder.
    :param relative_path: relative path of resource.
    :return: Absolute path if running from tmp folder or relative path if not.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return relative_path




# Path definitions according to platform
if os.name == 'nt':
    # windows
    # form path of gui images and conf file
    about_img_path = path_rc(os.path.join('gui', 'virtualee.png'))
    sign_in_img_path = path_rc(os.path.join('gui', 'sign_in_img.png'))
    default_conf_path = path_rc('conf.json')

    conf_parent = os.path.join(os.environ['APPDATA'], "Virtualee")
    conf_path = os.path.join(conf_parent, "conf.json")
    hist_record_path = os.path.join(conf_parent, 'history.db')

    default_local_docs_name = "eie-virtual"
    default_local_docs_parent = os.environ['USERPROFILE']

elif os.name == 'posix':
    # linux
    # form path of gui images and conf file
    cur_path = os.path.dirname(os.path.abspath(__file__))

    about_img_path = os.path.join(cur_path, 'gui', 'virtualee.png')
    sign_in_img_path = os.path.join(cur_path, 'gui', 'sign_in_img.png')
    default_conf_path = os.path.join(cur_path, 'conf.json')

    conf_parent = os.path.join(os.environ['HOME'], ".virtualee")
    conf_path = os.path.join(conf_parent, "conf.json")
    hist_record_path = os.path.join(conf_parent, 'history.db')

    default_local_docs_name = "eie-virtual"
    default_local_docs_parent = os.environ['HOME']

    # if getattr(sys, 'frozen', False):
    #     # is running in bundle
    #     cur_path = sys.executable
    #     logo_path = path_rc(os.path.join('gui', 'icons', 'logo_virtualee.png'))
    #     # create/update desktop file
    #     import setup_launcher
    #
    #     setup_launcher.update_launcher(cur_path, logo_path)

else:
    print "Not supported system"
    exit(0)
#############################################################################


#############################################################################
#  methods for getting/setting config values

conf_params = {'username': '',
               'username_empleo': '',
               'local_eie': '',
               'check_time': 20}


def set_conf_val(name, value):
    """
    Assigns a particular value to a config parameter.
    :param name: name of config parameter.
    :param value: Value to be assigned to the parameter.
    :return: None.
    """
    with open(conf_path, 'r') as conf_file:
        config = json.load(conf_file)
    config.update({name: value})
    with open(conf_path, 'w') as conf_file:
        json.dump(config, conf_file)


def get_conf_val(name):
    """
    Returns value of a given parameter.
    :param name: name of desired parameter.
    :return: value of config parameter.
    """
    with open(conf_path, 'r') as conf_file:
        config = json.load(conf_file)
    try:
        config[name]
    except KeyError:
        if name in conf_params:
            config.update({name: conf_params[name]})  # if it doesn't exists then create param
        with open(conf_path, 'w') as conf_file:
            json.dump(config, conf_file)

    return config[name]


#############################################################################


#############################################################################
# Initial setup at runtime
def setup():
    """
    Creates config file and eie-virtual folder.
    :return: None.
    """
    # if no config exists it must be created
    if not os.path.exists(conf_parent):
        os.makedirs(conf_parent)

    if not os.path.isfile(conf_path):
        shutil.copyfile(default_conf_path, conf_path)
        # set default local copy dir
        set_conf_val("local_eie", os.path.join(default_local_docs_parent, default_local_docs_name))

    # if eie-virtual directory doesn't exist it must be created
    curr_local_eie = get_conf_val('local_eie')
    if not os.path.exists(curr_local_eie):
        os.makedirs(curr_local_eie)


#############################################################################


#############################################################################
# Main window
class Virtualee(QMainWindow, virtualee_gui.Ui_MainWindow):
    signal_text = Signal(str)

    def __init__(self, parent=None):
        super(Virtualee, self).__init__(parent)
        self.setupUi(self)

        self.center()
        self.tabWidget.setCurrentIndex(0)
        self.empleo_lastcheck = 0.0

        # load credentials of eie virtual
        self.username = get_conf_val('username')
        self.password = keyring.get_password('eie-virtual', self.username)
        self.fullname = ""
        self.sce = scrapeie.ScrapEie()
        self.sce.set_cred(self.username, self.password)

        # load credentials of empleo eie
        self.seie_empleo = scrapeie.ScrapEmpleo()
        self.seie_empleo.set_creds(get_conf_val("username_empleo"),
                                   keyring.get_password('eie-empleo', get_conf_val("username_empleo")))

        # file downloads history manager
        self.hmg = histdocs.HistMg(hist_record_path)

        # version control manager
        self.vc = verctrl.VControl(self.sce, self.hmg)

        # thread to download new documents
        self.update_thread = UpdateDocsThread(self.vc)

        # creates sign in dialog for eie virtual
        self.sign_d = SignInDialog(self)

        # additional dialogs
        self.ab = AboutDialog(self)
        self.pref = PrefDialog(self)
        self.down_diag = DownloadDialog(self)

        # attempts to sign in
        if not self.log_in():
            self.sign_d.show()
        else:
            self.show_main_w()  # then show main window of virtualee

        # signals/slots
        self.connect(self.sign_d, SIGNAL("logged()"), self.show_main_w)  # shows main window
        # tells when sign in to eie-empleo is successful
        self.connect(self.clear_hist_btn, SIGNAL("clicked()"), self.clear_hist)  # erase history
        self.actionUpdate.triggered.connect(self.update_docs)  # begin update
        self.actionSign_out.triggered.connect(self.sign_out)  # sign out
        self.actionAbout.triggered.connect(self.showabout)  # show about window
        self.actionPreferences.triggered.connect(self.chpref)  # show preference editor
        self.actionExit.triggered.connect(sys.exit)  # exit program
        # tells when a different course is selected
        self.courses_list.currentItemChanged.connect(self.refresh_recent_list)
        self.tabWidget.currentChanged.connect(self.updatetabs)  # tells when current news tab is changed

        # signals/slots
        self.connect(self.update_thread, SIGNAL("setsize(int)"), self.set_current_progress)  # set current progress
        self.connect(self.update_thread, SIGNAL("setfinalsize(int)"), self.set_max_progress)  # set max of progress bar
        self.connect(self.down_diag.stop_down_btn, SIGNAL("clicked()"),
                     self.terminating_download)  # stops current update
        self.connect(self.down_diag, SIGNAL("stop_update()"), self.terminating_download)
        self.connect(self.update_thread, SIGNAL("finished()"), self.update_done)  # tells when update thread completes
        self.connect(self.down_diag.close_diag_btn, SIGNAL("clicked()"), self.down_diag.close)  # close dialog
        self.update_thread.signal_text.connect(self.add_line)  # add text to text browser


        # used to show error messages
        self.errbox = QErrorMessage()
        self.errbox.setWindowTitle("Error")

    def done_empleo_log(self):
        """
        Must be called after a successful login on eie-empleo, closes login dialog an refresh
        job announcements.
        :return: None.
        """
        self.empleod.close()
        self.refresh_anns_empleo()
        self.empleo_lastcheck = time.time()

    def sign_in_empleo(self):
        """
        Must be called to show a dialog where the user may enter his credentials.
        :return: None.
        """
        # create dialog for empleo sign in
        self.empleod = SignInEmpleoDialog(self.seie_empleo, self)
        self.empleod.show()

        self.connect(self.empleod, SIGNAL("logged_empleo()"), self.done_empleo_log)

    def updatetabs(self):
        """
        Updates news on tabs, depending on which is selected.
        :return: None.
        """
        # wait at least 300 seconds between updates
        if time.time() - self.empleo_lastcheck < 300.0:
            return

        if self.tab_jobs.isVisible():
            if self.refresh_anns_empleo():
                self.empleo_lastcheck = time.time()

        elif self.tab_eie.isVisible():
            self.refresh_anns_eieucr()

    @staticmethod
    def clear_layout(layout):
        """
        Removes all widgets from a layout.
        :param layout:
        :return: None.
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def refresh_anns_empleo(self):
        """
        Updates announcements on jobs tab.
        :return: Bool, True when news fetch from site is successful, False in opposite case.
        """
        try:
            if not self.seie_empleo.log_in():
                self.reset_jobs_prompt()
                return False

        except requests.ConnectionError:
            print "Connection error: Couldn't fetch news on eie main page"
            return False

        # scrap news from site
        news_list = self.seie_empleo.get_job_anns()

        # reset layout
        self.clear_layout(self.layout_jobs)

        # adds horizontal line
        hline = QFrame(self.scroll_area_jobs)
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Sunken)
        self.layout_jobs.addWidget(hline)

        for n in news_list:
            # add one announcement
            ann_label = QLabel(self.scroll_area_jobs)
            ann_label.setOpenExternalLinks(True)
            ann_label.setWordWrap(True)
            ann_label.setText(u'{0}'.format(n))
            self.layout_jobs.addWidget(ann_label)

            # add one horizontal line
            hline = QFrame(self.scroll_area_jobs)
            hline.setFrameShape(QFrame.HLine)
            hline.setFrameShadow(QFrame.Sunken)
            self.layout_jobs.addWidget(hline)

        # add spacer
        spacer_item = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout_jobs.addItem(spacer_item)

        return True

    def reset_jobs_prompt(self):
        """
        Adds a text label and button to open dialog for eie-empleo sign in.
        :return: None.
        """
        # clear layout
        self.clear_layout(self.layout_jobs)

        # add text info
        self.sign_empleo_label = QLabel(self.scrollAreaWidgetContents_2)
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sign_empleo_label.sizePolicy().hasHeightForWidth())
        self.sign_empleo_label.setSizePolicy(size_policy)
        self.sign_empleo_label.setWordWrap(True)
        self.sign_empleo_label.setObjectName("sign_empleo_label")
        self.layout_jobs.addWidget(self.sign_empleo_label)
        self.sign_empleo_label.setText(QApplication.translate("MainWindow",
                                                              "Sign in to view last job offers on empleo.eie.ucr.ac.cr",
                                                              None,
                                                              QApplication.UnicodeUTF8))

        # add button for sign in
        self.sign_in_empleo_btn = QPushButton(self.scrollAreaWidgetContents_2)
        self.sign_in_empleo_btn.setObjectName("sign_in_empleo_btn")
        self.layout_jobs.addWidget(self.sign_in_empleo_btn)
        spacer_item = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout_jobs.addItem(spacer_item)
        self.sign_in_empleo_btn.setText(QApplication.translate("MainWindow",
                                                               "Sign In",
                                                               None,
                                                               QApplication.UnicodeUTF8))

        # will open sign in dialog for eie-empleo when sign in button is clicked
        self.connect(self.sign_in_empleo_btn, SIGNAL("clicked()"), self.sign_in_empleo)

    def refresh_anns_eieucr(self):
        """
        Update announcements of eie mainpage.
        :return: Bool, True when news fetch from site is successful, False in opposite case.
        """
        try:
            news = scrapeie.get_anns()
        except requests.ConnectionError:
            print "Connection error: Couldn't fetch news on eie main page"
            return False

        # reset layout
        self.clear_layout(self.layout_eie_ans)

        # adds horizontal line
        hline = QFrame(self.scroll_area_eie)
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Sunken)
        self.layout_eie_ans.addWidget(hline)

        for n in news:
            # add one announcement
            ann_label = QLabel(self.scroll_area_eie)
            ann_label.setOpenExternalLinks(True)
            ann_label.setWordWrap(True)
            ann_label.setText(u'{0}\n{1}'.format(n, news[n]))
            self.layout_eie_ans.addWidget(ann_label)

            # add horizontal line
            hline = QFrame(self.scroll_area_eie)
            hline.setFrameShape(QFrame.HLine)
            hline.setFrameShadow(QFrame.Sunken)
            self.layout_eie_ans.addWidget(hline)

        # add spacer
        spacer_item = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout_eie_ans.addItem(spacer_item)
        return True

    def center(self):
        """
        Centers the main window.
        :return: None.
        """
        frame_gm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())

    def show_main_w(self):
        """
        Closes sign-in dialog and setups main window.
        :return: None.
        """
        self.sign_d.close()
        self.show()

        # welcome message
        self.statusbar.showMessage("Welcome {0}".format(self.fullname))

        # update news
        self.refresh_lists()
        self.updatetabs()
        self.reset_jobs_prompt()

    def refresh_lists(self):
        """
        Reloads contents of courses and recent-files lists.
        :return: None.
        """
        # populates list of courses on main window
        self.courses_list.clear()
        self.sce.get_course_list()
        self.courses_list.addItem("All")
        for c in self.sce.name_courses:
            self.courses_list.addItem(c)

        # resize window given size of items, then show
        self.courses_list.setMinimumWidth(self.courses_list.sizeHintForColumn(0))
        self.courses_list.show()

        # sets cursor and refresh recent files list
        self.courses_list.setCurrentRow(0)
        self.refresh_recent_list()

    def refresh_recent_list(self):
        """
        Loads contents of recent-files list from history file.
        :return: None.
        """
        if not self.courses_list.currentItem():
            return
        self.recent_files.clear()
        selection_rlist = self.courses_list.currentItem().text()

        if selection_rlist == "All":
            # show recent files of all courses
            hist_items = self.hmg.get_entries()
        else:
            # show recent files of only selected course
            hist_items = self.hmg.get_entries(selection_rlist)

        # last elements must be shown first
        hist_items.reverse()

        # adds all recent items to list
        for hitem in hist_items:
            self.recent_files.addItem(hitem['filename'])

    def clear_hist(self):
        """
        Erases history of selected course.
        :return: None.
        """
        selection_rlist = self.courses_list.currentItem().text()
        if selection_rlist == "All":
            # delete recent history of all courses
            self.hmg.clear_hist()
        else:
            # delete recent history of only selected course
            self.hmg.clear_hist(selection_rlist)
        # update list of main window
        self.refresh_recent_list()

    def update_docs(self):
        """
        Update local copy of files and updates recent-files list according to new changes.
        :return: None.
        """
        self.down_diag.show()

        # disable close button and enable stop button
        self.down_diag.close_diag_btn.setEnabled(False)
        self.down_diag.stop_down_btn.setEnabled(True)

        # reset widgets
        self.down_diag.progressBar.setValue(0)
        self.down_diag.progressBar.show()
        self.down_diag.update_info.clear()

        self.update_thread.start()

    def update_done(self):
        """
        Must be called after successful update, disables stop button and enables close dialog button.
        :return: None.
        """
        self.down_diag.stop_down_btn.setEnabled(False)
        self.down_diag.close_diag_btn.setEnabled(True)
        self.refresh_lists()

    def terminating_download(self):
        """
        Interrupts download process, waits for last download to complete.
        :return: None.
        """
        self.down_diag.stop_down_btn.setEnabled(False)
        self.update_thread.set_stopflg()

    def set_current_progress(self, curr_value):
        """
        Sets current value of progress bar.
        :param curr_value: Int, depends on the maximum previously assigned.
        :return: None.
        """
        self.down_diag.progressBar.setValue(curr_value)

    def set_max_progress(self, max_value):
        """
        Sets maximum of progress bar, in case there is nothing to download, show message on dialog.
        :param max_value: Int, may be size(bytes) or amount of files.
        :return: None.
        """
        if max_value == 0:
            self.down_diag.progressBar.hide()
        else:
            self.down_diag.progressBar.setMaximum(max_value)

    @Slot(str)
    def add_line(self, text_out):
        """
        Adds a new line to text browser of download dialog.
        :param text_out: String, feedback of current update progress.
        :return: None.
        """
        self.down_diag.update_info.append(text_out)
        self.down_diag.update_info.show()

    def sign_out(self):
        """
        Deletes pass/user and shows sign-in dialog.
        :return: None.
        """
        # erase user and keyring
        try:
            keyring.delete_password("eie-virtual", get_conf_val('username'))
            set_conf_val('username', '')
            self.sce.set_cred("", "")
        except keyring.errors.PasswordDeleteError as err:
            None

        try:
            keyring.delete_password("eie-empleo", get_conf_val('username_empleo'))
            set_conf_val('username_empleo', '')
            self.seie_empleo.set_creds("", "")
        except keyring.errors.PasswordDeleteError as err:
            None

        # create new sign in dialog and wait for sign in
        self.sign_d = SignInDialog(self)
        self.connect(self.sign_d, SIGNAL("logged()"), self.show_main_w)
        self.hide()
        self.sign_d.show()

    def showabout(self):
        """
        Shows about dialog.
        :return: None.
        """
        self.ab.show()

    def chpref(self):
        """
        Shows preferences dialog.
        :return: None.
        """
        self.pref.show()

    def log_in(self):
        """
        Signs in to eie-virtual site with a pass/user previously set.
        :return: Boolean, True if sign-in was successful.
        """
        self.fullname = self.sce.log_in()
        # full name of user is used to check if we are logged in
        if self.fullname:
            return True
        else:
            return False

#############################################################################


#############################################################################
# Related to update of documents
class UpdateDocsThread(QThread, Virtualee):
    def __init__(self, vc):
        QThread.__init__(self)
        self.stopflg = False
        self.vc = vc
        self.finalsize = 0
        self.size = 0

    def run(self):
        """
        Begins material update process.
        :return: None.
        """
        self.stopflg = False
        try:
            # calculates total bytes to download
            self.finalsize = self.vc.estimate_size(get_conf_val('local_eie'))
            self.emit(SIGNAL('setfinalsize(int)'), self.finalsize)
            self.size = 0
            if self.finalsize:
                self.update_all(get_conf_val('local_eie'))
            else:
                self.signal_text.emit("Nothing to download")

        except requests.ConnectionError:
            self.signal_text.emit("Connection error")

    def set_stopflg(self):
        """
        Sets stop flag.
        :return: None.
        """
        self.stopflg = True

    def update_all(self, dest):
        """
        Updates local copy of all courses.
        :param dest: path to local copy.
        :return: None.
        """
        self.vc.sce.get_course_list()
        text_output = "Got course list"
        self.signal_text.emit(text_output)

        cloud_trees = []

        # update each course
        for c in self.vc.sce.nameurl_courses:
            # parse cloud course materials
            text_output = u"Parsing cloud materials of : {0}".format(c)
            self.signal_text.emit(text_output)
            cloud_trees.append(self.vc.sce.gen_cloud_tree(c, self.vc.sce.nameurl_courses[c]))
            # update local copy of one course
            self.update_local_docs(dest, cloud_trees[-1], c)

        if self.stopflg:
            text_output = "Update interrupted"
        else:
            text_output = "Update done"

        self.signal_text.emit(text_output)

    def update_local_docs(self, dest, cloud_node, course_name):
        """
        Updates a dir level of the local copy of course materials.
        :param course_name: course name.
        :param dest: parent directory path.
        :param cloud_node: Node object, made with found materials in eie-virtual site.
        :return: None.
        """
        current_path = os.path.join(dest, cloud_node.name)
        # checks if current directory exist
        if not os.path.exists(current_path):
            os.makedirs(current_path)
            # then downloads all materials
            for f in cloud_node.files:
                if self.stopflg:
                    return
                self.vc.sce.download_file(f.url, os.path.join(current_path, f.name))  # download file
                self.vc.add2hist(f.name, course_name, time.time())  # add event to history db

                # update current progress
                self.size += self.vc.sce.get_file_size(f.url)
                self.emit(SIGNAL('setsize(int)'), self.size)
                text_output = "Downloaded {0}".format(f.name)
                self.signal_text.emit(text_output)
        else:
            # downloads materials in case don't exist in current copy
            for f in cloud_node.files:
                if self.stopflg:
                    return
                curr_file_path = os.path.join(current_path, f.name)

                # if doc doesn't exists, then download it
                if not os.path.isfile(curr_file_path):
                    self.vc.sce.download_file(f.url, curr_file_path)
                    self.vc.add2hist(f.name, course_name, time.time())

                    # update current progress
                    self.size += self.vc.sce.get_file_size(f.url)
                    self.emit(SIGNAL('setsize(int)'), self.size)
                    text_output = "Downloaded {0}".format(f.name)
                    self.signal_text.emit(text_output)

                else:
                    # if sizes don't match, then download doc
                    cloud_file_size = self.vc.sce.get_file_size(f.url)
                    local_file_size = int(os.stat(curr_file_path).st_size)
                    if cloud_file_size != local_file_size:
                        self.vc.sce.download_file(f.url, curr_file_path)
                        self.vc.add2hist(f.name, course_name, time.time())

                        # update current progress
                        self.size += cloud_file_size
                        self.emit(SIGNAL('setsize(int)'), self.size)
                        text_output = "Downloaded {0}".format(f.name)
                        self.signal_text.emit(text_output)

        # does the same for next level of subdirectories
        for node in cloud_node.dirs:
            if self.stopflg:
                return
            self.update_local_docs(current_path, node, course_name)
#############################################################################


#############################################################################
# Sign in eie-virtual dialog
class SignInDialog(QDialog, sign_in_gui.Ui_SignInDialog):
    def __init__(self, m, parent=None):
        super(SignInDialog, self).__init__(parent)
        self.setupUi(self)

        # top image
        self.image = QPixmap(sign_in_img_path)
        self.sign_img_lab.setPixmap(self.image)

        self.connect(self.signin_btn, SIGNAL("clicked()"), self.sign_in)
        self.mainw = m

    def sign_in(self):
        """
        Carries sign-in with user/pass given on dialog fields.
        :return: None.
        """
        # values from dialog
        username = str(self.user_ledit.text())
        password = str(self.pass_ledit.text())

        # checks for sign-in success
        self.mainw.sce.set_cred(username, password)
        if not self.mainw.log_in():
            self.show()
            self.warn_cred.setText("<font color='red'>Wrong username/password!</font>")
        else:
            # sign-in successful
            if self.cb_remember.isChecked():
                # if remember then save pass and user
                keyring.set_password("eie-virtual", username, password)
                set_conf_val('username', username)
            # success, so emit signal and hide sign in dialog
            self.hide()
            self.emit(SIGNAL("logged()"))
#############################################################################


#############################################################################
# Sign in eie-empleo dialog
class SignInEmpleoDialog(QDialog, sign_in_empleo_gui.Ui_SignInEmpleoDialog):
    def __init__(self, scem, parent=None):
        super(SignInEmpleoDialog, self).__init__(parent)
        self.setupUi(self)
        self.scem = scem
        self.connect(self.signin_btn, SIGNAL("clicked()"), self.sign_in)

    def sign_in(self):
        """
        Carries sign-in with user/pass given on dialog fields.
        :return: None.
        """
        # values from dialog
        username = str(self.user_ledit.text())
        password = str(self.pass_ledit.text())

        # checks for sign-in success
        self.scem.set_creds(username, password)
        if not self.scem.log_in():
            self.warn_cred.setText("<font color='red'>Wrong username/password!</font>")
        else:
            # sign-in successful
            if self.cb_remember.isChecked():
                # if remember then save pass and user
                keyring.set_password("eie-empleo", username, password)
                set_conf_val('username_empleo', username)
            # success, so emit signal and hide sign in dialog
            self.hide()
            self.emit(SIGNAL("logged_empleo()"))
#############################################################################


#############################################################################
# Dialog for setting preferences
class PrefDialog(QDialog, pref.Ui_Dialog):
    def __init__(self, parent=None):
        super(PrefDialog, self).__init__(parent)
        self.setupUi(self)

        self.local_docs_dir_parent = ""
        self.local_docs_dir = ""

        # button signals/slots
        # save changes for click in save button
        save_btn = self.pref_box.button(QDialogButtonBox.Save)
        save_btn.clicked.connect(self.save_prefs)
        # ignore changes for click in cancel button
        cancel_btn = self.pref_box.button(QDialogButtonBox.Cancel)
        cancel_btn.clicked.connect(self.cancel_prefs)
        # select dir
        self.connect(self.choose_root, SIGNAL("clicked()"), self.select_dir)

        self.load_current_prefs()  # load current values to dialog widgets

        self.errbox = QErrorMessage()  # used to show error messages
        self.errbox.setWindowTitle("Error")

    def select_dir(self):
        """
        Lets the user choose a destination directory for eie-virtual folder.
        :return: None.
        """
        tmp_dir = str(QFileDialog.getExistingDirectory(self, "Select directory for course materials"))
        if tmp_dir:
            self.local_docs_dir_parent = tmp_dir
            self.local_docs_dir_ledit.setText(os.path.join(tmp_dir, default_local_docs_name))

    def save_prefs(self):
        """
        Saves the current fields of preferences dialog.
        :return: None.
        """
        self.hide()
        try:
            # moves current eie-virtual folder to new destination
            if self.local_docs_dir != os.path.join(self.local_docs_dir_parent, default_local_docs_name):
                shutil.move(self.local_docs_dir, self.local_docs_dir_parent)
        except shutil.Error as err:
            self.errbox.showMessage(err.message)
            self.load_current_prefs()
            return

        # store new config values
        set_conf_val('check_time', self.minutes_spin.value())
        set_conf_val('local_eie', os.path.join(self.local_docs_dir_parent, default_local_docs_name))
        # load config values on dialog fields
        self.load_current_prefs()

    def cancel_prefs(self):
        """
        Ignores fields and hides preferences dialog.
        :return: None.
        """
        self.load_current_prefs()
        self.hide()

    def load_current_prefs(self):
        """
        Loads config values onto dialog fields.
        :return: None.
        """
        # set spin value from config
        self.minutes_spin.setValue(get_conf_val('check_time'))
        # set line edit(docs path) from config
        self.local_docs_dir_ledit.setText(get_conf_val('local_eie'))
        # update paths
        self.local_docs_dir = get_conf_val('local_eie')
        self.local_docs_dir_parent = os.path.split(self.local_docs_dir)[0]
#############################################################################


#############################################################################
# Dialog to show update progress and feedback
class DownloadDialog(QDialog, down_prog.Ui_Dialog):
    def __init__(self, parent=None):
        super(DownloadDialog, self).__init__(parent)
        self.setupUi(self)

    def closeEvent(self, event):
        """
        Emits signal to indicate that current update must be stopped.
        :param event:
        :return: None.
        """
        self.emit(SIGNAL("stop_update()"))
        event.accept()

#############################################################################


#############################################################################
# Contact dialog
class AboutDialog(QDialog, about.Ui_Dialog):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setupUi(self)

        # top image
        self.image = QPixmap(about_img_path)
        self.virtualee_img.setPixmap(self.image)
        # contact
        self.info.setText("\nVirtualee 2.0\n\n"
                          "If you find bugs, have comments or\n"
                          " questions please send an email to\n"
                          "virtualeecr@gmail.com\n"
                          "I'll be grateful to any suggestions, except those about changing that logo :v\n"
                          "\nAuthor:\n"
                          "Alexander Marin Drobinoga\n"
                          "\nLicensed under GPLv3\n")
#############################################################################


def main():
    setup()
    app = QApplication(sys.argv)
    v = Virtualee()
    app.exec_()


if __name__ == "__main__":
    main()
