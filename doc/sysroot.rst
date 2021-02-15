.. _ref-building-a-sysroot:

.. program:: pyqtdeploy-sysroot

Building a System Root Directory
================================

:program:`pyqtdeploy-sysroot` is used to create a target-specific system root
directory (*sysroot*) containing any *components* required by the application.

:program:`pyqtdeploy-sysroot` is actually a wrapper around a number of
component plugins.  A plugin, written in Python, is responsible for installing
the individual *parts* that make up a component.  A part may be a Python
package, an extension module or a supporting library.

A sysroot is defined by a `TOML <https://github.com/toml-lang/toml>`__
specification file.  This contains a section for each component to install.
The key/value options of a section determine how the component is configured.
Component sections may have target-specific sub-sections so that they can be
configured on a target by target basis.

The components are installed in the correct order irrespective of where they
appear in the specification file.

A component will only be installed in a sysroot if it hasn't already been done.
However if the installed version is different then all components will be
re-installed.  This is done because some components take a long time to
install (building Qt from source being the obvious example) making it very
inconvenient when debugging the installation of a later component.

An API is provided to allow you to develop your own component plugins.  If you
develop a plugin for a commonly used component then please consider
contributing it so that it can be included in a future release of
:program:`pyqtdeploy`.


Standard Component Plugins
--------------------------

The following component plugins are included as standard with
:program:`pyqtdeploy`.

**OpenSSL**
    This provides the OpenSSL libraries for v1.0.2 and later on Android (as a
    shared library), Linux (using the OS supplied library), macOS (as a static
    library) and Windows (as a static library).  When building from source it
    requires ``perl`` to be installed on :envvar:`PATH`.

**PyQt**
    This provides a static version of the PyQt5 extension modules for all
    target architectures.

**PyQt3D**
    This provides a static version of the PyQt3D extension modules for all
    target architectures.

**PyQtChart**
    This provides a static version of the PyQtChart extension module for all
    target architectures.

**PyQtDataVisualization**
    This provides a static version of the PyQtDataVisualization extension
    module for all target architectures.

**PyQtPurchasing**
    This provides a static version of the PyQtPurchasing extension module for
    all target architectures.

**PyQtWebEngine**
    This provides a static version of the PyQtWebEngine extension module for
    all target architectures.

**Python**
    This will provide Python from source, or use an existing installation, for
    both the host and target architectures.  Building the host version from
    source is not supported on Windows.  Installing the host version from an
    existing installation is not supported on Android or iOS.  The target
    version of the Python library and extension modules built from source will
    be built statically.  Installing the target version from an existing
    installation is only supported on Windows.

**QScintilla**
    This provides a static version of the QScintilla library and Python
    extension module for all target architectures.

**Qt**
    This will provide a static version of Qt5 from source (but not for the
    Android and iOS targets).  It will use an existing installation created by
    the standard Qt installer.  When building from source on Windows it
    requires Python v2.7 to be installed (but it does not need to be on
    :envvar:`PATH`).

**SIP**
    This provides a static version of the :mod:`sip` extension module for all
    target architectures.

**zlib**
    This provides a static version of the zlib library for all target
    architectures.  It can also use an OS supplied library for all targets
    except Windows.


Creating a Sysroot Specification File
-------------------------------------

The following specification file contains a section for each of the standard
component plugins.  (You can also download a copy of the file from
:download:`here</examples/sysroot.toml>`).  Dummy values have been used for all
required configuration options.

.. literalinclude:: /examples/sysroot.toml

Using this file, run the following command::

    pyqtdeploy-sysroot --options sysroot.toml

You will then see a description of each component's configuration options, the
type of value expected and whether or not a value is required.  You can then
add options to the appropriate sections to meet your requirements.

If your application does not require all of the standard components then simply
remove the corresponding sections from the specification file.  If your
application requires additional components then you need to create appropriate
component plugins and add corresponding sections to the specification file.

At any time you can verify your specification file.  This will check that all
required options have a value and that all components have supported versions
that are mutually compatible.  It will also warn you if you have specified
versions that are untested (but should work).  To do this run::

    pyqtdeploy-sysroot --verify sysroot.toml

To build a native sysroot (i.e. for the host architecture) from a fully
configured specification file, run::

    pyqtdeploy-sysroot sysroot.toml


The :program:`pyqt-demo` Sysroot
--------------------------------

In this section we walk through the sysroot specification file for
:program:`pyqt-demo`, component by component.

OpenSSL
.......

::

    [OpenSSL]
    disabled_targets = ["ios"]
    version = "1.1.1g"

    [OpenSSL.linux]
    install_from_source = false

On iOS we choose to not support SSL from Python and use Qt's SSL support
instead (which will use Apple's Secure Transport).

On Linux we will use the OS supplied OpenSSL libraries.


Python
......

::

    [Python]
    version = "3.7.8"
    install_host_from_source = true

    [Python.win]
    install_host_from_source = false

The Python component plugin handles installation for both host and target
architectures.  For the host we choose to install from source except on Windows
where the registry is searched for the location of an existing installation.
For all target architecures we choose to build Python from source.

:program:`pyqt-demo` is a very simple application that does not need to
dynamically load extension modules.  If this was needed then the
``dynamic_loading`` option would be set to ``true``.


PyQt
....

::

    [PyQt]
    version = "5.15.0"

    [PyQt.android]
    disabled_features = ["PyQt_Desktop_OpenGL", "PyQt_Printer"]
    installed_modules = ["QtCore", "QtGui", "QtNetwork", "QtWidgets",
            "QtAndroidExtras"]

    [PyQt.ios]
    disabled_features = ["PyQt_Desktop_OpenGL", "PyQt_MacOSXOnly",
            "PyQt_MacCocoaViewContainer", "PyQt_Printer", "PyQt_Process",
            "PyQt_NotBootstrapped"]
    installed_modules = ["QtCore", "QtGui", "QtNetwork", "QtWidgets",
            "QtMacExtras"]

    [PyQt.linux]
    installed_modules = ["QtCore", "QtGui", "QtNetwork", "QtWidgets",
            "QtX11Extras"]

    [PyQt.macos]
    installed_modules = ["QtCore", "QtGui", "QtNetwork", "QtWidgets",
            "QtMacExtras"]

    [PyQt.win]
    disabled_features = ["PyQt_Desktop_OpenGL"]
    installed_modules = ["QtCore", "QtGui", "QtNetwork", "QtWidgets",
            "QtWinExtras"]

The two options used to tailor the build of PyQt are ``disabled_features``
and ``installed_modules``.

Unfortunately the list of features that can be disabled is not properly
documented and relate to how Qt is configured.  However how
``disabled_features`` is set in the above will be appropriate for most cases.

The ``installed_modules`` option is used to specify the names of the individual
PyQt extension modules to be installed.  We choose to build only those
extension modules needed by :program:`pyqt-demo`.


PyQt3D
......

::

    [PyQt3D]
    version = "5.15.0"

It is only necessary to specifiy the version to install.


PyQtChart
.........

::

    [PyQtChart]
    version = "5.15.0"

It is only necessary to specifiy the version to install.


PyQtDataVisualization
.....................

::

    [PyQtDataVisualization]
    version = "5.15.0"

It is only necessary to specifiy the version to install.


PyQtPurchasing
..............

::

    [PyQtPurchasing]
    version = "5.15.0"

It is only necessary to specifiy the version to install.


QScintilla
..........

::

    [QScintilla]
    version = "2.11.5"

It is only necessary to specifiy the version to install.


Qt
..

::

    [Qt]
    version = "5.15.0"
    edition = "opensource"
    configure_options = ["-opengl", "desktop", "-no-dbus", "-qt-pcre"]
    skip = ["qtactiveqt", "qtconnectivity", "qtdoc", "qtgamepad", "qtlocation",
            "qtmultimedia", "qtnetworkauth", "qtquickcontrols",
            "qtquickcontrols2", "qtremoteobjects", "qtscript", "qtscxml",
            "qtsensors", "qtserialbus", "qtserialport", "qtspeech", "qtsvg",
            "qttools", "qttranslations", "qtwayland", "qtwebchannel",
            "qtwebengine", "qtwebsockets", "qtwebview", "qtxmlpatterns"]

    [Qt.android]
    install_from_source = false
    ssl = "openssl-linked"

    [Qt.ios]
    install_from_source = false
    ssl = "securetransport"

    [Qt.linux]
    ssl = "openssl-runtime"

    [Qt.macos]
    ssl = "openssl-linked"

    [Qt.win]
    ssl = "openssl-linked"
    static_msvc_runtime = true

We have chosen to install Qt from source except for Android and iOS where we
will use an existing installation.  In the context of the demo this is defined
by the ``--qmake`` option of the ``build-demo.py`` script.

We use the ``configure_options`` and ``skip`` options to tailor the Qt build in
order to reduce the time taken to do the build.

The ``ssl`` option specifies how Qt's SSL support is to be implemented.

On Android we have chosen to link against the shared OpenSSL libraries
installed by the ``OpenSSL`` component plugin which are bundled automaticallly
with the application executable.

On iOS Qt is dynamically linked to the Secure Transport libraries.

On Linux we have chosen to dynamically load the OS supplied OpenSSL libraries
at runtime.

On macOS and Windows we have chosen to link against the static OpenSSL
libraries installed by the ``OpenSSL`` component plugin.

Finally we have specified that (on Windows) we will link to static versions of
the MSVC runtime libraries.


SIP
...

::

    [SIP]
    version = "12.8.1"
    module_name = "PyQt5.sip"

When using SIP v5 and later the version number refers to the ABI implemented by
the :mod:`sip` module and not the version of SIP itself.  Suitable versions of
SIP and PyQt-builder must both be installed for the same Python installation
being used to run :program:`pyqtdeploy`.

If SIP v4 is being used then the version number refers to SIP itself and
:program:`pyqtdeploy` will automatically build and install that version.


zlib
....

::

    [zlib]
    version = "1.2.11"
    install_from_source = false

    [zlib.android]
    version = "1.2.7"

    [zlib.win]
    install_from_source = true
    static_msvc_runtime = true

On all targets, except for Windows, we choose to use the zlib library provided
by the OS.  On Android this is an earlier version.

On Windows we choose to link to static versions of the MSVC runtime libraries.


The Command Line
----------------

The full set of command line options is:

.. option:: -h, --help

    This will display a summary of the command line options.

.. option:: -V, --version

    This specifies that the version number should be displayed on ``stdout``.
    The program will then terminate.

.. option:: --component COMPONENT

    ``COMPONENT`` is the name of the component that will be installed.  It may
    be used more than once to install multiple components.  If the option is
    not specified then all components specified in the TOML specification file
    will be installed.

.. option:: --force

    This causes all components to be installed even if components with the
    required versions have already been installed.

.. option:: --no-clean

    A temporary build directory (called ``build`` in the sysroot) is created in
    order to build the required components.  Normally this is removed
    automatically after all components have been built.  Specifying this option
    leaves the build directory in place to make debugging component plugins
    easier.

.. option:: --options

    This causes the configurable options of each component specified in the
    TOML specification file to be displayed on ``stdout``.  The program will
    then terminate.

.. option:: --python EXECUTABLE

    ``EXECUTABLE`` is the full path name of the host Python interpreter.  It
    overrides any value provided by the sysroot but the version must be
    compatible with that specified in the TOML specification file.

.. option:: --qmake EXECUTABLE

    ``EXECUTABLE`` is the full path name of the host :program:`qmake`.  It
    overrides any value provided by the sysroot but the version must be
    compatible with that specified in the TOML specification file.

.. option:: --source-dir DIR

    ``DIR`` is the name of a directory containing any local copies of source
    archives used to install the components specified in the TOML specification
    file.  It may be specified any number of times and each directory will be
    searched in turn.  If a local copy cannot be found then the component
    plugin will attempt to download it.

.. option:: --sysroots-dir DIR

    ``DIR`` is the name of the directory where the target-specific sysroot
    directory will be created.  A sysroot directory will be called ``sysroot-``
    followed by a target-specific suffix.  If all components are to be
    re-installed then any existing sysroot will first be removed and
    re-created.

.. option:: --target TARGET

    ``TARGET`` is the target architecture.  By default the host architecture is
    used.  On Windows the default is determined by the target architecture of
    the currently configured compiler.

.. option:: --quiet

    This specifies that progress messages should be disabled.

.. option:: --verbose

    This specifies that additional progress messages should be enabled.

.. option:: specification

    ``specification`` is the name of the TOML specification file that defines
    each component to be included in the sysroot and how each is to be
    configured.


Writing a Component Plugin
--------------------------

A component plugin is a Python module that defines a sub-class of
:py:class:`pyqtdeploy.Component`.  The name of the module is the name used in
the TOML specification file.  It doesn't matter what the name of the sub-class
is.

Component plugins (other than those bundled with :program:`pyqtdeploy`) are
expected to be found in the directory containing the TOML specification file.

.. py:module:: pyqtdeploy

.. py:class:: Component

    This is the base class of all component plugins.

    .. py:attribute:: android_abi

        The Android architecture-specific ABI being used.

    .. py:attribute:: android_api

        The integer Android API level being used.

    .. py:attribute:: android_ndk_root

        The path of the root of the Android NDK.

    .. py:attribute:: android_ndk_sysroot

        The path of the Android NDK's sysroot directory.

    .. py:attribute:: android_ndk_version

        The the version number of the Android NDK.

    .. py:attribute:: android_sdk_version

        The version number of the Android SDK.

    .. py:attribute:: android_toolchain_bin

        The path of the Android toolchain's bin directory.

    .. py:attribute:: android_toolchain_cc

        The name of the Android toolchain's C compiler.

    .. py:attribute:: android_toolchain_prefix

        The name of the Android toolchain's prefix.

    .. py:attribute:: apple_sdk

        The Apple SDK being used.

    .. py:attribute:: apple_sdk_version

        The version number of the Apple SDK.

    .. py:attribute:: building_for_target

        This is set to ``True`` by the component plugin to configure building
        (i.e. compiling and linking) for the target (rather than the host)
        architecture.  The default value is ``True``.

    .. py:method:: copy_dir(src, dst, ignore=None)

        A directory is copied, optionally excluding file and sub-directories
        that match a number of glob patterns.  If the destination directory
        already exists then it is first removed.  Any errors are handled
        automatically.

        :param str src: the name of the source directory.
        :param str dst: the name of the destination directory.
        :param list[str] ignore: an optional sequence of glob patterns that
            specify files and sub-directories that should be ignored.

    .. py:method:: copy_file(src, dst, macros=None)

        A file is copied while expanding and optional dict of macros.  Any
        errors are handled automatically.

        :param str src: the name of the source file.
        :param str dst: the name of the destination file.
        :param dict macros: the dict of name/value pairs.

    .. py:method:: create_dir(name, empty=False)

        A new directory is created if it does not already exist.  If it does
        already exist then it is optionally emptied.  Any errors are handled
        automatically.

        :param str name: the name of the directory.
        :param bool empty: ``True`` if an existing directory should be emptied.

    .. py:method:: create_file(name)

        A new text file is created and its file object returned.  Any errors
        are handled automatically.

        :param str name: the name of the file.
        :return: the file object of the created file.

    .. py:method:: delete_dir(name)

        A directory and any contents are deleted.  Any errors are handled
        automatically.

        :param str name: the name of the directory.

    .. py:method:: error(message, detail='')

        An error message is displayed to the user and the program immediately
        terminates.

        :param str message: the message.
        :param str detail: additional detail displayed if the
            :option:`--verbose <pyqtdeploy-sysroot --verbose>` option was
            specified.

    .. py:method:: find_exe(name, required=True)

        The absolute path name of an executable located on :envvar:`PATH` is
        returned.

        :param str name: the generic executable name.
        :param bool required: ``True`` if the executable is required and it is
            an error if it could not be found.
        :return: the absolute path name of the executable.

    .. py:method:: get_archive(name):

        The pathname of a local copy of the component's source archive is
        returned.  The directories specified by the
        :option:`--source-dir <pyqtdeploy-sysroot --source-dir>` option are
        searched first.  If the archive is not found then it is downloaded if
        the component supports it.

        :return: the pathname of the archive.

    .. py:method:: get_archive_name():
        :abstractmethod:

        This must be re-implemented to return the version-specific name of the
        component's source archive.

        :return: the name of the archive.

    .. py:method:: get_archive_urls():

        This is re-implemented to return a sequence of URLs (excluding the
        source archive name) from which the component's source archive may be
        downloaded from.

        :return: the sequence of URLs.

    .. py:method:: get_component(name, required=True)

        The :py:class:`~pyqtdeploy.Component` instance for a component is
        returned.

        :param str name: the name of the component.
        :param bool required: ``True`` if the component is required and it is
            an error if it was not specified.
        :return: the component instance.

    .. py:method:: get_file(name)

        The absolute path name of a file or directory in a directory specified
        by a :option:`--source-dir <pyqtdeploy-sysroot --source-dir>` option is
        returned.

        :param str name: the name of the file or directory.
        :return: the absolute path name of the file or directory or ``None`` if
            it wasn't found.

    .. py:method:: get_options()

        A sequence of :py:class:`~pyqtdeploy.ComponentOption` instances
        describing the component's configurable options is returned.

        :return: the sequence of option instances.

    .. py:method:: get_pypi_urls(pypi_project):

        This can be called from a re-implementation of
        :py:meth:`~pyqtdeploy.Component.get_archive_urls` to return a sequence
        of URLs (excluding the source archive name) from which the component's
        source archive may be downloaded from a PyPI project.

        :param str pypi_project: the name of the PyPI project.
        :return: the sequence of URLs.

    .. py:method:: get_python_install_path(major, minor)

        The name of the directory containing the root of a Python installation
        on Windows is returned.  It must only be called by a Windows host.

        :param int major: the major version number.
        :param int minor: the major version number.
        :return: the absolute path of the installation directory.

    .. py:method:: get_version_from_file(identifier, filename)

        A file is read and a (stripped) line containing an identifier
        (typically a pre-processor macro defining a version number) is
        returned.  it is an error if the identifier could not be found.

        :param str identifer: the identifier to find.
        :param str filename: the name of the file to read.
        :return: the stripped line containing the identifier.

    .. py:attribute:: host_dir

        The name of the directory where components built for the host
        architecture should be installed.

    .. py:method:: host_exe(name)

        A generic executable name is converted to a host-specific version.

        :param str name: the generic name.
        :return: the host-specific name.

    .. py:attribute:: host_make

        The name of the host :program:`make` executable.

    .. py:attribute:: host_platform_name

        The name of the host platform.

    .. py:attribute:: host_python

        The name of the host :program:`python` executable.  This is only
        implemented by the ``Python`` component plugin.

    .. py:attribute:: host_qmake

        The name of the host :program:`qmake` executable.  This is only
        implemented by the ``Qt`` component plugin.

    .. py:attribute:: host_sip

        The name of the host :program:`sip` executable.  This is only
        implemented by the ``SIP`` component plugin.

    .. py:method:: install()
        :abstractmethod:

        This must be re-implemented to install the component.

    .. py:attribute:: must_install_from_source

        This is set by the component if it must be installed from a source
        archive.

    .. py:method:: open_file(name)

        An existing text file is opened and its file object returned.  Any
        errors are handled automatically.

        :param str name: the name of the file.
        :return: the file object of the opened file.

    .. py:method:: parse_version_number(version_nr)
        :staticmethod:

        A version number is converted to a :class:`~pyqtdeploy.VersionNumber`
        instance.  It may be a string, an encoded integer or a tuple.

        :param name: the version number to parse.
        :type name: str, int, or tuple
        :return: the version number.

    .. py:method:: patch_file(name, patcher)

        Patch a file.

        :param str name: the name of the file to patch
        :param callable patcher: invoked for each line of the file and passed
            the line and a file object to which the (possibly) modified line
            should be written to.

    .. py:attribute:: preinstalls

        The list of components that this component is dependent on.

    .. py:method:: progress(message)

        A progress message is displayed to the user.  It will be suppressed if
        the :option:`--quiet <pyqtdeploy-sysroot --quiet>` option was
        specified.

        :param str message: the message.

    .. py:attribute:: provides

        The dict of parts, keyed by the name of the part, provided by this
        component.

    .. py:method:: run(*args, capture=False)

        An external command is run.  The command's stdout can be optionally
        captured.

        :param \*args: the name of the command and its arguments.
        :param bool capture: ``True`` if the command's stdout should be
            captured and returned.
        :return: the stdout of the command if requested, otherwise ``None``.

    .. py:method:: sdk_configure(platform_name)

        This should be implemented to perform any SDK-specific configuration
        prior to installing the component.

        :param str platform_name: the target platform name.

    .. py:method:: sdk_deconfigure(platform_name)

        This should be implemented to remove any SDK-specific configuration
        after to installing the component.

        :param str platform_name: the target platform name.

    .. py:attribute:: sysroot_dir

        The full pathname of the system root directory.

    .. py:attribute:: target_arch_name

        The name of the target architecture.

    .. py:attribute:: target_include_dir

        The name of the directory where header files built for the target
        architecture should be installed.

    .. py:attribute:: target_lib_dir

        The name of the directory where libraries built for the target
        architecture should be installed.

    .. py:attribute:: target_platform_name

        The name of the target platform.

    .. py:attribute:: target_py_include_dir

        The pathname of the directory containing the target Python header
        files.  This is only implemented by the ``Python`` component plugin.

    .. py:attribute:: target_py_lib

        The name of the target Python library.  This is only implemented by the
        ``Python`` component plugin.

    .. py:attribute:: target_sip_dir

        The pathname of the directory containing the target ``.sip`` files.
        This is only implemented by the ``SIP`` component plugin.

    .. py:attribute:: target_sitepackages_dir

        The pathname of the target Python ``site-packages`` directory.  This is
        only implemented by the ``Python`` component plugin.

    .. py:attribute:: target_src_dir

        The name of the directory where source files can be found.  Note that
        these are sources left by components for the use of other components
        and not the sources used to build a component.

    .. py:method:: unpack_archive(archive, chdir=True)

        A source archive is unpacked in the current directory and the name of
        the archive directory (not its pathname) is returned.

        :param str archive: the pathname of the source archive.
        :param bool chdir: ``True`` if the current directory is changed to be
            the archive directory.
        :return: the name of the archive directory.

    .. py:method:: unsupported(detail=None)

        Issue an error message that the version of the component is
        unsupported.

        :param str detail: additional detail to append to the message.

    .. py:method:: untested()

        Issue a warning message that the version of the component is untested.

    .. py:method:: verify()
        :abstractmethod:

        This must be re-implemented to verify the component.  A component
        will always be verified even if it does not get installed.  The plugin
        should check that everything is available (e.g. other components,
        external tools) using the specified versions for a successful
        installation.

    .. py:method:: verbose(message)

        A verbose progress message is displayed to the user.  It will be
        suppressed unless the
        :option:`--verbose <pyqtdeploy-sysroot --verbose>` option was
        specified.

        :param str message: the message.

    .. py:attribute:: verbose_enabled

        This is set if the :option:`--verbose <pyqtdeploy-sysroot --verbose>`
        option was specified.

    .. py:method:: warning(message)

        A warning progress message is displayed to the user.

        :param str message: the message.


.. py:class:: ComponentOption(name, type=str, required=False, default=None, values=None, help='')

    This class implements an option used to configure the component.  An option
    can be specified as an attribute of the component's object in the sysroot
    specification file.  An instance of the component plugin will contain an
    attribute for each option whose value is that specified in the sysroot
    specification file (or an appropriate default if it was omitted).

    :param str name: the name of the option.
    :param type: the type of a value of the option.
    :type type: bool, int, list or str
    :param bool required: ``True`` if a value for the option is required.
    :param default: the default value of the option.
    :param values: the possible values of the option.
    :param str help: the help text displayed by the
        :option:`--options <pyqtdeploy-sysroot --options>` option of
        :program:`pyqtdeploy-sysroot`.


.. py:class:: VersionNumber

    This class encapsulates a version number in the form ``M[.m[.p]][suffix]``
    where ``M`` is an integer major version number, ``m`` is an optional
    integer minor version number, ``p`` is an optional integer patch version
    number and ``suffix`` is an optional string suffix.

    Instances may be compared with other instances, integers or tuples to
    determine equality or relative chronology.  An integer is interpreted as a
    major version number.  A tuple may have between one and four elements and
    the number of elements determines the precision of the comparison.  For
    example, if a 2-tuple is specified then only the major and minor version
    numbers are considered and the patch version numbers and suffixes are
    ignored.

    .. py:method:: __str__()

        Convert the version number to a user friendly representation.

        :return: the version number as a string.

    .. py:attribute:: major

        The major version number.

    .. py:attribute:: minor

        The minor version number.

    .. py:attribute:: patch

        The patch version number.

    .. py:attribute:: suffix

        The suffix.


Defining Component Parts
........................

The following classes are used to define the different types of part that a
component can provide.

A part is provided by a range of versions of the component.  The optional
``min_version`` is the minimum version of the component that provides the part.
The optional ``max_version`` is the maximum version of the component that
provides the part.  The optional ``version`` can be used to specify an exact
version of the component that provides the part and is the equivalent of
specifying the same value for both ``min_version`` and ``max_version``.  A
version can be specified as either an integer major version number, a 2-tuple
of major and minor version numbers or a 3-tuple of major, minor and patch
version numbers.

Several attributes of different parts are described as sequences of *scoped
values*.  A scoped value is a *scope* and a *value* separated by ``#``.  A
scope defines one or more targets.  If the current target is defined by the
scope then the value is used, otherwise it is ignored.  A scope may be one or
more architecture or platform names separated by ``|`` meaning that the scope
defines all the the specified architectures or platforms.  An individual name
may be preceded by ``!`` which excludes the name from the scope.  For example
``ios|macos`` defines the value for the iOS and macOS platforms and ``!win-32``
defines the value for all targets except for 32-bit Windows.

Some parts may be dependent on other parts, possibly parts provided by
different components.  A dependency may be specified as a component name and a
part name separated by ``:``.  If the component name is omitted then the
current component is assumed.


.. py:class:: ComponentLibrary(min_version=None, version=None, max_version=None, target='', defines=None, libs=None, includepath=None, bundle_shared_libs=False)

    This class encapsulates a library that is usually a dependency of an
    extension module.

    :param min_version: the minimum version of the component providing the
        part.
    :type min_version: int, 2-tuple or 3-tuple
    :param version: the exact version of the component providing the part.
    :type version: int, 2-tuple or 3-tuple
    :param max_version: the maximum version of the component providing the
        part.
    :type max_version: int, 2-tuple or 3-tuple
    :param str target: the target platform for which the part is provided.
    :param sequence defines: the scoped pre-processor macros to be added to the
        ``DEFINES`` :program:`qmake` variable.
    :param sequence libs: the scoped library names to be added to the ``LIBS``
        :program:`qmake` variable.
    :param sequence includepath: the scoped directory names to be added to the
        ``INCLUDEPATH`` :program:`qmake` variable.
    :param bool bundle_shared_libs: ``True`` if the libraries are shared and
        need to be bundled with the application.  Current this only applies to
        Android targets.


.. py:class:: DataFile(name, min_version=None, version=None, max_version=None, target='')

    This class encapsulates a data file.

    :param str name: the name of the file.
    :param min_version: the minimum version of the component providing the
        part.
    :type min_version: int, 2-tuple or 3-tuple
    :param version: the exact version of the component providing the part.
    :type version: int, 2-tuple or 3-tuple
    :param max_version: the maximum version of the component providing the
        part.
    :type max_version: int, 2-tuple or 3-tuple
    :param str target: the target platform for which the part is provided.


.. py:class:: ExtensionModule(min_version=None, version=None, max_version=None, target='', min_android_api=None, deps=(), defines=None, libs=None, includepath=None, source=None, qmake_config=None, qmake_cpp11=False, qmake_qt=None)

    This class encapsulates an extension module.

    :param min_version: the minimum version of the component providing the
        part.
    :type min_version: int, 2-tuple or 3-tuple
    :param version: the exact version of the component providing the part.
    :type version: int, 2-tuple or 3-tuple
    :param max_version: the maximum version of the component providing the
        part.
    :type max_version: int, 2-tuple or 3-tuple
    :param str target: the target platform for which the part is provided.
    :param int min_android_api: the minimum Android API level required.
    :param sequence deps: the scoped names of other parts that this part is
        dependent on.
    :param sequence defines: the scoped pre-processor macros to be added to the
        ``DEFINES`` :program:`qmake` variable.
    :param sequence libs: the scoped library names to be added to the ``LIBS``
        :program:`qmake` variable.
    :param sequence includepath: the scoped directory names to be added to the
        ``INCLUDEPATH`` :program:`qmake` variable.
    :param source: the name of the source file(s) of the extension module.
    :type source: str or sequence
    :param qmake_config: the value(s) to be added to the ``CONFIG``
        :program:`qmake` variable.
    :type qmake_config: str or sequence
    :param bool qmake_cpp11: ``True`` if the extension module requires support
        for C++11.
    :param qmake_qt: the value(s) to be added to the ``QT`` :program:`qmake`
        variable.
    :type qmake_qt: str or sequence


.. py:class:: PythonModule(min_version=None, version=None, max_version=None, target='', min_android_api=None, deps=())

    This class encapsulates a Python module (i.e. a single ``.py`` file).

    :param min_version: the minimum version of the component providing the
        part.
    :type min_version: int, 2-tuple or 3-tuple
    :param version: the exact version of the component providing the part.
    :type version: int, 2-tuple or 3-tuple
    :param max_version: the maximum version of the component providing the
        part.
    :type max_version: int, 2-tuple or 3-tuple
    :param str target: the target platform for which the part is provided.
    :param int min_android_api: the minimum Android API level required.
    :param sequence deps: the scoped names of other parts that this part is
        dependent on.


.. py:class:: PythonPackage(min_version=None, version=None, max_version=None, target='', min_android_api=None, deps=(), exclusions=())

    This class encapsulates a Python package (i.e. a directory containing an
    ``__init__.py`` file and other ``.py`` files).

    :param min_version: the minimum version of the component providing the
        part.
    :type min_version: int, 2-tuple or 3-tuple
    :param version: the exact version of the component providing the part.
    :type version: int, 2-tuple or 3-tuple
    :param max_version: the maximum version of the component providing the
        part.
    :type max_version: int, 2-tuple or 3-tuple
    :param str target: the target platform for which the part is provided.
    :param int min_android_api: the minimum Android API level required.
    :param sequence deps: the scoped names of other parts that this part is
        dependent on.
    :param sequence exclusions: the names of any files or directories, relative
        to the package, that should be excluded.
