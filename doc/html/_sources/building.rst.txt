.. _ref-building-an-application:

.. program:: pyqtdeploy-build

Building the Application
========================

:program:`pyqtdeploy-build` uses the project file created by
:program:`pyqtdeploy` to generate the target-specific source code, including
the :program:`qmake` ``.pro`` files, needed to create the application.  The
simplest invocation is::

    pyqtdeploy-build pyqt-demo.pdt

The next step in the full build process would be to change to the build
directory and run :program:`qmake`.  The final step is target-specific.  For
Android, Linux, macOS and Windows targets it is only necessary to run
:program:`make` (or :program:`nmake` in the case of Windows).  (Although for an
Android target using versions of Qt prior to v5.14 it is also necessary to run
Qt's :program:`androiddeployqt` utility.)  For an iOS target :program:`qmake`
generates an Xcode project file.  Xcode is then used to perform the final
build.

The demo's :program:`build-demo.py` script takes care of (almost) all of this
process automatically.


The Command Line
----------------

The full set of command line options is:

.. option:: -h, --help

    This will display a summary of the command line options.

.. option:: -V, --version

    This specifies that the version number should be displayed on ``stdout``.
    The program will then terminate.

.. option:: --build-dir DIR

    ``DIR`` is the name of the directory where all the application source code
    will be placed.  The default value is ``build-`` followed by a
    target-specific suffix.

.. option:: --no-clean

    Normally the build directory is deleted and re-created before starting a
    new build.  Specifying this option leaves any existing build directory as
    it is before starting a new build.

.. option:: --opt LEVEL

    ``LEVEL`` is the level of optimisation performed when freezing Python
    source files:

    0 - no optimisation is done

    1 - ``assert`` statements are removed

    2 - ``assert`` statements and docstrings are removed.

    The default is ``2``.

.. option:: --python EXECUTABLE

    ``EXECUTABLE`` is the full path name of the host Python interpreter.  It
    overrides any value provided by the sysroot but the version must be
    compatible with that specified in the :file:`sysroot.toml` file.

.. option:: --qmake EXECUTABLE

    ``EXECUTABLE`` is the full path name of the host :program:`qmake`.  It
    overrides any value provided by the sysroot but the version must be
    compatible with that specified in the :file:`sysroot.toml` file.

.. option:: --resources NUMBER

    ``NUMBER`` is the number of Qt ``.qrc`` resource files that are generated.
    On Windows, MSVC may not be able to cope with very large resource files and
    complains of a lack of heap space.  If you run into this problem then try
    increasing the the number of resource files generated.

.. option:: --target TARGET

    ``TARGET`` is the target architecture.  By default the host architecture is
    used.  On Windows the default is determined by the target architecture of
    the currently configured compiler.

.. option:: --quiet

    This specifies that progress messages should be disabled.

.. option:: --verbose

    This specifies that additional progress messages should be enabled.

.. option:: project

    ``project`` is the name of the project file created by
    :program:`pyqtdeploy`.
