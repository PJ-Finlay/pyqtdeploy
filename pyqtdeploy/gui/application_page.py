# Copyright (c) 2020, Riverbank Computing Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontInfo, QGuiApplication
from PyQt5.QtWidgets import (QCheckBox, QFileDialog, QGridLayout, QGroupBox,
        QLineEdit, QPlainTextEdit, QWidget)

from .better_form import BetterForm
from .collapsible_widget import CollapsibleWidget
from .filename_editor import FilenameEditor
from .package_editor import PackageEditor


class ApplicationPage(QWidget):
    """ The GUI for the application page of a project. """

    # The page's label.
    label = "Application Source"

    @property
    def project(self):
        """ The project property getter. """

        return self._project

    @project.setter
    def project(self, value):
        """ The project property setter. """

        if self._project != value:
            self._project = value
            self._script_edit.set_project(value)
            self._package_edit.set_project(value)
            self._update_page()

    def __init__(self):
        """ Initialise the page. """

        super().__init__()

        self._project = None

        # Create the page's GUI.
        layout = QGridLayout()

        form = BetterForm()

        self._name_edit = QLineEdit(
                placeholderText="Application name",
                whatsThis="The name of the application. It will default to "
                        "the base name of the application script without any "
                        "extension.",
                textEdited=self._name_changed)
        form.addRow("Name", self._name_edit)

        self._script_edit = FilenameEditor("Application Script",
                placeholderText="Application script",
                whatsThis="The name of the application's optional main script "
                        "file.",
                textEdited=self._script_changed)
        form.addRow("Main script file", self._script_edit)

        self._entry_point_edit = QLineEdit(
                placeholderText="Entry point in application package",
                whatsThis="The name of the optional entry point in the "
                        "application's package.",
                textEdited=self._entry_point_changed)
        form.addRow("Entry point", self._entry_point_edit)

        self._sys_path_edit = QLineEdit(
                placeholderText="Additional sys.path directories",
                whatsThis="A space separated list of additional directories, "
                        "ZIP files and eggs to add to <tt>sys.path</tt>. Only "
                        "set this if you want to allow external packages to "
                        "be imported.",
                textEdited=self._sys_path_changed)
        form.addRow("sys.path", self._sys_path_edit)

        layout.addLayout(form, 0, 0)

        options_layout = BetterForm()

        self._console_edit = QCheckBox("Use console (Windows)",
                whatsThis="Enable console output for Windows applications. "
                        "Console output will be enabled automatically if no "
                        "graphical PyQt modules are used.",
                stateChanged=self._console_changed)
        options_layout.addRow(self._console_edit)

        self._bundle_edit = QCheckBox("Application bundle (macOS)",
                whatsThis="Build an application bundle on macOS. If it is not "
                        "checked then the application will be built as a "
                        "simple executable.",
                stateChanged=self._bundle_changed)
        options_layout.addRow(self._bundle_edit)

        layout.addLayout(options_layout, 0, 1)

        # Extra space is needed before the application package editor.
        layout.setRowMinimumHeight(1,
                1.4 * QFontInfo(QGuiApplication.font()).pixelSize())

        self._package_edit = _ApplicationPackageEditor()
        self._package_edit.package_changed.connect(self._package_changed)
        package_edit_gb = QGroupBox(self._package_edit.title)
        package_edit_gb.setFlat(True)
        package_edit_gb.setLayout(self._package_edit)
        layout.addWidget(package_edit_gb, 2, 0, 1, 2)

        qmake = CollapsibleWidget("Additional qmake Configuration")
        self._qmake_edit = QPlainTextEdit(
                whatsThis="Any text entered here will be appended to the "
                        "generated <tt>.pro</tt> that will be processed by "
                        "<tt>qmake</tt>.",
                textChanged=self._qmake_changed)
        qmake.setWidget(self._qmake_edit)
        layout.addWidget(qmake, 3, 0, 1, 2)

        self.setLayout(layout)

    def _update_page(self):
        """ Update the page using the current project. """

        project = self.project

        self._name_edit.setText(project.application_name)
        self._script_edit.setText(project.application_script)
        self._entry_point_edit.setText(project.application_entry_point)
        self._sys_path_edit.setText(project.sys_path)
        self._package_edit.configure(project.application_package, project)

        blocked = self._console_edit.blockSignals(True)
        self._console_edit.setCheckState(
                Qt.Checked if project.application_is_console else Qt.Unchecked)
        self._console_edit.blockSignals(blocked)

        blocked = self._bundle_edit.blockSignals(True)
        self._bundle_edit.setCheckState(
                Qt.Checked if project.application_is_bundle else Qt.Unchecked)
        self._bundle_edit.blockSignals(blocked)

        blocked = self._qmake_edit.blockSignals(True)
        self._qmake_edit.setPlainText(self._project.qmake_configuration)
        self._qmake_edit.blockSignals(blocked)

    def _console_changed(self, state):
        """ Invoked when the user changes the console state. """

        self.project.application_is_console = (state == Qt.Checked)
        self.project.modified = True

    def _bundle_changed(self, state):
        """ Invoked when the user changes the bundle state. """

        self.project.application_is_bundle = (state == Qt.Checked)
        self.project.modified = True

    def _name_changed(self, value):
        """ Invoked when the user edits the application name. """

        self.project.application_name = value
        self.project.modified = True

    def _script_changed(self, value):
        """ Invoked when the user edits the application script name. """

        self.project.application_script = value
        self.project.modified = True

    def _entry_point_changed(self, value):
        """ Invoked when the user edits the entry point. """

        self.project.application_entry_point = value
        self.project.modified = True

    def _sys_path_changed(self, value):
        """ Invoked when the user edits the sys.path directories. """

        self.project.sys_path = value.strip()
        self.project.modified = True

    def _package_changed(self):
        """ Invoked when the user edits the application package. """

        self.project.modified = True

    def _qmake_changed(self):
        """ Invoked when the user edits the qmake configuration. """

        self.project.qmake_configuration = self._qmake_edit.toPlainText()
        self.project.modified = True


class _ApplicationPackageEditor(PackageEditor):
    """ A memory filesystem package editor for the application package. """

    # The editor title.
    title = "Application Package Directory"

    def __init__(self):
        """ Initialise the editor. """

        super().__init__(show_root=True, scan="Scan...",
                scan_whats_this="Display a dialog from which you can select "
                        "the application package directory.",
                whats_this="This shows the scanned application package "
                        "directory and its contents. Check those directories "
                        "and files that should be included in the "
                        "application.")

        self.setContentsMargins(0, 0, 0, 0)

        self._project = None

    def get_root_dir(self):
        """ Get the name of the application directory. """

        project = self._project
        application_package = project.application_package

        default = application_package.name
        if default is not None:
            default = project.project_path(default)

        root = QFileDialog.getExistingDirectory(self.parentWidget(),
                self.title, default)

        if root != '':
            application_package.name = project.minimal_path(root)

        return root

    def set_project(self, project):
        """ Set the project. """

        self._project = project
