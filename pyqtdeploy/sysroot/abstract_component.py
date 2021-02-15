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


from abc import ABC, abstractmethod
import copy
import os
import shutil

from ..parts import CompiledPart, ExtensionModule, Part

from .component_option import ComponentOption


class AbstractComponent(ABC):
    """ The abstract base class for the implementation of a component plugin.
    """

    ###########################################################################
    # The following make up the public API to be used by component plugins.
    ###########################################################################

    # The list of components that, if specified, should be installed before
    # this one.
    preinstalls = []

    # The dict of parts provided by the component.
    provides = {}

    @property
    def android_abi(self):
        """ The Android ABI being used. """

        return self._sysroot.target.android_abi

    @property
    def android_api(self):
        """ The Android API being used. """

        return self._sysroot.target.platform.android_api

    @property
    def android_ndk_root(self):
        """ The path of the root of the Android NDK. """

        return self._sysroot.target.platform.android_ndk_root

    @property
    def android_ndk_sysroot(self):
        """ The path of the Android NDK's sysroot directory. """

        return self._sysroot.target.platform.android_ndk_sysroot

    @property
    def android_ndk_version(self):
        """ The VersionNumber object representing the version number of the
        Android NDK.
        """

        return self._sysroot.target.platform.android_ndk_version

    @property
    def android_sdk_version(self):
        """ The VersionNumber object representing the version number of the
        Android SDK.
        """

        return self._sysroot.target.platform.android_sdk_version

    @property
    def android_toolchain_bin(self):
        """ The path of the Android toolchain's bin directory. """

        return self._sysroot.target.android_toolchain_bin

    @property
    def android_toolchain_cc(self):
        """ The name of the Android toolchain's C compiler. """

        return self._sysroot.target.android_toolchain_cc

    @property
    def android_toolchain_prefix(self):
        """ The name of the Android toolchain's prefix. """

        return self._sysroot.target.android_toolchain_prefix

    @property
    def apple_sdk(self):
        """ The Apple SDK being used. """

        return self._sysroot.apple_sdk

    @property
    def apple_sdk_version(self):
        """ The version number of the Apple SDK. """

        return self._sysroot.apple_sdk_version

    @property
    def building_for_target(self):
        """ This is set if building (ie. compiling and linking) for the target
        architecture.  Otherwise build for the host.  The default is True.
        """

        return self._sysroot.building_for_target

    @building_for_target.setter
    def building_for_target(self, value):
        """ Set to build (ie. compile and link) for the target architecture.
        Otherwise build for the host.
        """

        self._sysroot.building_for_target = value

    def copy_dir(self, src, dst, ignore=None):
        """ Copy a directory and its contents optionally ignoring a sequence of
        patterns.  If the destination directory already exists its contents
        will be first deleted.
        """

        # Make sure the destination does not exist but can be created.
        self.delete_dir(dst)
        self.create_dir(os.path.dirname(dst))

        self.verbose("copying {0} to {1}".format(src, os.path.abspath(dst)))

        if ignore is not None:
            ignore = shutil.ignore_patterns(*ignore)

        try:
            shutil.copytree(src, dst, ignore=ignore)
        except Exception as e:
            self.error("unable to copy directory {0}".format(src),
                    detail=str(e))

    def copy_file(self, src, dst, macros=None):
        """ Copy a file while expanding an optional dict of macros. """

        self.verbose("copying {0} to {1}".format(src, os.path.abspath(dst)))

        if macros is None:
            try:
                shutil.copy(src, dst)
            except Exception as e:
                self.error("unable to copy {0}".format(src), detail=str(e))
        else:
            try:
                with open(src) as f:
                    contents = f.read()
            except Exception as e:
                self.error("unable to open {0} for reading".format(src),
                        detail=str(e))

            for key, value in macros.items():
                contents = contents.replace(key, value)

            try:
                with open(dst, 'w') as f:
                    f.write(contents)
            except Exception as e:
                self.error("unable to create {0} for writing".format(dst),
                        detail=str(e))

    def create_dir(self, name, empty=False):
        """ Ensure a directory exists and optionally delete its contents. """

        self._sysroot.create_dir(name, empty=empty, component=self)

    def create_file(self, name):
        """ Create a text file and return the file object. """

        return self._sysroot.create_file(name, component=self)

    def delete_dir(self, name):
        """ Delete a directory and its contents. """

        self._sysroot.delete_dir(name, component=self)

    def error(self, message, detail=''):
        """ Issue an error message.  This method will not return. """

        self._sysroot.error(message, detail=detail, component=self)

    def find_exe(self, name, required=True):
        """ Return the absolute pathname of an executable located on PATH. """

        return self._sysroot.find_exe(name, required=required, component=self)

    def get_component(self, name, required=True):
        """ Return the component object for the given name or None if the
        component hasn't been specified.  If it has not been specified and it
        is required then raise an exception.
        """

        return self._sysroot.get_component(name, required=required,
                component=self)

    def get_file(self, name):
        """ Return the pathname of a file in one of the directories specified
        by the --source-dir command line option.  None is return if it could
        not be found.
        """

        for source_dir in self._sysroot.source_dirs:
            self.verbose("looking for '{0}' in {1}".format(name, source_dir))

            pathname = os.path.join(source_dir, name)
            if os.path.isfile(pathname):
                self.verbose("found '{0}' in {1}".format(name, source_dir))

                return pathname

        return None

    def get_options(self):
        """ Return a list of ComponentOption objects that define the components
        configurable options.
        """

        return [ComponentOption('version', required=True,
                help="The version number of the component.")]

    def get_python_install_path(self, major, minor):
        """ Return the name of the directory containing the root of a Python
        installation directory.  It must not be called on a non-Windows
        platform.
        """

        from winreg import HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, QueryValue

        reg_version = '{}.{}'.format(major, minor)
        if self.target_arch_name.endswith('-32'):
            reg_version += '-32'

        sub_key_user = 'Software\\Python\\PythonCore\\{}\\InstallPath'.format(
                reg_version)
        sub_key_all_users = 'Software\\Wow6432Node\\Python\\PythonCore\\{}\\InstallPath'.format(
                reg_version)

        queries = (
            (HKEY_CURRENT_USER, sub_key_user),
            (HKEY_LOCAL_MACHINE, sub_key_user),
            (HKEY_LOCAL_MACHINE, sub_key_all_users))

        for key, sub_key in queries:
            try:
                install_path = QueryValue(key, sub_key)
            except OSError:
                pass
            else:
                break
        else:
            self.error(
                    "unable to find an installation of Python v{0}".format(
                            reg_version))

        return install_path

    def get_version_from_file(self, identifier, filename):
        """ Return the stripped line from a file containing an identifier
        (typically a pre-processor macro defining a version number).
        """

        self.verbose(
                "determining installed version from '{0}'".format(filename))

        version_line = None

        if os.path.isfile(filename):
            with open(filename) as f:
                for line in f:
                    if identifier in line:
                        version_line = line.strip()
                        break

        if version_line is None:
            self.error(
                    "unable to find '{0}' in {1}".format(identifier, filename))

        return version_line

    @property
    def host_dir(self):
        """ The directory containing any host installations. """

        return self._sysroot.host_dir

    def host_exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

        return self._sysroot.host_exe(name)

    @property
    def host_make(self):
        """ The name of the host make executable. """

        return self._sysroot.host.platform.make

    @property
    def host_platform_name(self):
        """ The name of the host platform. """

        return self._sysroot.host.platform.name

    @abstractmethod
    def install(self):
        """ Install the component. """

    def open_file(self, name):
        """ Open an existing text file and return the file object. """

        return self._sysroot.open_file(name, component=self)

    @staticmethod
    def parse_version_number(version_nr):
        """ Return the VersionNumber object corresponding to a version number
        as a string, an encoded integer or a tuple.  UserException is raised if
        it couldn't be parsed.

        The version number format, as a string, is M[.m[.p]][suffix] where M is
        the int major version, m is the int minor version, p is the int patch
        version and suffix is a str suffix.
        """

        from ..version_number import VersionNumber

        return VersionNumber.parse_version_number(version_nr)

    def patch_file(self, name, patcher):
        """ Invoke a patcher for each line of a file to be patched.  The
        patcher is passed the line and a file object of the updated version of
        the file.
        """

        # Ignore if the source file doesn't exist.
        if not os.path.isfile(name):
            return

        orig = name + '.orig'
        os.rename(name, orig)

        orig_file = self.open_file(orig)
        patch_file = self.create_file(name)

        for line in orig_file:
            patcher(line, patch_file)

        orig_file.close()
        patch_file.close()

    def progress(self, message):
        """ Issue a progress message. """

        self._sysroot.progress(message, component=self)

    def run(self, *args, capture=False):
        """ Run a command, optionally capturing stdout. """

        return self._sysroot.run(*args, capture=capture)

    def sdk_configure(self, platform_name):
        """ Perform any platform-specific SDK configuration. """

        pass

    def sdk_deconfigure(self, platform_name):
        """ Remove any platform-specific SDK configuration applied by a
        previous call to sdk_configure().
        """

        pass

    @property
    def sysroot_dir(self):
        """ The name of the sysroot directory. """

        return self._sysroot.sysroot_dir

    @property
    def target_arch_name(self):
        """ The name of the target architecture. """

        return self._sysroot.target.name

    @property
    def target_include_dir(self):
        """ The name of the directory containing target header files. """

        return self._sysroot.target_include_dir

    @property
    def target_lib_dir(self):
        """ The name of the directory containing target libraries. """

        return self._sysroot.target_lib_dir

    @property
    def target_platform_name(self):
        """ The name of the target platform. """

        return self._sysroot.target.platform.name

    @property
    def target_src_dir(self):
        """ The name of the directory containing target sources. """

        return self._sysroot.target_src_dir

    def unsupported(self, detail=None):
        """ Issue an error message that the version of the component is
        unsupported.
        """

        message = "v{0} is unsupported".format(self.version)

        if detail is not None:
            message += ' ' + detail

        self.error(message)

    def untested(self):
        """ Issue a warning message that the version of the component is
        untested.
        """

        self.warning("v{0} is untested".format(self.version))

    def verify(self):
        """ Verify the component.  This will be called after the options have
        been parsed and the version number resolved.
        """

    def verbose(self, message):
        """ Issue a verbose progress message. """

        self._sysroot.verbose(message, component=self)

    @property
    def verbose_enabled(self):
        """ True if verbose messages are being displayed. """

        return self._sysroot.verbose_enabled

    def warning(self, message):
        """ Issue a warning message. """

        self._sysroot.warning(message, component=self)

    ###########################################################################
    # The following are not part of the public API used by component plugins.
    ###########################################################################

    # The installation status.
    _IS_NOT_INSTALLED, _IS_IN_PROGRESS, _IS_INSTALLED = range(3)

    def __init__(self, name, configuration, sysroot):
        """ Initialise the component. """

        self._install_status = self._IS_NOT_INSTALLED

        self.name = name
        self._sysroot = sysroot
        self._parts = None

        # Configure the component.
        for option in self.get_options():
            value = configuration.get(option.name)

            if value is None:
                if option.required:
                    self.error(
                            "'{0}' has not been specified".format(option.name))

                # Create a default value.
                if option.default is None:
                    value = option.type()
                else:
                    value = option.default
            elif not isinstance(value, option.type):
                self.error(
                        "value of '{0}' has an unexpected type".format(
                                option.name))
            elif option.values:
                values = value if isinstance(value, list) else [value]

                for v in values:
                    if v not in option.values:
                        self.error(
                                "'{0}' must have one of these values: {1} and "
                                        "not '{2}'".format(option.name,
                                                ', '.join(option.values), v))

            setattr(self, option.name, value)

            try:
                del configuration[option.name]
            except KeyError:
                pass

        unused = configuration.keys()
        if unused:
            self.error("unknown option(s): {0}".format(', '.join(unused)))

        # Allow the version number to be defined by an environment variable.
        self.version = self.parse_version_number(
                os.path.expandvars(self.version))

    @staticmethod
    def add_to_path(name):
        """ Add the name of a directory to the start of PATH if it isn't
        already present.  The original PATH is returned.
        """

        original_path = os.environ['PATH']
        path = original_path.split(os.pathsep)

        if name not in path:
            path.insert(0, name)
            os.environ['PATH'] = os.pathsep.join(path)

        return original_path

    def ensure_installed(self, build_dir, all_components, manifest):
        """ Ensure the component is installed. """

        # Handle the trivial case where the manifest show that the component is
        # already installed.
        if self.name in manifest:
            self._install_status = self._IS_INSTALLED
            return

        if self._install_status == self._IS_NOT_INSTALLED:
            self._install_status = self._IS_IN_PROGRESS

            # If all components are being installed then make sure they are
            # done in the right order.
            if all_components:
                for preinstall in self.preinstalls:
                    component = self.get_component(preinstall, required=False)
                    if component is not None:
                        component.ensure_installed(build_dir, all_components,
                                manifest)

            self.progress("installing component")
            os.chdir(build_dir)
            self.install()

            self._install_status = self._IS_INSTALLED
            manifest[self.name] = self.version

        elif self._install_status == self._IS_IN_PROGRESS:
            self.error("the component is part of a circular dependency")

    def get_target_src_path(self, name):
        """ Return the absolute pathname of a source file provided by the
        component.
        """

        # This default implementation assumes the name is relative to the
        # sysroot's target source directory.
        return os.path.join(self.target_src_dir, name)

    @property
    def parts(self):
        """ The mapping of parts, keyed by the scoped name of the part,
        provided by this version of the component.
        """

        if self._parts is None:
            self._parts = {}

            openssl = self.get_component('OpenSSL', required=False)

            # Get the provided version and target-specific parts.
            provides = {}
            for unscoped_name, versions in self.provides.items():
                part = self._normalised_part(unscoped_name, versions)
                if part is not None:
                    provides[part.name] = part

            # For each provided part remember the part or None if any of its
            # dependencies are unavailable.
            for name, part in provides.items():
                self._add_part(name, part, openssl, provides)

            # Remove all unavailable parts.
            self._parts = {n: p for n, p in self._parts.items()
                    if p is not None}

        return self._parts

    @property
    def target_modules_dir(self):
        """ The absolute pathname of the directory containing any Python
        modules provided by the component.
        """

        # This default implementation returns the target Python installation's
        # site-packages directory.
        return self.get_component('Python').target_sitepackages_dir

    def _add_part(self, name, part, openssl, provides):
        """ Add a part if all its dependencies are available. """

        # Handle the trivial case.
        if name in self._parts:
            return

        # Save the part now (to handle recursion) assuming all its dependencies
        # will be met.  Note that this doesn't handle complicated mutual
        # dependencies correctly because we could end up with parts that were
        # available based on this assumption but the assumption was later found
        # to be incorrect.  However there are currently no examples of this in
        # the standard library and other packages are unlikely to be that
        # complicated.
        self._parts[name] = part

        # Check (and possibly update) the dependencies.
        updated_deps = []

        for dep_name in part.deps:
            component_name, part_name = Part.get_name_parts(dep_name)

            required = True

            if part_name.startswith('?'):
                # The dependency is optional so its availability has no impact.
                required = False

                dep_name = Part.get_name(component_name, part_name[1:])
            elif part_name.startswith('!'):
                # This is only provided if OpenSSL is not available.
                if openssl is not None:
                    continue

                dep_name = Part.get_name(component_name, part_name[1:])

            # See if it is an intra-component dependency.
            if self.name == component_name:
                # See if the dependency is theoretically provided (although it
                # might not actually be available).
                dep_part = provides.get(dep_name)
                if dep_part is None:
                    if required:
                        part = None
                        break
                else:
                    self._add_part(dep_name, dep_part, openssl, provides)

                    # See if the dependency was actually available.
                    if self._parts[dep_name] is None:
                        if required:
                            part = None
                            break
                    else:
                        updated_deps.append(dep_name)
            else:
                component = self.get_component(component_name, required=False)

                if component is None or dep_name not in component.parts:
                    if required:
                        part = None
                else:
                    updated_deps.append(dep_name)

        if part is not None:
            part.deps = updated_deps

        # Update the part's entry now we know its availability.
        self._parts[name] = part

    def _normalised_deps(self, deps):
        """ Ensure a sequence of dependent parts is scoped by the providing
        component name and eliminate any dependencies not for the current
        target.
        """

        scoped_deps = []

        for dep in deps:
            if Part.is_scoped_name(dep):
                component_name, dep = Part.get_name_parts(dep)
            else:
                component_name = self.name

            # Discard anything not for the current target.
            dep = self._targeted_value(dep)
            if dep is not None:
                scoped_deps.append(Part.get_name(component_name, dep))

        return scoped_deps

    def _normalised_part(self, unscoped_name, versions):
        """ Return a normalised part from a sequence of version-specific parts.
        All target-specific values are resolved.
        """

        if not isinstance(versions, tuple):
            versions = (versions, )

        # Go through each version of the part.
        for part in versions:
            if part.applies_to(self.version):
                # Discard parts for other targets.  Note that we can't check
                # the Android API level because we don't yet know which level
                # is being targeted.
                if part.target != '' and not self._sysroot.target.is_targeted(part.target):
                    part = None
                    break

                # Don't modify the original part.
                part = copy.deepcopy(part)

                # Save the scoped name of the part.
                part.name = Part.get_name(self.name, unscoped_name)

                # Normalise the dependencies.
                part.deps = self._normalised_deps(part.deps)
                part.hidden_deps = self._normalised_deps(part.hidden_deps)

                # Resolve all target-specific values.
                if isinstance(part, CompiledPart):
                    part.defines = self._normalised_values(part.defines)
                    part.includepath = self._normalised_values(
                            part.includepath)
                    part.libs = self._normalised_values(part.libs)

                if isinstance(part, ExtensionModule):
                    part.source = self._normalised_values(part.source)

                break
        else:
            part = None

        return part

    def _normalised_values(self, values):
        """ Return a list of values that have target-specific elements
        resolved.
        """

        resolved_values = []

        if values is not None:
            for value in values:
                value = self._targeted_value(value)
                if value is not None:
                    resolved_values.append(value)

        return resolved_values if resolved_values else None

    def _targeted_value(self, value):
        """ Return a value if appropriate for the current target or None if
        not.
        """

        if '#' in value:
            target, value = value.split('#', maxsplit=1)

            if not self._sysroot.target.is_targeted(target):
                return None

        return value
