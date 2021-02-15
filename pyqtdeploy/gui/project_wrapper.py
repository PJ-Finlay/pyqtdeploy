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


from PyQt5.QtCore import QObject, pyqtSignal


class ProjectWrapper(QObject):
    """ A wrapper around a project that handles GUI-driven change
    notifications.
    """

    def __init__(self, project):
        """ Initialise the wrapper. """

        super().__init__()

        self._project = project

        self._modified = False

    # Emitted when the modification state of the project changes.
    modified_changed = pyqtSignal(bool)

    @property
    def modified(self):
        """ The modified property getter. """

        return self._modified

    @modified.setter
    def modified(self, value):
        """ The modified property setter. """

        self._modified = value

        self.modified_changed.emit(value)

    # Emitted when the name of the project changes.
    name_changed = pyqtSignal(str)

    @property
    def name(self):
        """ The name property getter. """

        return self._project.name

    @name.setter
    def name(self, value):
        """ The name property setter. """

        self._project.name = value

        self.name_changed.emit(self._project.name)

    def save(self):
        """ Save the project. """

        self._project.save()
        self.modified = False

    def save_as(self, name):
        """ Save the project under a new name. """

        self._project.save_as(name)
        self.modified = False

        self.name_changed.emit(self._project.name)

    def __getattr__(self, name):
        """ Reimplemented to get any unknown attributes from the project. """

        return getattr(self._project, name)

    def __setattr__(self, name, value):
        """ Reimplemented to set any unknown attributes in the project. """

        # See if the attribute is really implemented by the wrapper.
        if name in ('modified', 'name') or name.startswith('_'):
            super().__setattr__(name, value)
        else:
            setattr(self._project, name, value)
