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
import sys

from ... import AbstractQtComponent, ComponentOption


class QtComponent(AbstractQtComponent):
    """ The Qt component. """

    # The list of components that, if specified, should be installed before
    # this one.
    preinstalls = ['OpenSSL', 'zlib']

    def __init__(self, *args, **kwargs):
        """ Initialise the component. """

        super().__init__(*args, **kwargs)

        self._host_qmake = None

    def get_archive_name(self):
        """ Return the filename of the source archive. """

        return 'qt-everywhere-src-{}.tar.xz'.format(self.version)

    def get_archive_urls(self):
        """ Return the list of URLs where the source archive might be
        downloaded from.
        """

        return ['https://download.qt.io/archive/qt/{}.{}/{}/single/'.format(
                self.version.major, self.version.minor, self.version)]

    def get_options(self):
        """ Return a list of ComponentOption objects that define the components
        configurable options.
        """

        options = super().get_options()

        options.append(
                ComponentOption('configure_options', type=list,
                        help="The additional options to be passed to "
                                "'configure' when building from source."))

        options.append(
                ComponentOption('disabled_features', type=list,
                        help="The features that are disabled when building "
                                "from source."))

        options.append(
                ComponentOption('edition', values=['commercial', 'opensource'],
                        help="The Qt edition being used when building from "
                                "source."))

        options.append(
                ComponentOption('ssl',
                        values=['openssl-linked', 'openssl-runtime',
                                'securetransport'],
                        help="Enable SSL support."))

        options.append(
                ComponentOption('skip', type=list,
                        help="The Qt modules to skip when building from "
                                "source."))

        options.append(
                ComponentOption('static_msvc_runtime', type=bool,
                        help="Set if the MSVC runtime should be statically "
                                "linked."))

        return options

    @property
    def host_qmake(self):
        """ The full pathname of the host qmake executable. """

        if self._host_qmake is None:
            if self.install_from_source:
                self._host_qmake = os.path.join(self.sysroot_dir, 'Qt', 'bin',
                        self.host_exe('qmake'))
            else:
                self._host_qmake = self.find_exe('qmake')

        return self._host_qmake

    @host_qmake.setter
    def host_qmake(self, value):
        """ Set the full pathname of the host qmake executable. """

        self._host_qmake = value

    def install(self):
        """ Install for the target. """

        if self.install_from_source:
            self._install_from_source()

    def sdk_configure(self, platform_name):
        """ Perform any platform-specific SDK configuration. """

        if platform_name == 'ios':
            if 'IPHONEOS_DEPLOYMENT_TARGET' not in os.environ:
                if self.version >= (5, 14):
                    dep_target = '12.0'
                else:
                    dep_target = '11.0'

                os.environ['IPHONEOS_DEPLOYMENT_TARGET'] = dep_target
                setattr(self, '_ios_dep_target_set', True)

        elif self.target_platform_name == 'macos':
            if 'MACOSX_DEPLOYMENT_TARGET' not in os.environ:
                if self.version >= (5, 14):
                    dep_target = '10.13'
                else:
                    dep_target = '10.12'

                os.environ['MACOSX_DEPLOYMENT_TARGET'] = dep_target
                setattr(self, '_macos_dep_target_set', True)

    def sdk_deconfigure(self, platform_name):
        """ Remove any platform-specific SDK configuration applied by a
        previous call to sdk_configure().
        """

        if platform_name == 'ios':
            if getattr(self, '_ios_dep_target_set', False):
                del os.environ['IPHONEOS_DEPLOYMENT_TARGET']
                delattr(self, '_ios_dep_target_set')

        elif platform_name == 'macos':
            if getattr(self, '_macos_dep_target_set', False):
                del os.environ['MACOSX_DEPLOYMENT_TARGET']
                delattr(self, '_macos_dep_target_set')

    def verify(self):
        """ Verify the component. """

        # Do some basic version checks.
        if self.version >= 6:
            self.unsupported()

        if self.version < (5, 12):
            self.unsupported()

        if self.version > (5, 15):
            self.untested()

        # If we are linking against OpenSSL then get its version number.
        if self.ssl == 'openssl-linked':
            self._openssl = self.get_component('OpenSSL')
        else:
            self._openssl = None

        if self.install_from_source:
            # We don't support cross-compiling Qt.
            if self.host_platform_name != self.target_platform_name:
                self.error("cross compiling Qt is not supported")

            if not self.edition:
                self.error(
                        "the 'edition' option must be specified when building "
                        "from source")

            # Make sure we have a Python v2.7 installation on Windows.
            if self.host_platform_name == 'win':
                self._py_27 = self.get_python_install_path(2, 7)

            # Check the OpenSSL version.
            if self._openssl is not None:
                if self.version >= (5, 15):
                    if self._openssl.version != (1, 1, 1):
                        self.error(
                                "v{0} requires OpenSSL v1.1.1".format(
                                        self.version))
        else:
            self._verify_installed_version()

            # Check the OpenSSL version for compatibility with the binary
            # installers.
            if self._openssl is not None:
                if self.version >= (5, 12, 4):
                    if self._openssl.version != (1, 1, 1):
                        self.error(
                                "v{0} requires OpenSSL v1.1.1".format(
                                        self.version))
                else:
                    if self._openssl.version != (1, 0, 2):
                        self.error(
                                "v{0} requires OpenSSL v1.0.2".format(
                                        self.version))

        # Platform-specific checks.
        if self.target_platform_name == 'android':
            if self.android_api < 21:
                self.error("Android API level 21 or greater is required")

            if self.version >= (5, 13, 2) or (5, 12, 6) <= self.version <= (5, 13, 0):
                if self.android_ndk_version not in (20, 21):
                    self.error(
                            "v{0} requires NDK r20 or r21".format(
                                    self.version))
            else:
                if self.android_ndk_version != 19:
                    self.error("v{0} requires NDK r19".format(self.version))
        elif self.target_platform_name == 'ios':
            if self.version >= (5, 13) and self.apple_sdk_version < (13, 2):
                self.error(
                        "v{0} requires iOS SDK v13.2 (Xcode 11) or "
                        "later".format(self.version))
            elif self.apple_sdk_version < (12, 1):
                self.error(
                        "v{0} requires iOS SDK v12.1 (Xcode 10) or "
                        "later".format(self.version))
        elif self.target_platform_name == 'mac':
            if self.apple_sdk_version < (10, 4):
                self.error(
                        "v{0} requires macOS SDK v10.4 (Xcode 10) or "
                        "later".format(self.version))

    def _install_from_source(self):
        """ Install Qt from source. """

        self.unpack_archive(self.get_archive())

        if self.host_platform_name == 'win':
            configure = 'configure.bat'

            dx_setenv = os.path.expandvars(
                    '%DXSDK_DIR%\\Utilities\\bin\\dx_setenv.cmd')

            if os.path.exists(dx_setenv):
                self.run(dx_setenv)

            original_path = os.environ['PATH']
            new_path = [original_path]

            new_path.insert(0, os.path.abspath('gnuwin32\\bin'))
            new_path.insert(0, self._py_27)

            os.environ['PATH'] = ';'.join(new_path)
        else:
            configure = './configure'
            original_path = None

        target_qt_dir = os.path.join(self.sysroot_dir, 'Qt')

        args = [configure, '-prefix', target_qt_dir, '-' + self.edition,
                '-confirm-license', '-static', '-release', '-nomake',
                'examples', '-nomake', 'tools',
                '-I', self.target_include_dir,
                '-L', self.target_lib_dir]

        if sys.platform == 'win32' and self.static_msvc_runtime:
            args.append('-static-runtime')

        if self.ssl:
            args.append('-ssl')

            if self.ssl == 'securetransport':
                args.append('-securetransport')

            elif self.ssl == 'openssl-linked':
                args.append('-openssl-linked')

                if sys.platform == 'win32':
                    if self._openssl.version >= (1, 1):
                        openssl_libs = '-llibssl -llibcrypto'
                    else:
                        openssl_libs = '-lssleay32 -llibeay32'

                    args.append('OPENSSL_LIBS=' + openssl_libs + ' -lws2_32 -lgdi32 -ladvapi32 -lcrypt32 -luser32')

            elif self.ssl == 'openssl-runtime':
                args.append('-openssl-runtime')

        else:
            args.append('-no-ssl')

        if self.configure_options:
            args.extend(self.configure_options)

        xcb_enabled = True
        if self.disabled_features:
            for feature in self.disabled_features:
                args.append('-no-feature-' + feature)

                if feature == 'xcb':
                    xcb_enabled = False

        if self.skip:
            for module in self.skip:
                args.append('-skip')
                args.append(module)

        if sys.platform == 'win32':
            # These cause compilation failures (although maybe only with static
            # builds).
            args.append('-skip')
            args.append('qtimageformats')
        elif sys.platform == 'linux' and self.version < (5, 15) and xcb_enabled:
            args.append('-qt-xcb')

        self.run(*args)
        self.run(self.host_make)
        self.run(self.host_make, 'install')

        if original_path is not None:
            os.environ['PATH'] = original_path

    def _verify_installed_version(self):
        """ Verify that the installed version is compatible with the specified
        version.
        """

        for line in self.run(self.host_qmake, '-query', capture=True).split():
            parts = line.split(':')
            if len(parts) == 2 and parts[0] == 'QT_VERSION':
                host_version = self.parse_version_number(parts[1])
                break
        else:
            self.error(
                    "unable to determine Qt version number from {0}".format(
                            self.host_qmake))

        if self.version != host_version:
            self.error(
                    "v{0} is specified but the host installation is "
                    "v{1}".format(self.version, host_version))
