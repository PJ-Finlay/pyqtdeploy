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


import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QSizePolicy, QSplitter, QTreeWidget,
        QTreeWidgetItem, QTreeWidgetItemIterator, QVBoxLayout, QWidget)

from ..parts import Part
from ..platforms import Architecture
from ..sysroot import Sysroot

from .better_form import BetterForm
from .filename_editor import FilenameEditor


class PackagesPage(QWidget):
    """ The GUI for the packages page of a project. """

    # The page's label.
    label = "Packages"

    def __init__(self):
        """ Initialise the page. """

        super().__init__()

        self._project = None
        self._part_items = {}
        self._has_openssl = False

        # Create the page's GUI.
        layout = QVBoxLayout()

        self._stdlib_edit = PartsEditor(self, "Standard Library",
                "This shows the packages and modules in the target Python "
                "version's standard library. Check those packages and modules "
                "that are explicitly imported by the application. A module "
                "will be partially checked (and automatically included) if "
                "another module requires it.")

        self._others_edit = PartsEditor(self, "Other Packages",
                "This shows the packages and modules that are "
                "available in the sysroot. Check those packages and modules "
                "that are explicitly imported by the application. A module "
                "will be partially checked (and automatically included) if "
                "another module requires it.")

        splitter = QSplitter()
        splitter.setSizePolicy(
                QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        splitter.addWidget(self._stdlib_edit)
        splitter.addWidget(self._others_edit)
        layout.addWidget(splitter)

        form = BetterForm()

        self._toml_edit = FilenameEditor("Sysroot specification file",
                placeholderText="Specification file name",
                whatsThis="The name of the sysroot specification file.",
                textEdited=self._toml_changed)
        form.addRow("Sysroot specification file", self._toml_edit)

        self._dir_edit = FilenameEditor("Sysroots Directory",
                placeholderText="Sysroots directory name",
                whatsThis="The name of the directory containing "
                        "target-specific sysroot directories.",
                textEdited=self._dir_changed, directory=True)
        form.addRow("Sysroots directory", self._dir_edit)

        layout.addLayout(form)

        self.setLayout(layout)

    @property
    def project(self):
        """ The project property getter. """

        return self._project

    @project.setter
    def project(self, value):
        """ The project property setter. """

        if self._project != value:
            self._project = value

            self._stdlib_edit.clear()
            self._others_edit.clear()

            self._toml_edit.set_project(value)
            self._dir_edit.set_project(value)

            self._update_page()

    def update_dependencies(self):
        """ Update the inter-part dependencies. """

        stdlib_blocked = self._stdlib_edit.blockSignals(True)
        others_blocked = self._others_edit.blockSignals(True)

        # The first pass is to clear any implicit parts.
        for part_item in self._part_items.values():
            if part_item.checkState(0) == Qt.PartiallyChecked:
                part_item.setCheckState(0, Qt.Unchecked)

        # The second pass is to set the state of any implicit parts.
        for part_item in self._part_items.values():
            if part_item.checkState(0) == Qt.Checked:
                self._set_implicit(part_item.parent())
                self._set_implicit_deps(part_item)
            elif part_item.part is not None and part_item.part.core:
                self._set_implicit(part_item)

        self._stdlib_edit.blockSignals(stdlib_blocked)
        self._others_edit.blockSignals(others_blocked)

    def _add_part(self, parent, part_name, part=None):
        """ Make sure a part appears in the dict of all parts. """

        unscoped_part_name = Part.get_unscoped_name(part_name)

        try:
            part_item = self._part_items[unscoped_part_name]

            # Update the part if it is currently just a place holder.
            if part_item.part is None:
                part_item.part = part
        except KeyError:
            part_item = PartItem(parent, part_name, part)
            self._part_items[unscoped_part_name] = part_item

        return part_item

    def _add_project_part(self, part_name, checked=True):
        """ Make sure a part is in the dict of all parts. """

        # Make sure any parent part items exist.
        if '.' in part_name:
            parent_name = '.'.join(part_name.split('.')[:-1])
            parent = self._add_project_part(parent_name, checked=False)
            parent.setExpanded(True)
        else:
            stdlib = Part.get_component_name(part_name) == 'Python'
            parent = (self._stdlib_edit if stdlib else self._others_edit)

        part_item = self._add_part(parent, part_name)

        if checked:
            part_item.setCheckState(0, Qt.Checked)

        return part_item

    def _dir_changed(self, value):
        """ Invoked when the user edits the sysroots directory name. """

        project = self.project

        project.absolute_sysroots_dir = value
        project.modified = True

        self._set_dir_edit_text()

    def _get_part_item(self, part_name, parts, stdlib):
        """ Return a PartItem object for a part or None if the part is
        internal.
        """

        # Ignore internal parts.
        part = parts.get(part_name)
        if part is not None and part.internal:
            return None

        # Make sure any parent part items exist.
        if '.' in part_name:
            parent_name = '.'.join(part_name.split('.')[:-1])
            parent = self._get_part_item(parent_name, parts, stdlib)
        else:
            parent = (self._stdlib_edit if stdlib else self._others_edit)

        return self._add_part(parent, part_name, part=part)

    def _set_dir_edit_text(self):
        """ Set the sysroots directory editor text. """

        self._dir_edit.setText(self.project.sysroots_dir)

    def _set_implicit(self, part_item):
        """ Set a part's state (and that of all it's parents) to be partially
        checked (unless it is already checked).
        """

        while part_item is not None:
            if part_item.checkState(0) == Qt.Unchecked:
                part_item.setCheckState(0, Qt.PartiallyChecked)

            part_item = part_item.parent()
            if part_item is not None:
                self._set_implicit_deps(part_item)

    def _set_implicit_deps(self, part_item):
        """ Set a part's state (and that of all it's dependents) to be
        partially checked (unless it is already checked).
        """

        if part_item.part is None:
            return

        for dep in part_item.part.deps:
            unscoped_dep = Part.get_unscoped_name(dep)
            dep_part_item = self._part_items.get(unscoped_dep)
            if dep_part_item is not None and dep_part_item.checkState(0) == Qt.Unchecked:
                self._set_implicit(dep_part_item)
                self._set_implicit_deps(dep_part_item)

    def _set_toml_edit_text(self):
        """ Set the sysroot secification editor text. """

        self._toml_edit.setText(self.project.sysroot_toml)

    def _toml_changed(self, value):
        """ Invoked when the user edits the specification file name. """

        project = self.project

        project.absolute_sysroot_toml = value
        project.modified = True

        self._set_toml_edit_text()

        project.load_sysroot()

        self._update_page()

    def _update_page(self):
        """ Update the page using the current project. """

        project = self.project

        self._set_toml_edit_text()
        self._set_dir_edit_text()

        # Create a non-verified sysroot for each target architecture and
        # determine the availability of each part.
        self._part_items.clear()
        host = Architecture.architecture()

        stdlib_blocked = self._stdlib_edit.blockSignals(True)
        others_blocked = self._others_edit.blockSignals(True)

        self._stdlib_edit.clear()
        self._others_edit.clear()

        if project.sysroot_specification is None:
            return

        self._has_openssl = False

        for target in Architecture.all_architectures:
            sysroot = Sysroot(project.sysroot_specification, host, target,
                    project.absolute_sysroots_dir)

            for component in sysroot.components:
                if component.name == 'OpenSSL':
                    self._has_openssl = True

                stdlib = (component.name == 'Python')

                parts = component.parts

                for part_name in parts:
                    part_item = self._get_part_item(part_name, parts,
                            stdlib)
                    if part_item is not None:
                        part_item.target_count += 1

        # Ensure that any parts explicitly used by the project have an item
        # even if they are not provided by the sysroot.
        for part_name in project.parts:
            self._add_project_part(part_name)

        # Set the availability of each part.
        for part_item in self._part_items.values():
            part_item.set_availability()

        # Sort part items in each editor.
        self._stdlib_edit.sortItems(0, Qt.AscendingOrder)
        self._others_edit.sortItems(0, Qt.AscendingOrder)

        # Update the dependencies.
        self.update_dependencies()

        self._stdlib_edit.blockSignals(stdlib_blocked)
        self._others_edit.blockSignals(others_blocked)


class PartsEditor(QTreeWidget):
    """ An editor for selecting a number of interdependent parts and packages.
    """

    def __init__(self, page, title, whats_this):
        """ Initialise the editor. """

        super().__init__(whatsThis=whats_this,
                itemChanged=self._part_changed)

        self._page = page

        self.setHeaderLabels([title])

    def _part_changed(self, itm, col):
        """ Invoked when a part changes. """

        page = self._page
        project = page.project
        parts = project.parts

        if itm.checkState(col) == Qt.Checked:
            parts.append(itm.part_name)
        else:
            parts.remove(itm.part_name)

        page.update_dependencies()

        project.modified = True


class PartItem(QTreeWidgetItem):
    """ An item in a QTreeWidget that encapsulates a public part. """

    # The colour to use for parts that aren't available for any target.
    _NO_TARGETS = QColor('#f00000')

    # The colour to use for parts that are only available for some targets.
    _SOME_TARGETS = QColor('#f08000')

    def __init__(self, parent, part_name, part):
        """ Initialise the item. """

        super().__init__(parent,
                Part.get_unscoped_name(part_name).split('.')[-1:])

        self.setFlags(Qt.ItemIsEnabled|Qt.ItemIsUserCheckable)
        self.setCheckState(0, Qt.Unchecked)

        self.part_name = part_name
        self.part = part
        self.target_count = 0

    def set_availability(self):
        """ Set the availability of the part. """

        if self.target_count == 0:
            self.setForeground(0, self._NO_TARGETS)
        elif self.target_count != len(Architecture.all_architectures):
            self.setForeground(0, self._SOME_TARGETS)
