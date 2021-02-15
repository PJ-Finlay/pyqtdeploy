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

from ... import Component, ComponentOption, ExtensionModule


class QScintillaComponent(Component):
    """ The QScintilla component. """

    # The component must be installed from source.
    must_install_from_source = True

    # The list of components that, if specified, should be installed before
    # this one.
    preinstalls = ['Python', 'PyQt', 'Qt', 'SIP']

    def get_archive_name(self):
        """ Return the filename of the source archive. """

        if self._commercial:
            return 'QScintilla_commercial-{}.tar.gz'.format(
                    self._version_str)

        if self.version <= (2, 11, 2):
            return 'QScintilla_gpl-{}.tar.gz'.format(self._version_str)

        return 'QScintilla-{}.tar.gz'.format(self._version_str)

    def get_archive_urls(self):
        """ Return the list of URLs where the source archive might be
        downloaded from.
        """

        if self._commercial:
            return super().get_archive_urls()

        return ['https://www.riverbankcomputing.com/static/Downloads/QScintilla/{}/'.format(self._version_str)]

    def install(self):
        """ Install for the target. """

        pyqt = self.get_component('PyQt')

        # See if it is the commercial version.
        self._commercial = (self.get_file('pyqt-commercial.sip') is not None)

        # Unpack the source.
        self.unpack_archive(self.get_archive())

        # Build the static C++ library.
        os.chdir('Qt4Qt5')

        # Somewhere between Qt v5.13 and v5.15 'printsupport' was removed from
        # the iOS mkspecs.  We patch the .pro and feature files rather than
        # require a fixed version of QScintilla.
        if self.target_platform_name == 'ios':
            self.patch_file('qscintilla.pro', self._patch_pro_for_ios)
            self.patch_file(
                    os.path.join('features_staticlib', 'qscintilla2.prf'),
                    self._patch_pro_for_ios)

        qmake_args = [self.get_component('Qt').host_qmake, 'CONFIG+=staticlib',
                'DEFINES+=SCI_NAMESPACE']

        if self.target_platform_name == 'android':
            qmake_args.append('ANDROID_ABIS={}'.format(self.android_abi))

        if not pyqt.using_sip_v4:
            # PyQt-builder explcitly specifies the release/debug mode and we
            # can't make assumptions about the default.
            qmake_args.append('CONFIG+=release')

        self.run(*qmake_args)

        self.run(self.host_make)
        self.run(self.host_make, 'install')
        os.chdir('..')

        # Build the static Python bindings.
        if pyqt.using_sip_v4:
            self._install_using_sip_v4()
        else:
            # Install using SIP v5 or later.  If there is no printer support
            # then make sure we don't try and import it.
            if self._is_print_support:
                bindings_config = None
            else:
                bindings_config = {
                    'disabled-features': ['PyQt_Printer']
                }

            # The QScintilla pyproject.toml file doesn't have a bindings
            # section so we need to explicitly specify the enabled modules.
            pyqt.install_pyqt_component(self, bindings=bindings_config,
                    enable=['Qsci'])

    @property
    def provides(self):
        """ The dict of parts provided by the component. """

        deps = 'PyQt:PyQt5.QtWidgets'

        if self._is_print_support:
            deps = (deps, 'PyQt:PyQt5.QtPrintSupport')

        return {
            'PyQt5.Qsci':
                ExtensionModule(deps=deps, libs='-lQsci',
                        qmake_config='qscintilla2')
        }

    def verify(self):
        """ Verify the component. """

        # We don't want to support old versions.
        if self.version < (2, 11):
            self.unsupported()

        if self.version > (2, 11, 5):
            self.untested()

        # The Scintilla code uses C++ library functions that are missing prior
        # to NDK v14.
        if self.target_platform_name == 'android' and self.android_ndk_version < 14:
            self.error("Android NDK r14 or later is required")

        pyqt = self.get_component('PyQt')
        pyqt.verify_pyqt_component(pyqt.version, min_sipbuild_version=(5, 4),
                min_pyqtbuild_version=(1, 5))

    def _install_using_sip_v4(self):
        """ Install using SIP v4. """

        os.chdir('Python')

        # Create a configuration file.
        python = self.get_component('Python')
        pyqt = self.get_component('PyQt')
        qt = self.get_component('Qt')
        sip = self.get_component('SIP')

        cfg = '''py_inc_dir = {0}
py_pylib_dir = {1}
py_pylib_lib = {2}
py_sip_dir = {3}
[PyQt 5]
module_dir = {4}
sip_module = PyQt5.sip
'''.format(python.target_py_include_dir, self.target_lib_dir,
                python.target_py_lib, sip.target_sip_dir,
                os.path.join(python.target_sitepackages_dir, 'PyQt5'))

        # If there is no printer support then make sure we don't try and import
        # it.
        disabled_features = pyqt.disabled_features

        if not self._is_print_support and 'PyQt_Printer' not in disabled_features:
            disabled_features = list(disabled_features)
            disabled_features.append('PyQt_Printer')

        if disabled_features:
            cfg += 'pyqt_disabled_features = {0}\n'.format(
                    ' '.join(disabled_features))

        cfg_name = 'qscintilla.cfg'

        with self.create_file(cfg_name) as cfg_file:
            cfg_file.write(cfg)

        # Configure, build and install.
        args = [python.host_python, 'configure.py', '--static', '--qmake',
            qt.host_qmake, '--sysroot', self.sysroot_dir, '--no-qsci-api',
            '--no-sip-files', '--no-stubs', '--configuration', cfg_name,
            '--sip', sip.host_sip, '-c', '--pyqt', 'PyQt5', '--no-dist-info']

        if self.verbose_enabled:
            args.append('--verbose')

        if self.target_platform_name == 'android':
            args.append('ANDROID_ABIS={}'.format(self.android_abi))

        self.run(*args)
        self.run(self.host_make)
        self.run(self.host_make, 'install')

    @property
    def _is_print_support(self):
        """ Return True if print support is available. """

        return 'QtPrintSupport' in self.get_component('PyQt').installed_modules

    @staticmethod
    def _patch_pro_for_ios(line, patch_file):
        """ Disable all support for printing in the .pro file. """

        if 'qsciprinter' in line:
            pass
        else:
            patch_file.write(line.replace('printsupport', ''))

    @property
    def _version_str(self):
        """ Return the version number as a string. """

        # The current convention for .0 releases began after v2.11.0.
        return '2.11' if self.version == (2, 11, 0) else str(self.version)
