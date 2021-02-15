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

from ... import Component, ComponentLibrary, ComponentOption


class zlibComponent(Component):
    """ The zlib component. """

    def get_archive_name(self):
        """ Return the filename of the source archive. """

        return 'zlib-{}.tar.gz'.format(self.version)

    def get_archive_urls(self):
        """ Return the list of URLs where the source archive might be
        downloaded from.
        """

        return ['https://zlib.net/']

    def get_options(self):
        """ Return a list of ComponentOption objects that define the components
        configurable options.
        """

        options = super().get_options()

        options.append(
                ComponentOption('static_msvc_runtime', type=bool,
                        help="Set if the MSVC runtime should be statically "
                                "linked."))

        return options

    def install(self):
        """ Install for the target. """

        if not self.install_from_source:
            return

        # Unpack the source.
        self.unpack_archive(self.get_archive())

        if self.target_platform_name == 'win':
            make_args = [self.host_make, '-f', 'win32\\Makefile.msc',
                    'zlib.lib']

            if self.static_msvc_runtime:
                make_args.append('LOC=-MT')

            self.run(*make_args)

            self.copy_file('zconf.h', self.target_include_dir)
            self.copy_file('zlib.h', self.target_include_dir)
            self.copy_file('zlib.lib', self.target_lib_dir)

        elif self.target_platform_name == 'android':
            # Configure the environment.
            original_path = self.add_to_path(self.android_toolchain_bin)
            os.environ['CROSS_PREFIX'] = self.android_toolchain_prefix
            os.environ['CC'] = self.android_toolchain_cc

            # It isn't clear why this is needed, possibly a clang bug.
            if self.target_arch_name == 'android-32':
                os.environ['CFLAGS'] = '-fPIC'

            self.run('./configure', '--static', '--prefix=' + self.sysroot_dir)
            self.run(self.host_make,
                    'AR=' + self.android_toolchain_prefix + 'ar cqs',
                    'install')

            if self.target_arch_name == 'android-32':
                del os.environ['CFLAGS']

            del os.environ['CROSS_PREFIX']
            del os.environ['CC']
            os.environ['PATH'] = original_path

        else:
            if self.target_platform_name == 'ios':
                # Note that this doesn't create a library that can be used with
                # an x86-based simulator.
                os.environ['CFLAGS'] = '-fembed-bitcode -O3 -arch arm64 -isysroot ' + self.apple_sdk

            self.run('./configure', '--static', '--prefix=' + self.sysroot_dir)
            self.run(self.host_make)
            self.run(self.host_make, 'install')

            if self.target_platform_name == 'ios':
                del os.environ['CFLAGS']

    @property
    def provides(self):
        """ The dict of parts provided by the component. """

        return {'zlib': ComponentLibrary(libs=('win#-lzlib', '!win#-lz'))}

    def verify(self):
        """ Verify the component. """

        # Make sure any installed version is the one specified.
        if not self.install_from_source:
            self._verify_installed_version()

    def _verify_installed_version(self):
        """ Verify that the installed version is compatible with the specified
        version.
        """

        # We support native versions for everything except Windows.
        if self.target_platform_name == 'android':
            root_dir = self.android_ndk_sysroot
        elif self.target_platform_name in ('ios', 'macos'):
            root_dir = self.apple_sdk
        elif self.target_platform_name == 'linux':
            root_dir = ''
        else:
            self.error(
                    "using an existing installation is not supported for "
                    "Windows targets")

        version_file = root_dir + '/usr/include/zlib.h'
        version_line = self.get_version_from_file('ZLIB_VERSION', version_file)

        version_str = version_line.split()[-1]
        if version_str.startswith('"'):
            version_str = version_str[1:]
        if version_str.endswith('"'):
            version_str = version_str[:-1]

        installed_version = self.parse_version_number(version_str)

        if self.version != installed_version:
            self.error(
                    "v{0} is specified but the host installation is "
                            "v{1}".format(self.version, installed_version))
