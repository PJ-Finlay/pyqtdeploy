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
import shutil
import sys

from ..file_utilities import (create_file as fu_create_file,
        open_file as fu_open_file)
from ..platforms import Platform
from ..user_exception import UserException
from ..version_number import VersionNumber


class Sysroot:
    """ Encapsulate a target-specific system root directory. """

    def __init__(self, specification, host, target, sysroots_dir,
            message_handler=None, python=None, qmake=None):
        """ Initialise the object. """

        self._specification = specification
        self.host = host
        self.target = target
        self._message_handler = message_handler

        self.sysroot_dir = os.path.join(sysroots_dir,
                'sysroot-' + self.target.name)

        self._building_for_target = True

        self.components = specification.create_components_for_target(target,
                self)

        # Set any externally specified qmake.
        if python is not None:
            python_component = self.get_component('Python', required=False)
            if python_component is not None:
                python_component.host_python = python

        if qmake is not None:
            qt_component = self.get_component('Qt', required=False)
            if qt_component is not None:
                qt_component.host_qmake = qmake

    @property
    def apple_sdk(self):
        """ The Apple SDK being used. """

        arch = self.target if self._building_for_target else self.host

        return arch.platform.apple_sdk

    @property
    def apple_sdk_version(self):
        """ The version of the Apple SDK being used. """

        arch = self.target if self._building_for_target else self.host

        return arch.platform.apple_sdk_version

    @property
    def building_for_target(self):
        """ This is set if building (ie. compiling and linking) for the target
        architecture.  Otherwise build for the host.  The default is True.
        """

        return self._building_for_target

    @building_for_target.setter
    def building_for_target(self, value):
        """ Set to build (ie. compile and link) for the target architecture.
        Otherwise build for the host.
        """

        if value:
            for component in self.components:
                component.sdk_deconfigure(self.host.platform.name)

            self.host.deconfigure()

            self.target.configure()

            for component in self.components:
                component.sdk_configure(self.target.platform.name)
        else:
            for component in self.components:
                component.sdk_deconfigure(self.target.platform.name)

            self.target.deconfigure()

            self.host.configure()

            for component in self.components:
                component.sdk_configure(self.host.platform.name)

        self._building_for_target = value

    def create_dir(self, name, empty=False, component=None):
        """ Ensure a directory exists and optionally delete its contents. """

        if empty:
            self.delete_dir(name)

        if os.path.exists(name):
            if not os.path.isdir(name):
                self.error("{0} exists but is not a directory".format(name),
                        component=component)
        else:
            self.verbose("creating {0}".format(name), component=component)

            try:
                os.makedirs(name, exist_ok=True)
            except Exception as e:
                self.error("unable to create directory {0}".format(name),
                        detail=str(e), component=component)

    def create_file(self, name, component=None):
        """ Create a text file and return the file object. """

        try:
            return fu_create_file(name)
        except UserException as e:
            self.error(str(e), component=component)

    def delete_dir(self, name, component=None):
        """ Delete a directory and its contents. """

        if os.path.exists(name):
            if not os.path.isdir(name):
                self.error("{0} exists but is not a directory".format(name),
                        component=component)

            self.verbose("deleting {0}".format(name), component=component)

            # 32 bit applications on Windows have a 256 character limit on file
            # names which we can hit.  The Microsoft work around is to prepend
            # a magic string.
            name_hack = '\\\\?\\' + name if sys.platform == 'win32' else name

            try:
                shutil.rmtree(name_hack)
            except Exception as e:
                self.error("unable to remove directory {0}".format(name),
                        detail=str(e), component=component)

    @classmethod
    def error(cls, message, detail='', exception=None, component=None):
        """ Raise an exception that will report an error is a user friendly
        manner.
        """

        raise UserException(cls._format_message(message, component),
                detail=detail) from exception

    def find_exe(self, name, required=True, component=None):
        """ Return the absolute pathname of an executable located on PATH. """

        host_exe = self.host_exe(name)

        for d in os.get_exec_path():
            exe_path = os.path.join(d, host_exe)

            if os.access(exe_path, os.X_OK):
                return exe_path

        if required:
            self.error("'{0}' could not be found on PATH".format(name),
                    component=component)

        return None

    def get_component(self, name, required=True, component=None):
        """ Return the component object for the given name or None if the
        component hasn't been specified.  If it has not been specified and it
        is required then raise an exception.
        """

        for comp in self.components:
            if comp.name == name:
                return comp

        if required:
            self.error(
                    "'{0}' must be specified as a component of the "
                            "sysroot".format(name),
                    component=component)

        return None

    @property
    def host_dir(self):
        """ The directory containing the host installations. """

        return os.path.join(self.sysroot_dir, 'host')

    def host_exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

        return self.host.platform.exe(name)

    def install_components(self, component_names, source_dirs, no_clean,
            force):
        """ Install a sequence of components.  If no names are given then
        use the Manifest file to determine what needs to be installed.  Raise a
        UserException if there is an error.
        """

        # Verify the configuration.
        self.verify()

        # Get the name of the components to install.
        if component_names:
            components = self._components_from_names(component_names)
            all_components = False
        else:
            components = self.components
            all_components = True

        # Unless a complete re-install is being forced, compare what needs to
        # be installed with what is currently installed.
        manifest = {}

        if not force:
            try:
                with open(self._manifest_file) as mf:
                    for line in mf:
                        name, version_str = line.split()
                        manifest[name] = VersionNumber.parse_version_number(
                                version_str)
            except FileNotFoundError:
                pass
            except Exception as e:
                raise UserException("invalid 'Manifest' file", detail=str(e))

            # Force a complete re-install if the version of any component
            # currently installed is not the same version as that required.
            # Note that we don't do the same if the configuration of a
            # component has changed, even though this may have similar
            # consequences.
            for component in components:
                installed = manifest.get(component.name)
                if installed is not None and installed != component.version:
                    force = True
                    manifest = {}
                    break

        # Normalise the list of source directories to search.
        if source_dirs:
            self.source_dirs = [os.path.abspath(s) for s in source_dirs]
        else:
            self.source_dirs = [
                    os.path.dirname(self._specification.specification_file)]

        self.target.configure()

        self.create_dir(self.sysroot_dir, empty=force)
        self._write_manifest(manifest)
        os.makedirs(self.host_dir, exist_ok=True)
        os.makedirs(self.target_include_dir, exist_ok=True)
        os.makedirs(self.target_lib_dir, exist_ok=True)
        os.makedirs(self.target_src_dir, exist_ok=True)

        # Create a new build directory.
        build_dir = os.path.join(self.sysroot_dir, 'build')
        self.create_dir(build_dir, empty=True)
        cwd = os.getcwd()

        # Install the components.
        self.building_for_target = True

        for component in components:
            component.ensure_installed(build_dir, all_components, manifest)
            self._write_manifest(manifest)

        # Remove the build directory if requested.
        os.chdir(cwd)

        if not no_clean:
            # This can fail on Windows (complaining about non-empty
            # directories).  Therefore we just warn that we couldn't do it.
            try:
                self.delete_dir(build_dir)
            except UserException as e:
                self.warning(e.text)

    def open_file(self, name, component=None):
        """ Open an existing text file and return the file object. """

        try:
            return fu_open_file(name)
        except UserException as e:
            self.error(str(e), component=component)

    def progress(self, message, component=None):
        """ Issue a progress message. """

        assert self._message_handler is not None
        self._message_handler.progress_message(
                self._format_message(message, component))

    def run(self, *args, capture=False):
        """ Run a command, optionally capturing stdout. """

        assert self._message_handler is not None
        return Platform.run(*args, message_handler=self._message_handler,
                capture=capture)

    def show_options(self, component_names):
        """ Show the options for a sequence of components.  If no names are
        given then show the options of all components.  Raise a UserException
        if there is an error.
        """

        if component_names:
            components = self._components_from_names(component_names)
        else:
            components = self.components

        assert self._message_handler is not None
        self._specification.show_options(components, self._message_handler)

    @property
    def target_include_dir(self):
        """ The name of the directory containing target header files. """

        return os.path.join(self.sysroot_dir, 'include')

    @property
    def target_lib_dir(self):
        """ The name of the directory containing target libraries. """

        return os.path.join(self.sysroot_dir, 'lib')

    @property
    def target_src_dir(self):
        """ The name of the directory containing target sources. """

        return os.path.join(self.sysroot_dir, 'src')

    def verify(self):
        """ Verify the configuration.  Raise a UserException if there is an
        error.
        """

        assert self._message_handler is not None

        # Verify the host and target.
        self.progress(
                "verifying host architecture '{0}'".format(self.host.name))
        self.host.verify_as_host(self.target, self._message_handler)

        self.progress(
                "verifying target architecture '{0}'".format(self.target.name))
        self.target.verify_as_target(self._message_handler)

        # Verify the components.
        for component in self.components:
            self.progress(
                    "verifying {0} v{1}".format(component.name,
                            component.version))

            component.verify()

    def verbose(self, message, component=None):
        """ Issue a verbose progress message. """

        assert self._message_handler is not None
        self._message_handler.verbose_message(
                self._format_message(message, component))

    @property
    def verbose_enabled(self):
        """ True if verbose messages are being displayed. """

        assert self._message_handler is not None
        return self._message_handler.verbose

    def warning(self, message, component=None):
        """ Issue a warning message. """

        assert self._message_handler is not None
        self._message_handler.warning(self._format_message(message, component))

    def _components_from_names(self, component_names):
        """ Return a sequence of components from a sequence of names. """

        components = []

        for name in component_names:
            for component in self.components:
                if component.name == name:
                    components.append(component)
                    break
            else:
                self.error("unkown component '{0}'".format(name))

        return components

    @staticmethod
    def _format_message(message, component):
        """ Return a formatted message. """

        if component is None:
            message = '{}{}.'.format(message[0].upper(), message[1:])
        else:
            message = "{0}: {1}.".format(component.name, message)

        return message

    @property
    def _manifest_file(self):
        """ The full pathname of the Manifest file. """

        return os.path.join(self.sysroot_dir, 'Manifest')

    def _write_manifest(self, manifest):
        """ Write the manifest file. """

        with self.create_file(self._manifest_file) as mf:
            for name in sorted(manifest.keys()):
                mf.write('{} {}\n'.format(name, manifest[name]))
