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


from .version_number import VersionNumber


class Part:
    """ Encapsulate the meta-data for a part. """

    def __init__(self, min_version=None, version=None, max_version=None,
            target='', min_android_api=None, internal=False, deps=(),
            hidden_deps=(), core=False):
        """ Initialise the part. """

        self._min_version = min_version
        self._max_version = max_version
        self._version = version

        # The scoped name of the part.
        self.name = None

        # The target platform(s) of the part.
        self.target = target

        # The minimum Android API required.
        self.min_android_api = min_android_api

        # Set if the part is internal, ie. not part of a public API exposed to
        # an application being deployed.
        self.internal = internal

        # The sequence of the names of parts that this one is dependent on.  A
        # name is of the form '[component:]name'.
        self.deps = (deps, ) if isinstance(deps, str) else deps

        # The sequence of additional parts that this one is dependent on.
        # These dependencies are hidden from the user and (most importantly)
        # further sub-dependencies are ignored.  The use case is the warnings
        # module in Python v3 which is a dependency of the core (for a simple
        # function that should never be called) but drags in a lot of other
        # stuff.
        self.hidden_deps = (hidden_deps, ) if isinstance(hidden_deps, str) else hidden_deps

        # Set if the part is already compiled in to the interpreter library
        # (if it is an extension module) or if it is required (if it is a
        # Python module).
        self.core = core

    def applies_to(self, version):
        """ Returns True if the given version applies to this part. """

        if self._version is not None:
            return version == self._version

        if self._min_version is not None:
            if version < self._min_version:
                return False

        if self._max_version is not None:
            if version > self._max_version:
                return False

        return True

    @property
    def component_name(self):
        """ The name of the component that provides the part. """

        return self.name.split(':', maxsplit=1)[0]

    @classmethod
    def get_component_name(cls, name):
        """ Return the component name from a scoped part name. """

        return cls.get_name_parts(name)[0]

    @staticmethod
    def get_name(component_name, unscoped_name):
        """ Return the scoped part name from the component name and the
        unscoped part name.
        """

        return component_name + ':' + unscoped_name

    @staticmethod
    def get_name_parts(name):
        """ Return a 2-tuple of the component name and unscoped part name from
        a scoped part name.
        """

        return name.split(':', maxsplit=1)

    @classmethod
    def get_unscoped_name(cls, name):
        """ Return the unscoped part name from a scoped part name. """

        return cls.get_name_parts(name)[1]

    @staticmethod
    def is_scoped_name(name):
        """ Return True if a name is a scoped part name. """

        return ':' in name

    @property
    def unscoped_name(self):
        """ The unscoped name of the part. """

        return self.get_unscoped_name(self.name)


class CompiledPart(Part):
    """ Encapsulate the meta-data for a part that is compiled. """

    def __init__(self, min_version=None, version=None, max_version=None,
            target='', min_android_api=None, internal=False, deps=(),
            hidden_deps=(), core=False, defines=None, libs=None,
            includepath=None):
        """ Initialise the part. """

        super().__init__(min_version=min_version, version=version,
                max_version=max_version, target=target,
                min_android_api=min_android_api, internal=internal, deps=deps,
                hidden_deps=hidden_deps, core=core)

        # The sequence of (possibly scoped) DEFINES to add to the .pro file.
        self.defines = (defines, ) if isinstance(defines, str) else defines

        # The sequence of (possibly scoped) LIBS to add to the .pro file.
        self.libs = (libs, ) if isinstance(libs, str) else libs

        # The sequence of (possibly scoped) directories directory to add to
        # INCLUDEPATH.
        self.includepath = (includepath, ) if isinstance(includepath, str) else includepath


class ComponentLibrary(CompiledPart):
    """ Encapsulate the meta-data for a component library. """

    def __init__(self, min_version=None, version=None, max_version=None,
            target='', defines=None, libs=None, includepath=None,
            bundle_shared_libs=False):
        """ Initialise the part. """

        super().__init__(min_version=min_version, version=version,
                max_version=max_version, target=target, internal=True,
                defines=defines, libs=libs, includepath=includepath)

        # True if the libs are shared and need to be bundled with the
        # application.  Currently this is only applicable to Android targets.
        self.bundle_shared_libs = bundle_shared_libs


class DataFile(Part):
    """ Encapsulate the meta-data for a part that is a data file. """

    def __init__(self, name, min_version=None, version=None, max_version=None,
            target=''):
        """ Initialise the part. """

        super().__init__(min_version=min_version, version=version,
                max_version=max_version, target=target, internal=True)

        # The name of the file.
        self.name = name


class ExtensionModule(CompiledPart):
    """ Encapsulate the meta-data for an extension module. """

    def __init__(self, min_version=None, version=None, max_version=None,
            target='', min_android_api=None, internal=False, deps=(),
            hidden_deps=(), core=False, defines=None, libs=None,
            includepath=None, source=None, qmake_config=None,
            qmake_cpp11=False, qmake_qt=None, pyd=None, dlls=None):
        """ Initialise the part. """

        super().__init__(min_version=min_version, version=version,
                max_version=max_version, target=target,
                min_android_api=min_android_api, internal=internal, deps=deps,
                hidden_deps=hidden_deps, core=core, defines=defines, libs=libs,
                includepath=includepath)

        # The sequence of (possibly scoped) source files.
        self.source = (source, ) if isinstance(source, str) else source

        # The sequence of strings to add the qmake's CONFIG variable.
        self.qmake_config = (qmake_config, ) if isinstance(qmake_config, str) else qmake_config

        # Set if C++11 compiler support is needed.
        self.qmake_cpp11 = qmake_cpp11

        # The sequence of strings to add the qmake's QT variable.
        self.qmake_qt = (qmake_qt, ) if isinstance(qmake_qt, str) else qmake_qt

        # The name of the extension module if it is implemented as a .pyd file
        # included in the Windows installer from python.org.
        self.pyd = pyd

        # The sequence of additional DLLs needed by the extension module and
        # included in the Windows installer from python.org.
        self.dlls = (dlls, ) if isinstance(dlls, str) else dlls


class PythonModule(Part):
    """ Encapsulate the meta-data for a single Python module. """

    def __init__(self, min_version=None, version=None, max_version=None,
            target='', min_android_api=None, internal=False, deps=(),
            hidden_deps=(), core=False, builtin=False):
        """ Initialise the part. """

        super().__init__(min_version=min_version, version=version,
                max_version=max_version, target=target,
                min_android_api=min_android_api, internal=internal, deps=deps,
                hidden_deps=hidden_deps, core=core)

        # Set if the part is a core Python module that is already embedded as a
        # builtin.
        self.builtin = builtin


class PythonPackage(Part):
    """ Encapsulate the meta-data for a Python package. """

    def __init__(self, min_version=None, version=None, max_version=None,
            target='', min_android_api=None, internal=False, deps=(),
            hidden_deps=(), core=False, exclusions=()):
        """ Initialise the part. """

        super().__init__(min_version=min_version, version=version,
                max_version=max_version, target=target,
                min_android_api=min_android_api, internal=internal, deps=deps,
                hidden_deps=hidden_deps, core=core)

        # The sequence of file or directory names relative to the package to be
        # excluded from the package.
        self.exclusions = (exclusions, ) if isinstance(exclusions, str) else exclusions
