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


class PyQtChartComponent(Component):
    """ The PyQtChart component. """

    # The component must be installed from source.
    must_install_from_source = True

    # The list of components that, if specified, should be installed before
    # this one.
    preinstalls = ['Python', 'PyQt', 'Qt', 'SIP']

    # The dict of parts provided by the component.
    provides = {
        'PyQt5.QtChart':
            ExtensionModule(deps='PyQt:PyQt5.QtWidgets', libs='-lQtChart',
                    qmake_qt='charts')
    }

    def get_archive_name(self):
        """ Return the filename of the source archive. """

        if self._commercial:
            return 'PyQtChart_commercial-{}.tar.gz'.format(
                    self._version_str)

        if self.version <= (5, 13, 0):
            return 'PyQtChart_gpl-{}.tar.gz'.format(self._version_str)

        return 'PyQtChart-{}.tar.gz'.format(self._version_str)

    def get_archive_urls(self):
        """ Return the list of URLs where the source archive might be
        downloaded from.
        """

        if self._commercial:
            return super().get_archive_urls()

        if self.version <= (5, 14):
            return ['https://www.riverbankcomputing.com/static/Downloads/PyQtChart/{}/'.format(self._version_str)]

        return self.get_pypi_urls('PyQtChart')

    def install(self):
        """ Install for the target. """

        # See if it is the commercial version.
        self._commercial = (self.get_file('pyqt-commercial.sip') is not None)

        # Unpack the source.
        self.unpack_archive(self.get_archive())

        pyqt = self.get_component('PyQt')
        if pyqt.using_sip_v4:
            self._install_using_sip_v4()
        else:
            # Install using SIP v5 or later.
            pyqt.install_pyqt_component(self)

    def verify(self):
        """ Verify the component. """

        pyqt = self.get_component('PyQt')
        pyqt.verify_pyqt_component(self.version, min_sipbuild_version=(5, 4),
                min_pyqtbuild_version=(1, 5))

    def _install_using_sip_v4(self):
        """ Install using SIP v4. """

        # Create a configuration file.
        python = self.get_component('Python')
        pyqt = self.get_component('PyQt')
        qt = self.get_component('Qt')
        sip = self.get_component('SIP')

        cfg = '''py_platform = {0}
py_inc_dir = {1}
py_pylib_dir = {2}
py_pylib_lib = {3}
py_sip_dir = {4}
[PyQt 5]
module_dir = {5}
sip_module = PyQt5.sip
'''.format(pyqt.pyqt_platform, python.target_py_include_dir,
                self.target_lib_dir, python.target_py_lib, sip.target_sip_dir,
                os.path.join(python.target_sitepackages_dir, 'PyQt5'))

        if pyqt.disabled_features:
            cfg += 'pyqt_disabled_features = {0}\n'.format(
                    ' '.join(pyqt.disabled_features))

        cfg_name = 'pyqtchart.cfg'

        with self.create_file(cfg_name) as cfg_file:
            cfg_file.write(cfg)

        # Configure, build and install.
        args = [python.host_python, 'configure.py', '--static', '--qmake',
            qt.host_qmake, '--sysroot', self.sysroot_dir, '--no-qsci-api',
            '--no-sip-files', '--no-stubs', '--configuration', cfg_name,
            '--sip', sip.host_sip, '-c', '--no-dist-info']

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
