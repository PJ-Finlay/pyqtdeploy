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
import toml

from ..sysroot import SysrootSpecification
from ..user_exception import UserException

from .project_parts import QrcDirectory, QrcFile, QrcPackage


class Project:
    """ The encapsulation of a project. """

    # The minimum supported project version.  At the moment a project will be
    # automatically updated to the current version when saved.
    min_version = 0

    # The current project version.
    version = 0

    @property
    def name(self):
        """ The name property getter. """

        return self._name

    @name.setter
    def name(self, value):
        """ The name property setter. """

        self._name = '' if value == '' else os.path.abspath(value)

    def __init__(self, name=''):
        """ Initialise the project. """

        self.name = name
        self.sysroot_specification = None

        # Initialise the project data.
        self.application_name = ''
        self.application_is_console = False
        self.application_is_bundle = True
        self.application_package = QrcPackage()
        self.application_script = ''
        self.application_entry_point = ''
        self.sys_path = ''
        self.sysroot_toml = ''
        self.sysroots_dir = ''
        self.parts = []
        self.qmake_configuration = ''

    @property
    def absolute_sysroot_toml(self):
        """ Get the absolute pathname of the sysroot specification file. """

        return self.project_path(
                'sysroot.toml' if self.sysroot_toml == '' else self.sysroot_toml)

    @absolute_sysroot_toml.setter
    def absolute_sysroot_toml(self, value):
        """ Set the absolute pathname of the sysroot specification file. """

        value = self.minimal_path(value)

        if value == os.path.join('.', 'sysroot.toml'):
            value = ''

        self.sysroot_toml = value

    @property
    def absolute_sysroots_dir(self):
        """ Get the absolute pathname of the sysroots directory. """

        if self.sysroots_dir == '':
            return os.path.dirname(self.absolute_sysroot_toml)

        return self.project_path(self.sysroots_dir)

    @absolute_sysroots_dir.setter
    def absolute_sysroots_dir(self, value):
        """ Set the absolute pathname of the sysroots directory. """

        if value != '':
            value = os.path.abspath(value)

        if value == os.path.dirname(self.absolute_sysroot_toml):
            value = ''
        else:
            value = self.minimal_path(value)

        self.sysroots_dir = value

    @classmethod
    def load(cls, name):
        """ Return a new project loaded from the given file.  Raise a
        UserException if there was an error.
        """

        # Get the loader for the project.
        if name.endswith('.pdy'):
            from .legacy import load_xml as loader

            # Save the file using the current format.
            save_as = name.replace('.pdy', '.pdt')
        else:
            loader = cls._load_toml
            save_as = name

        # Create the project and load it.
        project = cls(save_as)
        loader(project, name)

        # Load the sysroot specification.
        project.load_sysroot()

        return project

    def load_sysroot(self):
        """ Load the project's sysroot specification file. """

        self.sysroot_specification = SysrootSpecification(
                self.absolute_sysroot_toml)

    def minimal_path(self, path):
        """ Return a relative form of the path if it is in the same directory
        (or a sub-directory) as that containing the project file.  Otherwise
        return an absolute path.
        """

        if path == '':
            return ''

        path = os.path.abspath(path)

        try:
            common_path = os.path.commonpath((path, self._name))
        except ValueError:
            return path

        if common_path != os.path.dirname(self._name):
            return path

        return os.path.relpath(path, common_path)

    def project_path(self, path):
        """ Return an absolute path.  If the original path is relative then
        assume it is relative to the name of the project file.
        """

        if os.path.isabs(path):
            return path

        return os.path.normpath(
                os.path.join(os.path.dirname(self._name), path))

    def save(self):
        """ Save the project.  Raise a UserException if there was an error. """

        self._save_project(self._name)

    def save_as(self, name):
        """ Save the project to the given file and make the file the
        destination of subsequent saves.  Raise a UserException if there was an
        error.
        """

        self._save_project(name)

        # Only do this after the project has been successfully saved.
        self.name = name

    @staticmethod
    def _get_dict(container, name):
        """ Return a container value assuming it is a dict. """

        try:
            return container[name]
        except KeyError:
            return {}

    @staticmethod
    def _get_list(container, name):
        """ Return a container value assuming it is a list. """

        try:
            return container[name]
        except KeyError:
            return []

    @classmethod
    def _load_package(cls, container):
        """ Return a populated QrcPackage instance. """

        package = QrcPackage()

        package.name = container.get('name')
        package.contents = cls._load_mfs_contents(container)
        package.exclusions = cls._get_list(container, 'exclude')

        return package

    @classmethod
    def _load_mfs_contents(cls, container):
        """ Return a list of contents for a memory-filesystem container. """

        contents = []

        for content_element in cls._get_list(container, 'Content'):
            name = content_element.get('name')
            included = content_element.get('included', False)
            isdir = content_element.get('is_directory', False)

            content = QrcDirectory(name, included) if isdir else QrcFile(name, included)

            if isdir:
                content.contents = cls._load_mfs_contents(content_element)

            contents.append(content)

        return contents

    @classmethod
    def _load_toml(cls, project, file_path):
        """ Load a TOML format project file. """

        try:
            with open(file_path) as f:
                root = toml.load(f)
        except Exception as e:
            raise UserException("there was an error reading the project file",
                    str(e))

        # Check the project version number.
        version = root.get('version')
        if version is None:
            raise UserException("missing 'version' attribute")

        if version < cls.min_version:
            raise UserException("the project's format is no longer supported")

        if version > cls.version:
            raise UserException(
                    "the project's format is version {0} but only version {1} "
                    "is supported".format(version, cls.version))

        project.sysroot_toml = root.get('sysroot', '').replace('/', os.sep)
        project.sysroots_dir = root.get('sysroots_dir', '').replace('/', os.sep)
        project.parts = cls._get_list(root, 'parts')

        # The application specific configuration.
        application = cls._get_dict(root, 'Application')

        project.application_entry_point = application.get('entry_point', '')
        project.application_is_console = application.get('is_console', False)
        project.application_is_bundle = application.get('is_bundle', False)
        project.application_name = application.get('name', '')
        project.application_script = application.get('script', '')
        project.qmake_configuration = application.get('qmake_configuration',
                '')
        project.sys_path = application.get('syspath', '')

        # Any application package.
        app_package = application.get('Package')

        if app_package is not None:
            project.application_package = cls._load_package(app_package)
        else:
            project.application_package = QrcPackage()

    def _save_project(self, file_name):
        """ Save the project to the given file.  Raise a UserException if there
        was an error.
        """

        root = {
            'version': self.version,
            'sysroot': self.sysroot_toml.replace(os.sep, '/'),
            'sysroots_dir': self.sysroots_dir.replace(os.sep, '/'),
            'parts': self.parts,
        }

        application = {
            'entry_point': self.application_entry_point,
            'is_console': self.application_is_console,
            'is_bundle': self.application_is_bundle,
            'name': self.application_name,
            'qmake_configuration': self.qmake_configuration,
            'script': self.application_script,
            'syspath': self.sys_path
        }

        if self.application_package.name is not None:
            application['Package'] = self._save_package(
                    self.application_package)

        root['Application'] = application

        try:
            with open(file_name, 'w') as f:
                toml.dump(root, f)
        except Exception as e:
            raise UserException("there was an error writing the project file",
                    str(e))

    @classmethod
    def _save_package(cls, qrc_package):
        """ Return a container containing a QrcPackage. """

        container = {
            'name': qrc_package.name,
            'exclude': qrc_package.exclusions
        }

        cls._save_mfs_contents(container, qrc_package.contents)

        return container

    @classmethod
    def _save_mfs_contents(cls, container, contents):
        """ Save the contents of a memory-filesystem container. """

        subcontainers = []

        for content in contents:
            isdir = isinstance(content, QrcDirectory)

            subcontainer = {
                'name': content.name,
                'included': content.included,
                'is_directory': isdir
            }

            if isdir:
                cls._save_mfs_contents(subcontainer, content.contents)

            subcontainers.append(subcontainer)

        container['Content'] = subcontainers
