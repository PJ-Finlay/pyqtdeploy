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


import glob
import os
import shutil

from ... import Component, ComponentLibrary, ComponentOption


# OpenSSL currently has 3 relevent 'releases': v1.0.2, v1.1.0 and v1.1.1.
#
# Python v3.5 and v3.6 use v1.0.2, Python v3.7 uses v1.1.0 (and uses v1.1.1
# from v3.7.4) and Python v3.8 and later use v1.1.1.  In addition Python v3.6.4
# and earlier contain a patch for OpenSSL for macOS which requires an exact
# version of OpenSSL to ensure the patch doesn't fail.  Specifically, Python
# v3.5.0 and v3.5.1 requires OpenSSL v1.0.2d, Python v3.5.2 requires OpenSSL
# v1.0.2f, Python v3.5.3 requires OpenSSL v1.0.2j, and Python v3.5.4 to Python
# v3.6.4 require OpenSSL v1.0.2k.
#
# Qt v5.15 requires OpenSSL v1.1.1, earlier versions only require OpenSSL
# v1.0.0.  The binary installers of Qt v5.12.4 and later are built against
# OpenSSL v1.1.1.


class OpenSSLComponent(Component):
    """ The OpenSSL component. """

    def get_archive_name(self):
        """ Return the filename of the source archive. """

        return 'openssl-{}.tar.gz'.format(self.version)

    def get_archive_urls(self):
        """ Return the list of URLs where the source archive might be
        downloaded from.
        """

        # The URLs depend on the version number.
        if self.version >= (1, 1, 1):
            sub_url = '1.1.1'
        elif self.version >= (1, 1, 0):
            sub_url = '1.1.0'
        else:
            sub_url = '1.0.2'

        return ['https://www.openssl.org/source/old/{}/'.format(sub_url),
                'https://www.openssl.org/source/']

    def install(self):
        """ Install for the target. """

        if not self.install_from_source:
            return

		# Unpack the source.
        self.unpack_archive(self.get_archive())

        # Set common options.
        common_options = ['--prefix=' + self.sysroot_dir, 'no-engine']

        if self.host_platform_name == 'win' and self.find_exe('nasm', required=False) is None:
            self.verbose(
                    "disabling assembler optimisations as nasm isn't "
                            "installed")
            common_options.append('no-asm')

        if self.version >= (1, 1):
            self._install_1_1(common_options)
        else:
            self._install_1_0_2(common_options)

    @property
    def provides(self):
        """ The dict of parts provided by the component. """

        if self.target_platform_name == 'win' and self.version == (1, 0):
            part = ComponentLibrary(libs=('libeay32.lib', 'ssleay32.lib'))
        else:
            bundle_shared_libs = self.target_platform_name == 'android'

            part = ComponentLibrary(
                    libs=('win#-llibcrypto', '!win#-lcrypto', 'win#-llibssl',
                            '!win#-lssl'),
                    bundle_shared_libs=bundle_shared_libs)

        return {'openssl': part}

    def sdk_configure(self, platform_name):
        """ Perform any platform-specific SDK configuration. """

        if platform_name == 'android':
            # OpenSSL v1.1.1 expects ANDROID_NDK_HOME to be set rather than
            # ANDROID_NDK_ROOT.
            if 'ANDROID_NDK_HOME' not in os.environ:
                os.environ['ANDROID_NDK_HOME'] = self.android_ndk_root
                setattr(self, '_android_ndk_home_set', True)

    def sdk_deconfigure(self, platform_name):
        """ Remove any platform-specific SDK configuration applied by a
        previous call to sdk_configure().
        """

        if platform_name == 'android':
            if getattr(self, '_android_ndk_home_set', False):
                del os.environ['ANDROID_NDK_HOME']
                delattr(self, '_android_ndk_home_set')

    def verify(self):
        """ Verify the component. """

        # We only support v1.0.2 and later.
        if (1, 0, 2) > self.version > (1, 1, 1):
            self.unsupported()

        # Make sure any installed version is the one specified.
        if not self.install_from_source:
            self._verify_installed_version()

            # That's all we need to check if the installed version is used.
            return

        # We only cross-compile to Android.
        host = self.host_platform_name
        target = self.target_platform_name

        if target != host and target != 'android':
            self.error(
                    "installing for {0} on {1} is not supported".format(target,
                            host))

        # Check the required host tools are available.
        tools = ['perl']

        # See if we will need to apply a patch from the Python source code.
        if target == 'macos' and self.version == (1, 0, 2):
            python = self.get_component('Python')
            if python.version <= (3, 6, 4):
                # The exact version of OpenSSL must be used otherwise the patch
                # may fail.
                if python.version >= (3, 5, 4):
                    if self.version.suffix != 'k':
                        self.error(
                                "v1.0.2k is required by Python v{0}".format(
                                        python.version))
                elif python.version == (3, 5, 3):
                    if self.version.suffix != 'j':
                        self.error(
                                "v1.0.2j is required by Python v{0}".format(
                                        python.version))
                elif python.version == (3, 5, 2):
                    if self.version.suffix != 'f':
                        self.error(
                                "v1.0.2f is required by Python v{0}".format(
                                        python.version))
                else:
                    if self.version.suffix != 'd':
                        self.error(
                                "v1.0.2d is required by Python v{0}".format(
                                        python.version))

                tools.append('patch')

        # Check the host tools are available.
        for tool in tools:
            self.find_exe(tool)

    def _install_1_1(self, common_options):
        """ Install v1.1 for supported platforms. """

        if self.target_platform_name == self.host_platform_name:
            # We are building natively.

            if self.target_platform_name == 'win':
                self._install_1_1_win(common_options)
            else:
                args = ['./config', 'no-shared']
                args.extend(common_options)

                self.run(*args)
                self.run(self.host_make)
                self.run(self.host_make, 'install')
        else:
            # We are cross-compiling.

            if self.target_platform_name == 'android':
                self._install_1_1_android(common_options)

    def _install_1_1_android(self, common_options):
        """ Install v1.1 for Android on either Linux or MacOS hosts. """

        # Configure the environment.
        original_path = self.add_to_path(self.android_toolchain_bin)

        configure_args = ['perl', 'Configure']

        configure_args.extend(common_options)

        configure_args.append('shared')
        configure_args.append('-D__ANDROID_API__={}'.format(self.android_api))

        if self.target_arch_name == 'android-32':
            os_compiler = 'android-arm'
        else:
            os_compiler = 'android-arm64'

        configure_args.append(os_compiler)

        self.run(*configure_args)

        self.run(self.host_make, 'SHLIB_VERSION_NUMBER=', 'SHLIB_EXT=_1_1.so',
                'build_libs')

        # Install the shared libraries.  Qt requires the versioned name and
        # Python requires the unversioned symbolic link.
        for lib in ('libcrypto', 'libssl'):
            versioned = lib + '_1_1.so'

            shutil.copy(versioned, self.target_lib_dir)

            link = os.path.join(self.target_lib_dir, lib + '.so')
            try:
                os.remove(link)
            except:
                pass

            os.symlink(versioned, link)

        # Install the header files.
        headers_dir = os.path.join(self.target_include_dir, 'openssl')
        shutil.rmtree(headers_dir, ignore_errors=True)
        shutil.copytree(os.path.join('include', 'openssl'), headers_dir)

        # Restore the environment.
        os.environ['PATH'] = original_path

    def _install_1_1_win(self, common_options):
        """ Install v1.1 for Windows. """

        # Set the architecture-specific values.
        if self.target_arch_name.endswith('-64'):
            target = 'VC-WIN64A'
        else:
            target = 'VC-WIN32'

        args = ['perl', 'Configure', target, 'no-shared',
                '--openssldir=' + self.sysroot_dir + '\\ssl']
        args.extend(common_options)

        self.run(*args)
        self.run(self.host_make)
        self.run(self.host_make, 'install')

    def _install_1_0_2(self, common_options):
        """ Install v1.0.2 for supported platforms. """

        # Add the common options that Python used prior to v3.7.
        common_options.extend([
            'no-krb5',
            'no-idea',
            'no-mdc2',
            'no-rc5',
            'no-zlib',
            'enable-tlsext',
            'no-ssl2',
            'no-ssl3',
            'no-ssl3-method',
        ])

        if self.target_platform_name == self.host_platform_name:
            # We are building natively.

            if self.target_arch_name == 'macos-64':
                self._install_1_0_2_macos(common_options)

            elif self.target_platform_name == 'win':
                self._install_1_0_2_win(common_options)
        else:
            # We are cross-compiling.

            if self.target_platform_name == 'android':
                self._install_1_0_2_android(common_options)

    def _install_1_0_2_android(self, common_options):
        """ Install v1.0.2 for Android on either Linux or MacOS hosts. """

        # Configure the environment.
        original_path = self.add_to_path(self.android_toolchain_bin)
        os.environ['MACHINE'] = 'arm7'
        os.environ['RELEASE'] = '2.6.37'
        os.environ['SYSTEM'] = 'android'
        os.environ['ARCH'] = 'arm'
        os.environ['ANDROID_DEV'] = os.path.join(self.android_ndk_sysroot,
                'usr')
        os.environ['CC'] = self.android_toolchain_cc
        os.environ['AR'] = self.android_toolchain_prefix + 'ar'
        os.environ['RANLIB'] = self.android_toolchain_prefix + 'ranlib'

        # Configure, build and install.
        args = ['perl', 'Configure', 'shared']
        args.extend(common_options)
        args.append('android')

        self.run(*args)

        # Patch the Makefile for clang.
        with open('Makefile') as f:
            mf = f.read()

        mf = mf.replace('-mandroid', '')

        with open('Makefile', 'w') as f:
            f.write(mf)

        self.run(self.host_make, 'depend')
        self.run(self.host_make,
                'CALC_VERSIONS="SHLIB_COMPAT=; SHLIB_SOVER="', 'build_libs',
                'build_apps')
        self.run(self.host_make, 'install_sw')

        for lib in ('libcrypto', 'libssl'):
            # Remove the static library that was also built.
            os.remove(os.path.join(self.target_lib_dir, lib + '.a'))

            # The unversioned .so was installed and then overwritten with a
            # symbolic link to the non-existing versioned .so, so install it
            # again.
            lib_so = lib + '.so'
            installed_lib_so = os.path.join(self.target_lib_dir, lib_so)

            os.remove(installed_lib_so)
            self.copy_file(lib_so, installed_lib_so)

        del os.environ['CC']
        del os.environ['AR']
        del os.environ['RANLIB']
        del os.environ['MACHINE']
        del os.environ['RELEASE']
        del os.environ['SYSTEM']
        del os.environ['ARCH']
        del os.environ['ANDROID_DEV']
        os.environ['PATH'] = original_path

    def _install_1_0_2_macos(self, common_options):
        """ Install v1.0.2 for 64 bit macOS. """

        # Find and apply any Python patch.
        python = self.get_component('Python')
        if python.version <= (3, 6, 4):
            python_archive = python.get_archive()
            python_dir = self.unpack_archive(python_archive, chdir=False)

            patches = glob.glob(python_dir + '/Mac/BuildScript/openssl*.patch')

            if len(patches) > 1:
                self.error(
                        "found multiple OpenSSL patches in the Python source "
                                "tree")

            if len(patches) == 1:
                self.run('patch', '-p1', '-i', patches[0])

            shutil.rmtree(python_dir, ignore_errors=True)

        # Configure, build and install.
        sdk_env = 'OSX_SDK=' + self.apple_sdk

        args = ['perl', 'Configure',
                'darwin64-x86_64-cc', 'enable-ec_nistp_64_gcc_128']
        args.extend(common_options)

        self.run(*args)
        self.run(self.host_make, 'depend', sdk_env)
        self.run(self.host_make, 'all', sdk_env)
        self.run(self.host_make, 'install_sw', sdk_env)

    def _install_1_0_2_win(self, common_options):
        """ Install v1.0.2 for Windows. """

        # Set the architecture-specific values.
        if self.target_arch_name.endswith('-64'):
            target = 'VC-WIN64A'
            post_config = 'ms\\do_win64a.bat'
        else:
            target = 'VC-WIN32'
            post_config = 'ms\\do_ms.bat' if 'no-asm' in common_options else 'ms\\do_nasm.bat'

        # 'no-engine' seems to be broken on Windows.  It (correctly) doesn't
        # install the header file but tries to build the engines anyway.
        common_options.remove('no-engine')

        # Configure, build and install.
        args = ['perl', 'Configure', target]
        args.extend(common_options)

        self.run(*args)
        self.run(post_config)
        self.run(self.host_make, '-f', 'ms\\nt.mak')
        self.run(self.host_make, '-f', 'ms\\nt.mak', 'install')

    def _verify_installed_version(self):
        """ Verify that the installed version is compatible with the specified
        version.
        """

        # We only support Linux native versions.
        if self.target_platform_name != 'linux':
            self.error(
                    "using an existing installation is only supported for "
                    "Linux targets.")

        version_line = self.get_version_from_file('OPENSSL_VERSION_NUMBER',
                '/usr/include/openssl/opensslv.h')

        # Extract the version number from the line.
        version = version_line.split()[-1]
        if version.startswith('0x'):
            version = version[2:]
        if version.endswith('L'):
            version = version[:-1]

        try:
            version = int(version, base=16)
        except ValueError:
            self.error("unable to extract the version number")

        major = (version >> 28) & 0xff
        minor = (version >> 20) & 0xff
        patch = (version >> 12) & 0xff

        # Note that we ignore any suffix and only check the parts that affect
        # binary compatibility.
        if self.version != (major, minor, patch):
            self.error(
                    "v{0} is specified but the host installation is "
                            "v{1}.{2}.{3}".format(self.version, major, minor,
                                    patch))
