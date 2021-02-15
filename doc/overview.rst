An Overview of the Deployment Process
=====================================

The purpose of :program:`pyqtdeploy` is to convert a Python application, the
Python interpreter, the Python standard library, Python C extension modules,
third-party Python packages and third-party extension modules to a single,
target-specific executable.  Depending on the target the executable may need to
be packaged in some way to be truly deployable.  For example, Android
applications need to be signed and packaged as a ``.apk`` file.  Any such
packaging is outside the scope of :program:`pyqtdeploy`.

While :program:`pyqtdeploy` allows you to create a single executable you are
free to keep components external to the executable if required.

:program:`pyqtdeploy` supports the following target architectures:

- android-32
- android-64
- ios-64
- linux-64
- macos-64
- win-32
- win-64.

The full architecture name consists of the platform and the word size separated
by a ``-``.  Note that not all platform/word size combinations are supported.

:program:`pyqtdeploy` uses the following parts of Qt:

- :program:`qmake` is the Qt build system that supports cross-compilation to
  multiple targets.

- :program:`rcc` is a utility that converts arbitrary files to C++ data
  structures that implement an embedded filesystem that can be linked as part
  of an application.

- The :program:`QtCore` library implements file access APIs that recognise file
  and directory names that refer to the contents of the embedded filesystem
  created with :program:`rcc`.  :program:`pyqtdeploy` implements import hooks
  that use :program:`QtCore` so that frozen Python modules can be imported from
  the embedded filesystem just as if they were being imported from an ordinary
  filesystem.

Note that :program:`pyqtdeploy` generated code does not itself use PyQt.
:program:`pyqtdeploy` can be used to deploy non-PyQt applications, including
simple command line scripts.  However, as every deployed application is linked
with the :program:`QtCore` library, you should make sure that your
application's license is compatible with the license of the version of Qt that
you are using.

The steps required to develop a deployable application are as follows:

- Develop and test the application as normal using a native Python
  installation containing the required third-party components.

- Create a sysroot specification file, typically called :file:`sysroot.toml`,
  that identifies the components (and their exact version numbers) that are
  required.  See :ref:`ref-building-a-sysroot` to learn how to do this.
  :program:`pyqtdeploy-sysroot` can be used to verify the specification file,
  i.e. that all component versions are mutually compatible.  At this stage it
  is not necessary to actually build the sysroot.  It is common practice to use
  the same sysroot for several applications.

- Create a project file for the application that identifies the application's
  source code and all the Python packages and extension modules it uses.  See
  :ref:`ref-creating-a-project` to learn how to use :program:`pyqtdeploy` to do
  this.

- Use :program:`pyqtdeploy-sysroot` to build the target-specific sysroot from
  its specification file if it has not already been done.

- Freeze the Python modules and generate a :program:`qmake` ``.pro`` file in a
  target-specific build directory.  The ``.pro`` file will reference all of the
  required components in the associated sysroot.  Run :program:`qmake` and then
  :program:`make` to create the application executable.  See
  :ref:`ref-building-an-application` to learn how to use
  :program:`pyqtdeploy-build` to do this.
