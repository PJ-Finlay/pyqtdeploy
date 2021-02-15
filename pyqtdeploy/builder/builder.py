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


import csv
import glob
import os
import shlex
import shutil
import tempfile

from ..file_utilities import create_file, open_file
from ..parts import (ComponentLibrary, DataFile, ExtensionModule, Part,
        PythonModule, PythonPackage)
from ..project import Project
from ..platforms import Architecture, Platform
from ..sysroot import Sysroot
from ..user_exception import UserException
from ..version import PYQTDEPLOY_HEXVERSION
from ..version_number import VersionNumber


class Builder:
    """ The builder for a project. """

    def __init__(self, project_name, target_arch_name, message_handler, python,
            qmake):
        """ Initialise the builder for a project. """

        self._message_handler = message_handler

        self._project = Project.load(project_name)
        self._host = Architecture.architecture()
        self._target = Architecture.architecture(target_arch_name)

        self._sysroot = Sysroot(self._project.sysroot_specification,
                self._host, self._target, self._project.absolute_sysroots_dir,
                message_handler=self._message_handler, python=python,
                qmake=qmake)

    def build(self, opt, nr_resources, clean, build_dir):
        """ Build the project in a given directory.  Raise a UserException if
        there is an error.
        """

        project = self._project

        # Verify the sysroot.
        self._sysroot.verify()

        python = self._sysroot.get_component('Python')

        # Check the sysroot directory exists.
        if not os.path.isdir(self._sysroot.sysroot_dir):
            raise UserException(
                    "the sysroot directory '{0}' does not exist".format(
                            self._sysroot.sysroot_dir))

        # Get all the parts provided by the sysroot.
        available_parts = {}
        for component in self._sysroot.components:
            available_parts.update(component.parts)

        # Get the required parts.
        parts = {}

        # Always include the core Python modules and their dependencies.
        for part_name, part in python.parts.items():
            if isinstance(part, (PythonModule, PythonPackage)) and part.core:
                self._add_project_part(part_name, parts, available_parts)

        for part_name in project.parts:
            self._add_project_part(part_name, parts, available_parts)

        # Determine the application name.
        if project.application_name:
            application_name = project.application_name
        elif project.application_script:
            application_name = os.path.basename(project.application_script).split('.', maxsplit=1)[0]
        elif project.application_package.name:
            application_name = os.path.basename(project.application_package.name)
        else:
            application_name = os.path.basename(project.name).split('.', maxsplit=1)[0]

        # Check there is an entry point or a script.
        if project.application_script == '':
            if project.application_entry_point == '':
                raise UserException("either the application script name or "
                        "the entry point must be specified")
            elif len(project.application_entry_point.split(':')) != 2:
                raise UserException("an entry point must be a module name and "
                        "a callable separated by a colon")
        elif project.application_entry_point != '':
            raise UserException("either the application script name or the "
                    "entry point must be specified but not both")

        # Set the name of the build directory.
        if not build_dir:
            build_dir = 'build-' + self._target.name

        self._build_dir = os.path.abspath(build_dir)

        # Remove any build directory if required.
        if clean:
            self._sysroot.verbose("cleaning {0}".format(self._build_dir))
            shutil.rmtree(self._build_dir, ignore_errors=True)

        # Now start the build.
        self._sysroot.create_dir(self._build_dir)

        # Create the job file and writer.
        job_dir = tempfile.TemporaryDirectory()
        job_filename = os.path.join(job_dir.name, 'jobs.csv')
        job_file = open(job_filename, 'w', newline='')
        job_writer = csv.writer(job_file)

        # Freeze the bootstrap.  Note that from Python v3.5 the modified part
        # is in _bootstrap_external.py and _bootstrap.py is unchanged from the
        # original source.  We continue to use a local copy of _bootstrap.py
        # as it still needs to be frozen and we don't want to depend on an
        # external source.
        self._freeze_bootstrap('bootstrap', self._build_dir, job_writer,
                python)
        self._freeze_bootstrap('bootstrap_external', self._build_dir,
                job_writer, python)

        # Freeze any main application script.
        if project.application_script != '':
            self._freeze(job_writer, project.application_script,
                    os.path.join(self._build_dir, 'frozen_main.h'),
                    project.project_path(project.application_script),
                    'pyqtdeploy_main', as_c=True)

        # Create the pyqtdeploy module version file.
        with create_file(os.path.join(self._build_dir, 'pyqtdeploy_version.h')) as f:
            f.write(
                    '#define PYQTDEPLOY_HEXVERSION %s\n' % hex(
                            PYQTDEPLOY_HEXVERSION))

        # Generate the application resources.
        resource_names = self._generate_resources(parts, job_writer,
                nr_resources)

        # Write the .pro file.
        self._write_qmake(application_name, parts, job_writer, opt,
                resource_names, python)

        # Run the freeze jobs.
        job_file.close()

        self._run_freeze(python, job_filename, opt)

    def _add_bundled_shared_libs(self, libs, bundled_shared_libs):
        """ Add the shared library files to be bundled with the application.
        """

        lib_dir = self._sysroot.target_lib_dir
        lib_so = []

        for value in libs:
            if value.startswith('-L'):
                lib_dir = value[2:]

                if not os.path.isabs(lib_dir):
                    lib_dir = os.path.join(self._sysroot.sysroot_dir, lib_dir)
            elif value.startswith('-l'):
                lib_so.append('lib' + value[2:] + '.so')

        if lib_dir != '':
            for lib in lib_so:
                lib_path = os.path.realpath(os.path.join(lib_dir, lib))

                if not os.path.isfile(lib_path):
                    raise UserException(
                            "bundled shared library '{0}' does not exist".format(lib_path))

                bundled_shared_libs.add(lib_path)

    def _add_project_part(self, part_name, parts, available_parts):
        """ Make sure a part is in the dict of all parts. """

        # See if it has already been done.
        if part_name in parts:
            return

        # Make sure any parent parts exist.
        if '.' in part_name:
            # Find the scoped name of the parent part.
            unscoped_name = Part.get_unscoped_name(part_name)
            unscoped_parent_name = '.'.join(unscoped_name.split('.')[:-1])

            for component in self._sysroot.components:
                parent_name = Part.get_name(component.name,
                        unscoped_parent_name)

                if parent_name in component.parts:
                    break
            else:
                # Ignore parts whose parent is not provided.
                return

            self._add_project_part(parent_name, parts, available_parts)

        # Ignore parts that aren't provided by the sysroot (we assume the
        # application will handle that).
        part = available_parts.get(part_name)
        if part is None:
            return

        # For Android check the API level.
        if self._target.platform.name == 'android' and part.min_android_api is not None and part.min_android_api > self._target.platform.android_api:
            return

        parts[part_name] = part

        # Now handle the dependencies.
        for dep in part.deps:
            self._add_project_part(dep, parts, available_parts)

        for dep in part.hidden_deps:
            self._add_project_part(dep, parts, available_parts)

    def _add_values(self, used_values, values, part, is_filename=True):
        """ Parse a sequence of values and add them to a set of used values.
        The values are optionally treated as filenames where they are converted
        to absolute filenames with UNIX separators.
        """

        # Handle the trivial case.
        if values is None:
            return

        component = self._sysroot.get_component(part.component_name)

        for value in values:
            # Convert potential filenames.
            if is_filename:
                value = component.get_target_src_path(value)
            elif value.startswith('-L'):
                value = '-L' + component.get_target_src_path(value[2:])

            used_values.add(value)

    @staticmethod
    def _freeze(job_writer, label, out_file, in_file, name, as_c=False):
        """ Freeze a Python source file to a C header file or a data file. """

        if as_c:
            conversion = 'C'
        else:
            name = ':/' + name
            conversion = 'data'

        job_writer.writerow([label, out_file, in_file, name, conversion])

    def _freeze_bootstrap(self, name, build_dir, job_writer, python):
        """ Freeze a version dependent bootstrap script. """

        # Find the bootstrap script appropriate for this version of Python.
        bootstrap_dir = self._get_lib_path(name)
        bootstrap = None
        bootstrap_version = None

        for fn in os.listdir(bootstrap_dir):
            version = fn.split('-')[-1]
            if version.endswith('.py'):
                version = version[:-3]

            try:
                version = VersionNumber.parse_version_number(version)
            except UserException:
                continue

            if version > python.version:
                # This is for a later version so we can ignore it.
                continue

            if bootstrap is None or bootstrap_version < version:
                # This is a better candidate than we have so far.
                bootstrap = fn
                bootstrap_version = version

        assert bootstrap is not None

        bootstrap_path = os.path.join(bootstrap_dir, bootstrap)
        self._freeze(job_writer, bootstrap,
                os.path.join(build_dir, 'frozen_' + name + '.h'),
                bootstrap_path, 'pyqtdeploy_' + name, as_c=True)

    def _generate_resources(self, parts, job_writer, nr_resources):
        """ Generate the application resource files and return the names of
        the files relatve to the build directory.
        """

        project = self._project

        resources_contents = []

        # Handle any application package.
        if project.application_package.name is not None:
            self._write_python_modules(project.application_package.parts,
                    resources_contents, job_writer,
                    part_root_dir=os.path.dirname(
                            project.project_path(
                                    project.application_package.name)))

        # Handle the standard library and other packages.
        self._write_python_modules(parts, resources_contents, job_writer)

        # Write the .qrc files.
        if nr_resources == 1:
            resource_names = [self._write_resource(resources_contents)]
        else:
            resource_names = []

            nr_files = len(resources_contents)

            if nr_resources > nr_files:
                nr_resources = nr_files

            per_resource = (nr_files + nr_resources - 1) // nr_resources
            start = 0

            for r in range(nr_resources):
                end = start + per_resource
                if end > nr_files:
                    end = nr_files

                resource_names.append(
                        self._write_resource(resources_contents[start:end], r))
                start += per_resource

        return resource_names

    def _get_abs_resource_path(self, rel_resource_path):
        """ Convert a relative path of a resource file to an absolute path and
        make sure the directory that will contain the resource file exists.
        """

        abs_resource_path = os.path.join(self._build_dir, 'resources',
                rel_resource_path)

        os.makedirs(os.path.dirname(abs_resource_path), exist_ok=True)

        return abs_resource_path

    @staticmethod
    def _get_lib_path(name):
        """ Get the pathname of a file or directory in the 'lib' sub-directory.
        """

        return os.path.join(os.path.dirname(__file__), 'lib', name)

    def _run_freeze(self, python, job_filename, opt):
        """ Run the accumlated freeze jobs. """

        args = [python.host_python]

        if opt == 2:
            args.append('-OO')
        elif opt == 1:
            args.append('-O')

        args.append(self._get_lib_path('freeze.py'))
        args.append(job_filename)

        self._host.platform.run(*args, message_handler=self._message_handler)

    def _write_inittab(self, f, inittab, c_inittab):
        """ Write the Python version specific extension module inittab. """

        # We want reproduceable output.
        sorted_inittab = sorted(inittab)

        for name in sorted_inittab:
            base_name = name.split('.')[-1]

            f.write('extern "C" PyObject *PyInit_%s(void);\n' % (base_name))

        f.write('''
static struct _inittab %s[] = {
''' % c_inittab)

        for name in sorted_inittab:
            base_name = name.split('.')[-1]

            f.write('    {"%s", PyInit_%s},\n' % (name, base_name))

        f.write('''    {NULL, NULL}
};
''')

    def _write_main(self, inittab, defines):
        """ Create the application specific pyqtdeploy_main.cpp file. """

        project = self._project

        f = create_file(os.path.join(self._build_dir, 'pyqtdeploy_main.cpp'))

        # Compilation fails when using GCC 5 when both Py_BUILD_CORE and
        # HAVE_STD_ATOMIC are defined.  Py_BUILD_CORE gets defined when certain
        # Python modukes are used.  We simply make sure HAVE_STD_ATOMIC is not
        # defined.
        if 'Py_BUILD_CORE' in defines:
            f.write('''// Py_BUILD_CORE/HAVE_STD_ATOMIC conflict workaround.
#include <pyconfig.h>
#undef HAVE_STD_ATOMIC

''')

        f.write('''#include <Python.h>


''')

        if len(inittab) > 0:
            c_inittab = 'extension_modules'

            self._write_inittab(f, inittab, c_inittab)
        else:
            c_inittab = 'NULL'

        sys_path = project.sys_path

        if sys_path != '':
            f.write('static const char *path_dirs[] = {\n')

            for dir_name in shlex.split(sys_path):
                f.write('    "{0}",\n'.format(dir_name.replace('"','\\"')))

            f.write('''    NULL
};

''')

        if project.application_script != '':
            main_module = '__main__'
            entry_point = 'NULL'
        else:
            main_module, entry_point = project.application_entry_point.split(
                    ':')
            entry_point = '"' + entry_point + '"'

        path_dirs = 'path_dirs' if sys_path != '' else 'NULL'

        if self._target.platform.name == 'win':
            f.write('''

#include <windows.h>

extern int pyqtdeploy_start(int argc, wchar_t **w_argv,
        struct _inittab *extension_modules, const char *main_module,
        const char *entry_point, const char **path_dirs);

int main(int argc, char **)
{
    LPWSTR *w_argv = CommandLineToArgvW(GetCommandLineW(), &argc);

    return pyqtdeploy_start(argc, w_argv, %s, "%s", %s, %s);
}
''' % (c_inittab, main_module, entry_point, path_dirs))
        else:
            f.write('''

extern int pyqtdeploy_start(int argc, char **argv,
        struct _inittab *extension_modules, const char *main_module,
        const char *entry_point, const char **path_dirs);

int main(int argc, char **argv)
{
    return pyqtdeploy_start(argc, argv, %s, "%s", %s, %s);
}
''' % (c_inittab, main_module, entry_point, path_dirs))

        f.close()

    def _write_python_module(self, name, part, parts, part_root_dir,
            resources_contents, job_writer):
        """ Write a Python module as a resource. """

        if not isinstance(part, (DataFile, PythonModule, PythonPackage)):
            return

        # Remove any scope from the name.
        if Part.is_scoped_name(name):
            name = Part.get_unscoped_name(name)

        # If the part root directory isn't specified then get it from the
        # component.
        if part_root_dir is None:
            component = self._sysroot.get_component(part.component_name)
            part_root_dir = component.target_modules_dir

        # Determine the full path of the file and whether or not it needs
        # freezing.
        src_name = name.replace('.', os.sep)

        to_freeze = []
        to_copy = []

        if isinstance(part, PythonModule):
            if part.builtin:
                return

            if os.path.isdir(os.path.join(part_root_dir, src_name)):
                src_name = os.path.join(src_name, '__init__')

            dst_name = src_name + '.pyo'
            src_name = src_name + '.py'

            src_path = os.path.join(part_root_dir, src_name)

            # Check that the .py file exists.
            if not os.path.exists(src_path):
                raise UserException("'{0}' does not exist".format(src_path))

            if not os.path.isfile(src_path):
                raise UserException("'{0}' is not a file".format(src_path))

            to_freeze.append((src_path, dst_name))

        elif isinstance(part, PythonPackage):
            root = os.path.join(part_root_dir, src_name)
            exclusions = [os.path.join(root, exc) for exc in part.exclusions]

            # Walk the package.
            for dirpath, dirnames, filenames in os.walk(root):
                if '__pycache__' in dirnames:
                    dirnames.remove('__pycache__')

                for dname in dirnames:
                    if os.path.join(dirpath, dname) in exclusions:
                        dirnames.remove(dname)

                for fname in filenames:
                    src_path = os.path.join(dirpath, fname)

                    if src_path in exclusions:
                        continue

                    if fname.endswith('.pyc'):
                        continue

                    if fname.endswith('.pyo'):
                        continue

                    rel_resource_path = os.path.relpath(src_path,
                            part_root_dir)

                    if fname.endswith('.py'):
                        # Convert '.py' to '.pyo'.
                        rel_resource_path += 'o'

                        to_freeze.append((src_path, rel_resource_path))
                    else:
                        to_copy.append(rel_resource_path)

        else:
            to_copy.append(os.path.join(os.path.dirname(name), part.name))

        # Freeze required resource files.
        for src_path, rel_resource_path in to_freeze:
            dst_path = self._get_abs_resource_path(rel_resource_path)

            self._freeze(job_writer, name, dst_path, src_path,
                    rel_resource_path.replace(os.sep, '/'))

            resources_contents.append(rel_resource_path)

        # Copy required resource files.
        for rel_resource_path in to_copy:
            src_path = os.path.join(part_root_dir, rel_resource_path)
            dst_path = self._get_abs_resource_path(rel_resource_path)

            shutil.copy2(src_path, dst_path)

            resources_contents.append(rel_resource_path)

    def _write_python_modules(self, parts, resources_contents, job_writer,
            part_root_dir=None):
        """ Write a collection of Python modules as resources. """

        for name, part in parts.items():
            self._write_python_module(name, part, parts, part_root_dir,
                    resources_contents, job_writer)

    def _write_qmake(self, application_name, parts, job_writer, opt,
            resource_names, python):
        """ Create the .pro file for qmake. """

        project = self._project
        target_platform = self._target.platform.name

        f = create_file(
                os.path.join(self._build_dir, application_name + '.pro'))

        f.write('# Generated for {0} and Python v{1}.\n\n'.format(
                self._target.name, python.version))

        f.write('TEMPLATE = app\n')
        f.write('\n')

        # Accumulate all the values of all the qmake variables.
        bundled_shared_libs = set()
        qmake_cpp11 = False
        qmake_config = set()
        qmake_qt = set()
        used_defines = set()
        used_dlls = set()
        used_includepath = set()
        used_inittab = set()
        used_libs = set()
        used_sources = set()

        used_includepath.add(self._sysroot.target_include_dir)
        used_includepath.add(python.target_py_include_dir)

        used_libs.add('-L' + self._sysroot.target_lib_dir)
        used_libs.add('-l' + python.target_py_lib)

        for part in parts.values():
            # Ignore core parts.
            if part.core:
                continue

            if isinstance(part, ExtensionModule):
                if python.install_from_source:
                    used_inittab.add(part.unscoped_name)

                    self._add_values(used_sources, part.source, part)

                    if part.qmake_config is not None:
                        qmake_config.update(part.qmake_config)

                    if part.qmake_cpp11:
                        qmake_cpp11 = True

                    if part.qmake_qt is not None:
                        qmake_qt.update(part.qmake_qt)
                elif target_platform == 'win' and part.pyd is not None:
                    used_dlls.add(part)
            elif isinstance(part, ComponentLibrary):
                if part.bundle_shared_libs:
                    self._add_bundled_shared_libs(part.libs,
                            bundled_shared_libs)
            else:
                continue

            self._add_values(used_defines, part.defines, part,
                    is_filename=False)
            self._add_values(used_libs, part.libs, part, is_filename=False)
            self._add_values(used_includepath, part.includepath, part)

        # Generate QT.
        if qmake_qt:
            f.write('QT += %s\n' % ' '.join(qmake_qt))

        # Generate CONFIG.
        config = ['warn_off']

        if target_platform == 'win':
            if project.application_is_console:
                config.append('console')

        if qmake_cpp11:
            config.append('c++11')

        f.write('CONFIG += {0}\n'.format(' '.join(config)))

        if target_platform == 'macos':
            if not project.application_is_bundle:
                f.write('CONFIG -= app_bundle\n')

        if qmake_config:
            f.write('CONFIG += %s\n' % ' '.join(qmake_config))

        # Python v3.6.0 requires C99 at least.  Note that specifying 'c++11' in
        # 'CONFIG' doesn't affect 'CFLAGS'.
        if python.version >= (3, 6) and target_platform != 'win':
            f.write('\n')
            f.write('QMAKE_CFLAGS += -std=c99\n')

        # Specify the resource files.
        f.write('\n')
        f.write('RESOURCES = \\\n')
        f.write(' \\\n'.join(['    resources/{0}'.format(n) for n in resource_names]))
        f.write('\n')

        # Specify the defines.
        defines = []
        headers = ['pyqtdeploy_version.h', 'frozen_bootstrap.h',
                'frozen_bootstrap_external.h']

        if project.application_script != '':
            defines.append('PYQTDEPLOY_FROZEN_MAIN')
            headers.append('frozen_main.h')

        if opt:
            defines.append('PYQTDEPLOY_OPTIMIZED')

        if defines or used_defines:
            f.write('\n')

            if defines:
                f.write('DEFINES += {0}\n'.format(' '.join(defines)))

            self._write_used_values(f, used_defines, 'DEFINES')

        # Specify the include paths.
        if used_includepath:
            f.write('\n')
            self._write_used_values(f, used_includepath, 'INCLUDEPATH')

        # Specify the source files and header files.
        f.write('\n')
        f.write('SOURCES = pyqtdeploy_main.cpp pyqtdeploy_start.cpp pdytools_module.cpp\n')
        self._write_used_values(f, used_sources, 'SOURCES')
        self._write_main(used_inittab, used_defines)
        shutil.copy2(self._get_lib_path('pyqtdeploy_start.cpp'),
                self._build_dir)
        shutil.copy2(self._get_lib_path('pdytools_module.cpp'),
                self._build_dir)

        f.write('\n')
        f.write('HEADERS = {0}\n'.format(' '.join(headers)))

        # Specify the libraries.
        if used_libs:
            f.write('\n')
            self._write_used_values(f, used_libs, 'LIBS')

        # Additional configuration for Android.
        if target_platform == 'android':
            f.write('\n')
            f.write('ANDROID_ABIS = {}\n'.format(self._target.android_abi))

            if bundled_shared_libs and target_platform == 'android':
                f.write(
                        'ANDROID_EXTRA_LIBS += %s\n' % ' '.join(
                                bundled_shared_libs))

        # If we are using the installed Python on Windows then copy in the
        # required DLLs.
        if used_dlls:
            self._copy_windows_dlls(python, used_dlls, f)

        # Add the project independent post-configuration stuff.
        with open_file(self._get_lib_path('post_configuration.pro')) as pro_f:
            f.write('\n')
            f.write(pro_f.read())

        # Add any application specific stuff.
        qmake_configuration = project.qmake_configuration.strip()

        if qmake_configuration != '':
            f.write('\n' + qmake_configuration + '\n')

        # All done.
        f.close()

    def _write_resource(self, resources_contents, nr=-1):
        """ Write a single resource file and return its basename. """

        suffix = '' if nr < 0 else str(nr)
        basename = 'pyqtdeploy{0}.qrc'.format(suffix)

        with create_file(os.path.join(self._build_dir, 'resources', basename)) as f:
            f.write('''<!DOCTYPE RCC>
<RCC version="1.0">
    <qresource>
''')

            for content in resources_contents:
                f.write('        <file>{}</file>\n'.format(content))

            f.write('''    </qresource>
</RCC>
''')

        return basename

    # The map of non-C/C++ source extensions to qmake variable.
    _source_extensions = (
        ('.asm',    'MASMSOURCES'),
        ('.h',      'HEADERS'),
        ('.java',   'JAVASOURCES'),
        ('.l',      'LEXSOURCES'),
        ('.pyx',    'CYTHONSOURCES'),
        ('.y',      'YACCSOURCES')
    )

    @classmethod
    def _write_used_values(cls, f, used_values, name):
        """ Write a set of used values to a .pro file. """

        # Sort them for reproduceable output.
        for value in sorted(used_values):
            qmake_var = name

            if qmake_var == 'SOURCES':
                for ext, var in cls._source_extensions:
                    if value.endswith(ext):
                        qmake_var = var
                        break

            elif qmake_var == 'LIBS':
                # A (strictly unnecessary) bit of pretty printing.
                if value.startswith('"-framework') and value.endswith('"'):
                    value = value[1:-1]

            f.write('{0} += {1}\n'.format(qmake_var, value))

    def _copy_windows_dlls(self, python, parts, f):
        """ Generate additional qmake commands to install additional Windows
        DLLs so that the application will be able to run.
        """

        dlls = []

        for part in parts:
            dlls.append(part.pyd)

            if part.dlls is not None:
                dlls.extend(part.dlls)

        dlls = ['DLLs\\' + dll for dll in dlls]

        py_major = python.version.major
        py_minor = python.version.minor

        dlls.append('python{}{}.dll'.format(py_major, py_minor))
        dlls.append('python{}.dll'.format(py_major))
        dlls.append('vcruntime140.dll')

        if python.version >= (3, 8):
            dlls.append('vcruntime140_1.dll')

        for name in dlls:
            f.write('''
PDY_DLL = %s\\%s
exists($$PDY_DLL) {
    CONFIG(debug, debug|release) {
        QMAKE_POST_LINK += $(COPY_FILE) $$shell_path($$PDY_DLL) $$shell_path($$OUT_PWD/debug) &
    } else {
        QMAKE_POST_LINK += $(COPY_FILE) $$shell_path($$PDY_DLL) $$shell_path($$OUT_PWD/release) &
    }
}
''' % (python.target_lib_dir, name))
