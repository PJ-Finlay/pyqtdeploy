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
import subprocess
import sys

from .user_exception import UserException
from .version_number import VersionNumber


class Platform:
    """ Encapsulate a platform. """

    # The list of all platforms.
    all_platforms = []

    # The name of the make executable.
    make = 'make'
    
    def __init__(self, full_name, name, archs):
        """ Initialise the object. """

        self.full_name = full_name
        self.name = name

        # Create the architectures.
        for arch_name, arch_factory in archs:
            arch_factory(arch_name, self)

        self.all_platforms.append(self)

    def configure(self):
        """ Configure the platform for building. """

        pass

    def deconfigure(self):
        """ Deconfigure the platform for building. """

        pass

    def exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

        return name

    @classmethod
    def platform(cls, name):
        """ Return the singleton Platform instance for a platform.  A
        UserException is raised if the platform is unsupported.
        """

        for platform in cls.all_platforms:
            if platform.name == name:
                return platform

        raise UserException("'{0}' is not a supported platform".format(name))

    @staticmethod
    def run(*args, message_handler, capture=False):
        """ Run a command, optionally capturing stdout. """

        message_handler.verbose_message(
                "Running '{0}'.".format(' '.join(args)))

        detail = None
        stdout = []

        try:
            with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True) as process:
                try:
                    while process.poll() is None:
                        line = process.stdout.readline()
                        if not line:
                            continue

                        if capture:
                            stdout.append(line)
                        else:
                            message_handler.verbose_message(line.rstrip())

                    if process.returncode != 0:
                        detail = "returned exit code {}".format(
                                process.returncode)

                except Exception as e:
                    process.kill()
        except Exception as e:
            detail = str(e)

        if detail:
            raise UserException(
                    "execution of '{0}' failed: {1}".format(args[0], detail))

        return ''.join(stdout).strip() if capture else None

    def verify_as_target(self, message_handler):
        """ Verify the platform as a target. """


class Architecture:
    """ Encapsulate an architecture. """

    # The list of all architectures.
    all_architectures = []

    def __init__(self, name, platform):
        """ Initialise the object. """

        self.name = name
        self.platform = platform

        self.all_architectures.append(self)

    @classmethod
    def architecture(cls, name=None):
        """ Return a singleton Architecture instance for an architecture.  If
        name is None then the host architecture is returned.  A UserException
        is raised if the architecture is unsupported.
        """

        if name is None:
            from distutils.util import get_platform

            parts = get_platform().split('-')
            base_platform = parts[0]

            if base_platform == 'linux':
                name = 'linux'
                size = '64' if parts[1] == 'x86_64' else '32'
            elif base_platform == 'macosx':
                name = 'macos'
                size = '64' if parts[2] == 'x86_64' else '32'
            elif base_platform in ('win32', 'win'):
                name = 'win'

                # The default architecture is determined by any MSVC target.
                # If it is missing then this will be picked up when the target
                # is verified.
                size = WindowsArchitecture.msvc_target(optional=True)
                if size is None:
                    size = 64 if len(parts) == 2 and parts[1] == 'amd64' else 32
            else:
                raise UserException(
                        "'{0}' is not a supported host platform".format(
                                base_platform))

            name = '{}-{}'.format(name, size)

        # Find the architecture instance.
        for arch in cls.all_architectures:
            if arch.name == name:
                return arch

            # If it is a platform then use the first architecture.
            if arch.platform.name == name:
                return arch

        raise UserException(
                "'{0}' is not a supported architecture".format(name))

    def configure(self):
        """ Configure the architecture for building. """

        self.platform.configure()

    def deconfigure(self):
        """ Deconfigure the architecture for building. """

        self.platform.deconfigure()

    def is_targeted(self, targets):
        """ Returns True if the architecture is covered by a set of targets.
        If the set of targets has a False value then the architecture is
        covered.  If the set of targets is a sequence of platform names then
        the architecture platform must appear in the sequence.  If the set of
        targets is a string then it is an expression of architecture or
        platform names which must contain the architecture or platform name.
        """

        if targets:
            if isinstance(targets, str):
                # See if the string is a '|' separated list of targets.
                targets = targets.split('|')
                if len(targets) == 1:
                    # There was no '|' so restore the original string.
                    targets = targets[0]

            if isinstance(targets, str):
                # String targets can come from the project file (ie. the user)
                # and so need to be validated.
                if targets.startswith('!'):
                    # Note that this assumes that the target is a platform
                    # rather than an architecture.  If this is incorrect then
                    # it is a bug in the meta-data somewhere.
                    platform = Platform.platform(targets[1:])
                    covered = (self.platform is not platform)
                elif '-' in targets:
                    architecture = Architecture.architecture(targets)
                    covered = (self is architecture)
                else:
                    platform = Platform.platform(targets)
                    covered = (self.platform is platform)
            else:
                covered = (self.platform.name in targets)
        else:
            covered = True

        return covered

    def supported_target(self, target, message_handler):
        """ Check that this architecture can host a target architecture. """

        # This default implementation checks that the architectures are the
        # same.
        return target is self

    def verify_as_host(self, target, message_handler):
        """ Verify the architecture as a host for a given target. """

        # Check we can host the target.
        if not self.supported_target(target, message_handler):
            raise UserException(
                    "{0} is not a supported {1} development host".format(
                            self.name, target.name))

    def verify_as_target(self, message_handler):
        """ Verify the architecture as a target. """

        self.platform.verify_as_target(message_handler)


class ApplePlatform(Platform):
    """ Encapsulate an Apple platform. """

    # The name of the SDK.
    sdk_name = ''

    # The prefix of the directory name of the SDK.
    sdk_prefix = ''

    def verify_as_target(self, message_handler):
        """ Verify the platform as a target. """

        super().verify_as_target(message_handler)

        self.apple_sdk = self.run('xcrun', '--sdk', self.sdk_name,
                '--show-sdk-path', message_handler=message_handler,
                capture=True)

        if not self.apple_sdk:
            raise UserException(
                    "a valid '{0}' SDK could not be found".format(
                            self.sdk_name))

        # Parse the version number.
        version_str = os.path.basename(self.apple_sdk)

        if version_str.startswith(self.sdk_prefix):
            version_str = version_str[len(self.sdk_prefix):]

        if version_str.endswith('.sdk'):
            version_str = version_str[:-len('.sdk')]

        self.apple_sdk_version = VersionNumber.parse_version_number(
                version_str)


# Define and implement the different platforms and architectures.  These should
# be done in alphabetical order.

class AndroidArchitecture(Architecture):
    """ A base class for any Android architecture. """

    # The name of the Android platform's architecture ABI (as recognised by
    # qmake).
    android_abi = ''

    # The name of the Android platform's architecture.
    android_platform_arch = ''

    # The name of the Android toolchain's prefix.
    android_toolchain_prefix = ''

    # The architecture-specific clang prefix.
    clang_prefix = ''

    def verify_as_target(self, message_handler):
        """ Verify the architecture as a target. """

        super().verify_as_target(message_handler)

        # Set the various property values.
        ndk_root = self.platform.android_ndk_root
        android_api = self.platform.android_api
        toolchain_prefix = self.android_toolchain_prefix
        android_host = '{}-x86_64'.format(
                'darwin' if sys.platform == 'darwin' else 'linux')

        # Check the toolchain bin directory.
        self.android_toolchain_bin = os.path.join(ndk_root, 'toolchains',
                'llvm', 'prebuilt', android_host, 'bin')

        self.platform.android_check_exists(self.android_toolchain_bin)

        # Check the compiler.
        self.android_toolchain_cc = '{}{}-clang'.format(self.clang_prefix,
                android_api)

        self.platform.android_check_exists(
                os.path.join(self.android_toolchain_bin,
                        self.android_toolchain_cc))

    def supported_target(self, target, message_handler):
        """ Check that this architecture can host a target architecture. """

        # Android can never be a host.
        return False


class Android_arm_32(AndroidArchitecture):
    """ Encapsulate the Android 32-bit Arm architecture. """

    # Archtecture-specific values.
    android_abi = 'armeabi-v7a'
    android_platform_arch = 'arch-arm'
    android_toolchain_prefix = 'arm-linux-androideabi-'
    clang_prefix = 'armv7a-linux-androideabi'


class Android_arm_64(AndroidArchitecture):
    """ Encapsulate the Android 64-bit Arm architecture. """

    # Archtecture-specific values.
    android_abi = 'arm64-v8a'
    android_platform_arch = 'arch-arm64'
    android_toolchain_prefix = 'aarch64-linux-android-'
    clang_prefix = 'aarch64-linux-android'


class Android(Platform):
    """ Encapsulate the Android platform. """

    def __init__(self):
        """ Initialise the object. """

        super().__init__("Android", 'android',
                [('android-32', Android_arm_32),
                        ('android-64', Android_arm_64)])

    @staticmethod
    def android_check_exists(name):
        """ Raise an exception if something is missing from the NDK. """

        if not os.path.exists(name):
            raise UserException(
                    "'{0}' does not exist, make sure ANDROID_NDK_ROOT and "
                    "ANDROID_NDK_PLATFORM are set correctly".format(name))

    # The environment variables that should be set.
    _REQUIRED_ENV_VARS = ('ANDROID_NDK_ROOT', 'ANDROID_NDK_PLATFORM',
            'ANDROID_SDK_ROOT')

    def verify_as_target(self, message_handler):
        """ Verify the platform as a target. """

        super().verify_as_target(message_handler)

        # Verify required environment variables.
        for name in self._REQUIRED_ENV_VARS:
            if name not in os.environ:
                raise UserException(
                        "the {0} environment variable must be set".format(
                                name))

        self.android_ndk_root = os.environ['ANDROID_NDK_ROOT']

        self.android_ndk_sysroot = os.path.join(self.android_ndk_root,
                'sysroot')
        self.android_check_exists(self.android_ndk_sysroot)

        # Verify the NDK revision.
        self.android_ndk_version = self._get_ndk_version()
        if self.android_ndk_version is None:
            raise UserException("unable to determine the NDK revision")

        # Require a minimum of r19 so that we can assume the compiler is clang
        # and that it works properly.
        revision = self.android_ndk_version.major
        if revision < 19:
            raise UserException("NDK r19 or later is required")

        # Issue a warning for untested NDK revision.
        if revision > 21:
            message_handler.warning(
                    "versions of the NDK later than r21 are untested")

        # Verify the SDK version.
        self.android_sdk_version = self._get_sdk_version()
        if self.android_sdk_version is None:
            raise UserException("unable to determine the SDK version number")

        if self.android_sdk_version < (26, 1, 1):
            message_handler.warning(
                    "versions of the SDK earlier than v26.1.1 are untested")

        if self.android_sdk_version > (26, 1, 1):
            message_handler.warning(
                    "versions of the SDK later than v26.1.1 are untested")

        # Verify the API.
        self.android_api = self._get_api()
        if self.android_api is None:
            raise UserException(
                    "unable to determine the API level from the "
                    "ANDROID_NDK_PLATFORM environment variable")

    def _get_api(self):
        """ Return the number of the Android API. """

        ndk_platform = os.environ['ANDROID_NDK_PLATFORM']

        if not os.path.isdir(os.path.join(self.android_ndk_root, 'platforms', ndk_platform)):
            raise UserException(
                    "NDK r{0} does not support {1}".format(
                            self.android_ndk_version.major, ndk_platform))

        parts = ndk_platform.split('-')

        if len(parts) == 2 and parts[0] == 'android':
            try:
                api = int(parts[1])
            except ValueError:
                api = None

        return api

    @staticmethod
    def _get_version(source_properties):
        """ Get the version number of a source.properties file. """

        with open(source_properties) as f:
            for line in f:
                line = line.replace(' ', '')
                parts = line.split('=')
                if parts[0] == 'Pkg.Revision' and len(parts) == 2:
                    version = VersionNumber.parse_version_number(parts[1])
                    break
            else:
                version = None

        return version

    def _get_ndk_version(self):
        """ Return the version number of the NDK. """

        # source.properties is available from r11.
        source_properties = os.path.join(self.android_ndk_root,
                'source.properties')
        if os.path.isfile(source_properties):
            return self._get_version(source_properties)

        # RELEASE.TXT is available in r10 and earlier.
        release_txt = os.path.join(self.android_ndk_root, 'RELEASE.TXT')
        if os.path.isfile(release_txt):
            with open(release_txt) as f:
                for line in f:
                    if line.startswith('r'):
                        line = line[1:]
                        for i, ch in enumerate(line):
                            if not ch.isdigit():
                                line = line[:i]
                                break

                        try:
                            # Note that we ignore the minor letter.
                            return VersionNumber(int(line))
                        except UserException:
                            pass

        return None

    def _get_sdk_version(self):
        """ Return the version number of the SDK. """

        # Assume that source.properties should be available.
        source_properties = os.path.join(os.environ['ANDROID_SDK_ROOT'],
                'tools', 'source.properties')

        if not os.path.exists(source_properties):
            raise UserException(
                    "'{0}' does not exist, make sure ANDROID_SDK_ROOT is set "
                    "correctly".format(source_properties))

        return self._get_version(source_properties)

Android()


class iOS_arm_64(Architecture):
    """ Encapsulate the ios 64-bit Arm architecture. """

    def supported_target(self, target, message_handler):
        """ Check that this architecture can host a target architecture. """

        # iOS can never be a host.
        return False


class iOS(ApplePlatform):
    """ Encapsulate the iOS platform. """

    # Platform-specific values.
    sdk_name = 'iphoneos'
    sdk_prefix = 'iPhoneOS'

    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("iOS", 'ios', [('ios-64', iOS_arm_64)])

iOS()


class Linux_x86_32(Architecture):
    """ Encapsulate the Linux 32-bit x86 architecture. """

    pass


class Linux_x86_64(Architecture):
    """ Encapsulate the Linux 64-bit x86 architecture. """

    def supported_target(self, target, message_handler):
        """ Check that this architecture can host a target architecture. """

        if target.platform.name == 'android':
            return True

        return super().supported_target(target, message_handler)


class Linux(Platform):
    """ Encapsulate the Linux platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("Linux", 'linux',
                [('linux-32', Linux_x86_32), ('linux-64', Linux_x86_64)])

Linux()


class macOS_x86_64(Architecture):
    """ Encapsulate the macOS 64-bit x86 architecture. """

    def supported_target(self, target, message_handler):
        """ Check that this architecture can host a target architecture. """

        if target.platform.name in ('android', 'ios'):
            return True

        return super().supported_target(target, message_handler)


class macOS(ApplePlatform):
    """ Encapsulate the macOS platform. """

    # Platform-specific values.
    sdk_name = 'macosx'
    sdk_prefix = 'MacOSX'

    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("macOS", 'macos', [('macos-64', macOS_x86_64)])

macOS()


class WindowsArchitecture(Architecture):
    """ Encapsulate any Windows x86 architecture. """

    def supported_target(self, target, message_handler):
        """ Check that this architecture can host a target architecture. """

        if target.platform.name == 'android':
            message_handler.warning(
                    "using Windows to host Android deployment is untested")

            return True

        return super().supported_target(target, message_handler)

    @staticmethod
    def msvc_target(optional=False):
        """ Return '32' or 64' depending the architecture being targeted by
        MSVC and raise an exception if a supported version of MSVC could not be
        found.
        """

        # MSVC2015 is v14, MSVC2017 is v15 and MSVC2019 is v16.
        vs_version = os.environ.get('VisualStudioVersion', '0.0')
        vs_major = vs_version.split('.')[0]

        if vs_major == '0':
            if optional:
                return None

            raise UserException("unable to detect any MSVC compiler")

        if vs_major == '14':
            is_32 = (os.environ.get('Platform') != 'X64')
        elif vs_major in ('15', '16'):
            is_32 = (os.environ.get('VSCMD_ARG_TGT_ARCH') != 'x64')
        else:
            if optional:
                return None

            raise UserException("MSVC v{0} is unsupported".format(vs_version))

        return '32' if is_32 else '64'


class Windows_x86_32(WindowsArchitecture):
    """ Encapsulate the Windows 32-bit x86 architecture. """

    def verify_as_target(self, message_handler):
        """ Verify the architecture as a target. """

        super().verify_as_target(message_handler)

        if self.msvc_target() != '32':
            raise UserException("MSVC is not configured for a 32-bit target")


class Windows_x86_64(WindowsArchitecture):
    """ Encapsulate the Windows 64-bit x86 architecture. """

    def verify_as_target(self, message_handler):
        """ Verify the architecture as a target. """

        super().verify_as_target(message_handler)

        if self.msvc_target() != '64':
            raise UserException("MSVC is not configured for a 64-bit target")



class Windows(Platform):
    """ Encapsulate the Windows platform. """

    # The name of the make executable.
    make = 'nmake'
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("Windows", 'win',
                [('win-32', Windows_x86_32), ('win-64', Windows_x86_64)])

    def exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

        if not name.endswith('.exe'):
            name += '.exe'

        return name

Windows()
