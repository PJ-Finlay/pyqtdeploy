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

from ... import (AbstractPyQtComponent, ComponentOption, ExtensionModule,
        PythonModule, PythonPackage)


# All the parts that can be provided by the component.
_ALL_PARTS = {
    'PyQt5': PythonModule(deps='Python:pkgutil'),
    'PyQt5.QAxContainer':
        ExtensionModule(target='win', deps='PyQt5.QtWidgets',
                libs='-lQAxContainer', qmake_qt='axcontainer'),
    'PyQt5.Qt': ExtensionModule(deps='PyQt5', libs='-lQt'),
    'PyQt5.QtAndroidExtras':
        ExtensionModule(target='android', deps='PyQt5.QtCore',
                libs='-lQtAndroidExtras', qmake_qt='androidextras'),
    'PyQt5.QtBluetooth':
        ExtensionModule(deps='PyQt5.QtCore', libs='-lQtBluetooth',
                qmake_qt='bluetooth'),
    'PyQt5.QtCore':
        ExtensionModule(deps=('SIP:PyQt5.sip', 'PyQt5'), libs='-lQtCore'),
    'PyQt5.QtDBus':
        ExtensionModule(deps='PyQt5.QtCore', libs='-lQtDBus', qmake_qt='dbus'),
    'PyQt5.QtGui': ExtensionModule(deps='PyQt5.QtCore', libs='-lQtGui'),
    'PyQt5.QtHelp':
        ExtensionModule(deps='PyQt5.QtWidgets', libs='-lQtHelp',
                qmake_qt='help'),
    'PyQt5.QtLocation':
        ExtensionModule(deps='PyQt5.QtPositioning', libs='-lQtLocation',
                qmake_qt='location'),
    'PyQt5.QtMacExtras':
        ExtensionModule(target='ios|macos', deps='PyQt5.QtGui',
                libs='-lQtMacExtras', qmake_qt='macextras'),
    'PyQt5.QtMultimedia':
        ExtensionModule(deps=('PyQt5.QtGui', 'PyQt5.QtNetwork'),
                libs='-lQtMultimedia', qmake_qt='multimedia'),
    'PyQt5.QtMultimediaWidgets':
        ExtensionModule(deps=('PyQt5.QtMultimedia', 'PyQt5.QtWidgets'),
                libs='-lQtMultimediaWidgets', qmake_qt='multimediawidgets'),
    'PyQt5.QtNetwork':
        ExtensionModule(deps='PyQt5.QtCore', libs='-lQtNetwork',
                qmake_qt='network'),
    'PyQt5.QtNetworkAuth':
        ExtensionModule(deps='PyQt5.QtNetwork', libs='-lQtNetworkAuth',
                qmake_qt=('network', 'networkauth')),
    'PyQt5.QtNfc':
        ExtensionModule(deps='PyQt5.QtCore', libs='-lQtNfc', qmake_qt='nfc'),
    'PyQt5.QtOpenGL':
        ExtensionModule(deps='PyQt5.QtWidgets', libs='-lQtOpenGL',
                qmake_qt='opengl'),
    'PyQt5.QtPositioning':
        ExtensionModule(deps='PyQt5.QtCore', libs='-lQtPositioning',
                qmake_qt='positioning'),
    'PyQt5.QtPrintSupport':
        ExtensionModule(target='!ios', deps='PyQt5.QtWidgets',
                libs='-lQtPrintSupport', qmake_qt='printsupport'),
    'PyQt5.QtQml':
        ExtensionModule(deps='PyQt5.QtNetwork', libs='-lQtQml',
                qmake_qt='qml'),
    'PyQt5.QtQuick':
        ExtensionModule(deps=('PyQt5.QtGui', 'PyQt5.QtQml'), libs='-lQtQuick',
                qmake_qt='quick'),
    'PyQt5.QtQuick3D':
        ExtensionModule(min_version=(5, 15),
                deps=('PyQt5.QtGui', 'PyQt5.QtQml'), libs='-lQtQuick3D',
                qmake_qt='quick3d'),
    'PyQt5.QtQuickWidgets':
        ExtensionModule(deps=('PyQt5.QtQuick', 'PyQt5.QtWidgets'),
                libs='-lQtQuickWidgets', qmake_qt='quickwidgets'),
    'PyQt5.QtRemoteObjects':
        ExtensionModule(deps='PyQt5.QtCore', libs='-lQtRemoteObjects',
                qmake_qt='remoteobjects'),
    'PyQt5.QtSensors':
        ExtensionModule(deps='PyQt5.QtCore', libs='-lQtSensors',
                qmake_qt='sensors'),
    'PyQt5.QtSerialPort':
        ExtensionModule(deps='PyQt5.QtCore', libs='-lQtSerialPort',
                qmake_qt='serialport'),
    'PyQt5.QtSql':
        ExtensionModule(deps='PyQt5.QtWidgets', libs='-lQtSql',
                qmake_qt='sql'),
    'PyQt5.QtSvg':
        ExtensionModule(deps='PyQt5.QtWidgets', libs='-lQtSvg',
                qmake_qt='svg'),
    'PyQt5.QtTest':
        ExtensionModule(deps='PyQt5.QtWidgets', libs='-lQtTest',
                qmake_qt='testlib'),
    'PyQt5.QtTextToSpeech':
        ExtensionModule(min_version=(5, 15, 1), deps='PyQt5.QtCore',
                libs='-lQtTextToSpeech', qmake_qt='texttospeech'),
    'PyQt5.QtWebChannel':
        ExtensionModule(deps='PyQt5.QtCore', libs='-lQtWebChannel',
                qmake_qt='webchannel'),
    'PyQt5.QtWebSockets':
        ExtensionModule(deps='PyQt5.QtNetwork', libs='-lQtWebSockets',
                qmake_qt='websockets'),
    'PyQt5.QtWidgets':
        ExtensionModule(deps='PyQt5.QtGui', libs='-lQtWidgets',
                qmake_qt='widgets'),
    'PyQt5.QtWinExtras':
        ExtensionModule(target='win', deps='PyQt5.QtWidgets',
                libs='-lQtWinExtras', qmake_qt='winextras'),
    'PyQt5.QtX11Extras':
        ExtensionModule(target='linux', deps='PyQt5.QtCore',
                libs='-lQtX11Extras', qmake_qt='x11extras'),
    'PyQt5.QtXml':
        ExtensionModule(deps='PyQt5.QtCore', libs='-lQtXml', qmake_qt='xml'),
    'PyQt5.QtXmlPatterns':
        ExtensionModule(deps='PyQt5.QtNetwork', libs='-lQtXmlPatterns',
                qmake_qt='xmlpatterns'),
    'PyQt5._QOpenGLFunctions_2_0':
        ExtensionModule(deps='PyQt5.QtGui', libs='-l_QOpenGLFunctions_2_0'),
    'PyQt5._QOpenGLFunctions_2_1':
        ExtensionModule(deps='PyQt5.QtGui', libs='-l_QOpenGLFunctions_2_1'),
    'PyQt5._QOpenGLFunctions_4_1_Core':
        ExtensionModule(deps='PyQt5.QtGui',
                libs='-l_QOpenGLFunctions_4_1_Core'),
    'PyQt5._QOpenGLFunctions_ES2':
        ExtensionModule(deps='PyQt5.QtGui', libs='-l_QOpenGLFunctions_ES2'),
    'PyQt5.uic':
        PythonPackage(
                deps=('Python:io', 'Python:logging', 'Python:os', 'Python:re',
                        'Python:traceback', 'Python:xml.etree.ElementTree'),
                exclusions=('port_v2', 'pyuic.py')),
}


class PyQtComponent(AbstractPyQtComponent):
    """ The PyQt component. """

    # The component must be installed from source.
    must_install_from_source = True

    # The list of components that, if specified, should be installed before
    # this one.
    preinstalls = ['Python', 'Qt', 'SIP']

    def get_archive_name(self):
        """ Return the filename of the source archive. """

        if self._license_file is not None:
            return 'PyQt5_commercial-{}.tar.gz'.format(self._version_str)

        if self.version <= (5, 13, 1):
            return 'PyQt5_gpl-{}.tar.gz'.format(self._version_str)

        return 'PyQt5-{}.tar.gz'.format(self._version_str)

    def get_archive_urls(self):
        """ Return the list of URLs where the source archive might be
        downloaded from.
        """

        if self._license_file is not None:
            return super().get_archive_urls()

        if self.version <= (5, 14):
            return ['https://www.riverbankcomputing.com/static/Downloads/PyQt5/{}/'.format(self._version_str)]

        return self.get_pypi_urls('PyQt5')

    def get_options(self):
        """ Return a list of ComponentOption objects that define the components
        configurable options.
        """

        options = super().get_options()

        options.append(
                ComponentOption('disabled_features', type=list,
                        help="The features that are disabled."))

        valid_modules = sorted(
                [name[len('PyQt5.'):]
                        for name in _ALL_PARTS
                                if name not in ('PyQt5', 'PyQt5.uic')])

        options.append(
                ComponentOption('installed_modules', type=list, required=True,
                        values=valid_modules,
                        help="The extension modules to be installed."))

        return options

    def install(self):
        """ Install for the target. """

        # See if there is a license file.
        self._license_file = self.get_file('pyqt-commercial.sip')

        # Unpack the source.
        self.unpack_archive(self.get_archive())

        # Copy any license file.
        if self._license_file is not None:
            self.copy_file(self._license_file, 'sip')

        if self.using_sip_v4:
            self._install_using_sip_v4()
        else:
            # Install using SIP v5 or later.
            project_config = {
                'confirm-license': True,
                'designer-plugin': False,
                'qml-plugin': False,
                'dbus-python': False,
                'tools': False,
            }

            bindings_config = {
                'disabled-features': self.disabled_features,
            }

            self.install_pyqt_component(self, project=project_config,
                    bindings=bindings_config, enable=self.installed_modules)

    def install_pyqt_component(self, component, project=None, bindings=None,
            enable=None):
        """ Install a PyQt-based component using SIP v5 or later. """

        # Load the component's pyproject.toml file.
        try:
            pyproject = toml.load('pyproject.toml')
        except FileNotFoundError:
            component.error("Unable to find 'pyproject.toml'")
        except Exception as e:
            component.error("There was an error loading 'pyproject.toml'",
                    detail=str(e))

        # Get the relevent sections.
        project_section = self._get_section('tool.sip.project', pyproject)
        bindings_section = self._get_section('tool.sip.bindings', pyproject)

        # Check the name of the sip module and the ABI version.  Component
        # versions earlier that v5.15.1 didn't set these reliably so provide
        # appropriate default values.
        sip = self.get_component('SIP')

        sip_module = project_section.get('sip-module', 'PyQt5.sip')

        if sip.module_name != sip_module:
            component.error(
                    "sip module '{0}' is required but '{1}' is provided".format(
                            sip_module, sip.module_name))

        abi_version = project_section.get('abi-version', '12.8')
        abi_version = self.parse_version_number(abi_version)

        if abi_version.major != sip.version.major or abi_version > sip.version:
            component.error(
                    "sip module ABI v'{0}' is required but v'{1}' is provided".format(
                            abi_version, sip.version))

        # Re-configure the build.
        python = self.get_component('Python')

        project_section['py-platform'] = self.pyqt_platform
        project_section['py-major-version'] = python.version.major
        project_section['py-minor-version'] = python.version.minor
        project_section['py-include-dir'] = python.target_py_include_dir
        project_section['py-pylib-dir'] = component.target_lib_dir
        project_section['py-pylib-lib'] = python.target_py_lib
        project_section['target-dir'] = python.target_sitepackages_dir

        # See if a limited set of modules are being installed.
        if enable is not None:
            project_section['enable'] = enable

            # Make sure there is a section so that we can configure it later.
            for module in enable:
                if module not in bindings_section:
                    bindings_section[module] = {}

        # Apply any additional component-specific values.
        if project is not None:
            project_section.update(project)

        for module in bindings_section.values():
            if isinstance(module, dict):
                module['static'] = True

                # Apply any additional component-specific values.
                if bindings is not None:
                    module.update(bindings)

        # Save the modified pyproject.toml file.
        try:
            with open('pyproject.toml', 'w') as f:
                toml.dump(pyproject, f)
        except Exception as e:
            component.error("Unable to write modified 'pyproject.toml'",
                    detail=str(e))

        # Run sip-install.
        args = [
            'sip-install',
            '--qmake', self.get_component('Qt').host_qmake,
            '--no-distinfo',
            '--concatenate', '2',
            '--no-docstrings'
        ]

        if self.target_platform_name == 'android':
            args.append('--android-abi')
            args.append(self.android_abi)

        if self.verbose_enabled:
            args.append('--verbose')

        self.run(*args)

    @property
    def provides(self):
        """ The dict of parts provided by the component. """

        parts = {
            'PyQt5': _ALL_PARTS['PyQt5'],
            'PyQt5.uic': _ALL_PARTS['PyQt5.uic'],
        }

        for name in self.installed_modules:
            name = 'PyQt5.' + name

            part = _ALL_PARTS[name]

            if name == 'PyQt5.QtCore':
                lib_dir = os.path.join(
                        self.get_component('Python').target_sitepackages_dir,
                        'PyQt5')

                part.libs = ('-L' + lib_dir,) + part.libs

            parts[name] = part

        return parts

    @property
    def pyqt_platform(self):
        """ The target platform name as recognised by PyQt. """

        pyqt_platform = self.target_platform_name

        if pyqt_platform == 'android':
            pyqt_platform = 'linux'
        elif pyqt_platform in ('ios', 'macos'):
            pyqt_platform = 'darwin'
        elif pyqt_platform == 'win':
            pyqt_platform = 'win32'

        return pyqt_platform

    @property
    def using_sip_v4(self):
        """ True if SIP v4 is being used. """

        return self.get_component('SIP').version.major == 4

    def verify(self):
        """ Verify the component. """

        if self.version < (5, 12):
            self.unsupported()

        if self.version > (5, 15):
            self.untested()

        # Check the corresponding SIP version.
        if self.using_sip_v4:
            sip_version = self.get_component('SIP').version

            if sip_version < (4, 19, 19):
                if self.version >= (5, 13, 1):
                    self.error("SIP v4.19.19 or later is required")
            elif sip_version < (4, 19, 20):
                if self.version >= (5, 14):
                    self.error("SIP v4.19.20 or later is required")
            elif sip_version < (4, 19, 23):
                if self.version >= (5, 15):
                    self.error("SIP v4.19.23 or later is required")

            if self.version >= (5, 13, 1) and sip_version < (4, 19, 19):
                self.error("SIP v4.19.19 or later is required")
            elif self.version >= (5, 15) and sip_version < (4, 19, 23):
                self.error("SIP v4.19.23 or later is required")
        else:
            self.verify_pyqt_component(self.version,
                    min_sipbuild_version=(5, 4), min_pyqtbuild_version=(1, 5))

        # This is needed by dependent components.
        if not self.get_component('Qt').ssl:
            self.disabled_features.append('PyQt_SSL')

    def verify_pyqt_component(self, min_pyqt_version, min_sipbuild_version,
            min_pyqtbuild_version):
        """ Verify a PyQt-based component.  All versions are minimum versions.
        The sipbuild and pyqtbuild version numbers are ignored if SIP v4 is
        being used.
        """

        # Check the minimum PyQt requirement, ignoring the path version and
        # making sure it is the same major version.
        min_pyqt_version = self.parse_version_number(min_pyqt_version)

        if min_pyqt_version.major != self.version.major or min_pyqt_version.minor > self.version.minor:
            self.error(
                    "PyQt v{} or later is required".format(min_pyqt_version))

        if self.using_sip_v4:
            return

        # Support for SIP v5 was added to PyQt and sub-packages during v5.13.
        # For simplicity require v5.14 if using SIP v5.
        if self.version < (5, 14):
            self.error("SIP v5 requires v5.14.0 or later")

        # Check the minimum SIP requirement.
        # TODO: this assumes that pyqtdeploy and sip are installed in the same
        # venv which may not be the case.  Therefore we either need a way of
        # querying the versions of sip and PyQt-builder from the command line
        # or we have a way of invoking sip through the API (avoiding the
        # command line).
        min_sipbuild_version = self.parse_version_number(min_sipbuild_version)

        try:
            from sipbuild import SIP_VERSION
        except ImportError:
            SIP_VERSION = 0

        sipbuild_version = self.parse_version_number(SIP_VERSION)

        if min_sipbuild_version.major == 5 and sipbuild_version.major in (5, 6):
            # We assume that all PyQt dependent projects don't use features
            # deprecated in SIP v6.
            pass
        elif min_sipbuild_version.major != sipbuild_version.major:
            self.error(
                    "SIP v{} is required".format(min_sipbuild_version.major))

        if min_sipbuild_version > sipbuild_version:
            self.error(
                    "SIP v{} or later is required".format(
                            min_sipbuild_version))

        # Check the minimum PyQt-builder requirement, making sure it is the
        # same major version.
        min_pyqtbuild_version = self.parse_version_number(
                min_pyqtbuild_version)

        try:
            from pyqtbuild import PYQTBUILD_VERSION
        except ImportError:
            PYQTBUILD_VERSION = 0

        pyqtbuild_version = self.parse_version_number(PYQTBUILD_VERSION)

        if min_pyqtbuild_version.major != pyqtbuild_version.major or min_pyqtbuild_version > pyqtbuild_version:
            self.error(
                    "PyQt-builder v{} or later is required".format(
                            min_pyqtbuild_version))

    @staticmethod
    def _get_section(name, pyproject):
        """ Return a dict containing the named section from a pyproject.toml
        file.
        """

        section = pyproject

        for section_name in name.split('.'):
            # A section might be missing so make sure it is there (and empty).
            if section_name not in section:
                section[section_name] = {}

            section = section[section_name]

            if not isinstance(section, dict):
                return {}

        return section

    def _install_using_sip_v4(self):
        """ Install using SIP v4. """

        # Create a configuration file.
        python = self.get_component('Python')
        qt = self.get_component('Qt')
        sip = self.get_component('SIP')

        cfg = '''py_platform = {0}
py_inc_dir = {1}
py_pylib_dir = {2}
py_pylib_lib = {3}
pyqt_module_dir = {4}
pyqt_sip_dir = {5}
[Qt 5.0]
pyqt_modules = {6}
'''.format(self.pyqt_platform, python.target_py_include_dir,
                self.target_lib_dir, python.target_py_lib,
                python.target_sitepackages_dir,
                os.path.join(sip.target_sip_dir, 'PyQt5'),
                ' '.join(self.installed_modules))

        if self.disabled_features:
            cfg += 'pyqt_disabled_features = {0}\n'.format(
                    ' '.join(self.disabled_features))

        cfg_name = 'pyqt5.cfg'

        with self.create_file(cfg_name) as cfg_file:
            cfg_file.write(cfg)

        # Configure, build and install.
        args = [python.host_python, 'configure.py', '--static', '--qmake',
            qt.host_qmake, '--sysroot', self.sysroot_dir, '--no-tools',
            '--no-qsci-api', '--no-designer-plugin', '--no-python-dbus',
            '--no-qml-plugin', '--no-stubs', '--configuration', cfg_name,
            '--sip', sip.host_sip, '--confirm-license', '-c', '-j2',
            '--no-dist-info']

        if self.verbose_enabled:
            args.append('--verbose')

        if self.target_platform_name == 'android':
            args.append('ANDROID_ABIS={}'.format(self.android_abi))

        self.run(*args)
        self.run(self.host_make)
        self.run(self.host_make, 'install')

    @property
    def _version_str(self):
        """ Return the version number as a string. """

        # The current convention for .0 releases began with v5.13.0.
        return '5.12' if self.version == (5, 12, 0) else str(self.version)
