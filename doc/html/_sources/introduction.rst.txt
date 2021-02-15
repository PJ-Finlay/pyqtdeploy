Introduction
============

:program:`pyqtdeploy` is a tool that, in conjunction with other tools provided
with Qt, enables the deployment of PyQt applications written with Python v3.5
or later.  It supports deployment to desktop platforms (Linux, Windows and
macOS) and to mobile platforms (iOS and Android).

Normally you would create statically compiled versions of the Python
interpreter library and any third party extension modules (including PyQt).
This way your application has no external dependencies.  However there is
nothing to stop you using shared versions of any of these components in order
to reduce the size of the application, but at the cost of increasing the
complexity of the deployment.

:program:`pyqtdeploy` itself requires PyQt5 and Python v3.5 or later.

:program:`pyqtdeploy` works by taking the individual modules of a PyQt
application, freezing them, and then placing them in a Qt resource file that is
converted to C++ code by Qt's :program:`rcc` tool.  Python's standard library
is handled in the same way.

:program:`pyqtdeploy` generates a simple C++ wrapper around the Python
interpreter library that uses the Python import mechanism to enable access to
the embedded frozen modules in a similar way that Python supports the packaging
of modules in zip files.

Finally :program:`pyqtdeploy` generates a target-specific Qt ``.pro`` file that
describes all the generated C++ code.  From this Qt's :program:`qmake` tool is
used to generate a ``Makefile`` which will then generate a single executable.
Further Qt and/or platform specific tools can then be used to convert the
executable to a target-specific deployable package.

When run :program:`pyqtdeploy` presents a GUI that allows all the separate
components to be specified.  This information is stored in a
:program:`pyqtdeploy` project file.

:program:`pyqtdeploy` does not (yet) perform auto-discovery of Python standard
library modules or third party modules to be included with the application.
You must specify these yourself.  However it does understand the
inter-dependencies within the standard library and external modules, so you
only need to specify those packages that your application explicitly imports.

A companion program :program:`pyqtdeploy-sysroot` is used to create a system
root (*sysroot*) directory containing target-specific installations of
components (e.g. Python itself and PyQt) that are to be linked with the
application.

Another companion program :program:`pyqtdeploy-build` is then run from the
command line (or a shell script or batch file) to generate the application's
C++ code from a project file.

:program:`pyqtdeploy` does not itself generate a final distribution package,
i.e. one that is handled by a target platform's package management system.
This is left to the target platform's standard packaging tools.  For desktop
targets the `fman Build System <https://build-system.fman.io>`__ is an
alternative solution that includes support for ``.exe`` files (for Windows),
``.dmg`` files (for macOS) and ``.deb`` and ``.rpm`` files (for Linux).

.. note::

    Creating a single executable (particularly one with no external
    dependencies) from a complex Python application (particularly one that uses
    external C extension modules) is not a simple task.  It requires experience
    of C code, compilers, build systems and the ability to debug associated
    problems.  You have been warned!


Differences from Version 2
--------------------------

There have been a number of changes to :program:`pyqtdeploy` since v2:

- Project files created for v2 are automatically updated to the latest version.
  v3 project files have a ``.pdt`` extension.

- Python versions earlier than v3.5 (including v2) are no longer supported.
  Note that SIP v5 will be support in :program:`pyqtdeploy` v3.1 and Python
  v3.8 and later will be supported in :program:`pyqtdeploy` v3.2.

- PyQt4 is no longer supported.

- The use of a sysroot directory to contain the target-specific components to
  be linked with the application is no longer optional.

- The file used to specify the contents of a sysroot is now in `TOML
  <https://github.com/toml-lang/toml>`__ format rather than JSON.

- The API provided to write component plugins has changed requiring plugins to
  be rewritten.

- All component plugins included with :program:`pyqtdeploy` will download their
  source packages automatically when required.

- The :program:`pyqtdeploy` GUI has been greatly simplified.


Author
------

:program:`pyqtdeploy` is copyright (c) Riverbank Computing Limited.  Its
homepage is https://www.riverbankcomputing.com/software/pyqtdeploy/.

Support may be obtained from the PyQt mailing list at
https://www.riverbankcomputing.com/mailman/listinfo/pyqt/.


License
-------

:program:`pyqtdeploy` is released under the BSD license.


Installation
------------

:program:`pyqtdeploy` can be downloaded and installed from
`PyPi <https://pypi.python.org/pypi/pyqtdeploy/>`_::

    pip install pyqtdeploy
