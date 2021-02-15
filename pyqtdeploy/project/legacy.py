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


from xml.etree.ElementTree import Element, ElementTree, SubElement

from ..platforms import Platform
from ..user_exception import UserException
from ..version_number import VersionNumber

from .project_parts import QrcDirectory, QrcFile, QrcPackage


# The minimum supported XML project version.
_MIN_VERSION = 4

# The last project version.
_LAST_VERSION = 7


def load_xml(project, file_path):
    """ Load a legacy XML project and raise a UserException if there was an
    error.
    """

    tree = ElementTree()

    try:
        root = tree.parse(file_path)
    except Exception as e:
        raise UserException(
                "there was an error reading the project file", str(e))

    _assert(root.tag == 'Project',
            "Unexpected root tag '{0}', 'Project' expected.".format(root.tag))

    # Check the project version number.
    version = root.get('version')
    _assert(version is not None, "Missing 'version' attribute.")

    try:
        version = int(version)
    except:
        version = None

    _assert(version is not None, "Invalid 'version'.")

    if version < _MIN_VERSION:
        raise UserException("the project's format is no longer supported")

    if version > _LAST_VERSION:
        raise UserException(
                "the project's format is version {0} but only version {1} is "
                "supported".format(version, _LAST_VERSION))

    # The application specific configuration.
    application = root.find('Application')
    _assert(application is not None, "Missing 'Application' tag.")

    project.application_entry_point = application.get('entrypoint', '')
    project.application_is_console = _get_bool(application, 'isconsole',
            'Application')

    project.application_is_bundle = _get_bool(application, 'isbundle',
            'Application')
    project.application_name = application.get('name', '')
    project.application_script = application.get('script', '')
    project.sys_path = application.get('syspath', '')

    # Any qmake configuration. This was added in version 5.
    qmake_configuration = application.find('QMakeConfiguration')

    if qmake_configuration is not None:
        project.qmake_configuration = qmake_configuration.text

    # Any application package.
    app_package = application.find('Package')

    if app_package is not None:
        project.application_package = _load_package(app_package)
    else:
        project.application_package = QrcPackage()

    # Any standard library modules.
    project.parts = []

    for stdlib_module_element in root.iterfind('StdlibModule'):
        name = stdlib_module_element.get('name')
        _assert(name is not None, "Missing 'StdlibModule.name' attribute.")

        project.parts.append('Python:' + name)

    # Any PyQt modules.
    for pyqt_m in root.iterfind('PyQtModule'):
        name = pyqt_m.get('name', '')
        _assert(name != '', "Missing or empty 'PyQtModule.name' attribute.")

        component_map = {
            'Qsci':                 'QScintilla',
            'Qt3DAnimation':        'PyQt3D',
            'Qt3DCore':             'PyQt3D',
            'Qt3DExtras':           'PyQt3D',
            'Qt3DInput':            'PyQt3D',
            'Qt3DLogic':            'PyQt3D',
            'Qt3DRender':           'PyQt3D',
            'QtChart':              'PyQtChart',
            'QtDataVisualization':  'PyQtDataVisualization',
            'QtPurchasing':         'PyQtPurchasing',
            'QtWebEngine':          'PyQtWebEngine',
            'QtWebEngineCore':      'PyQtWebEngineCore',
            'QtWebEngineWidgets':   'PyQtWebEngineWidgets',
            'sip':                  'SIP',
        }

        project.parts.append(
                '{}:PyQt5.{}'.format(component_map.get(name, 'PyQt'), name))


def _assert(ok, detail):
    """ Validate an assertion and raise a UserException if it failed. """

    if not ok:
        raise UserException("the project file is invalid", detail)


def _get_bool(element, name, context, default=None):
    """ Get a boolean attribute from an element. """

    value = element.get(name)
    try:
        value = int(value)
    except:
        value = default

    _assert(value is not None,
            "Missing or invalid boolean value of '{0}.{1}'.".format(context,
                    name))

    return bool(value)


def _load_mfs_contents(mfs_element):
    """ Return a list of contents for a memory-filesystem container. """

    contents = []

    for content_element in mfs_element.iterfind('PackageContent'):
        isdir = _get_bool(content_element, 'isdirectory',
                'Package.PackageContent')

        name = content_element.get('name', '')
        _assert(name != '',
                "Missing or empty 'Package.PackageContent.name' attribute.")

        included = _get_bool(content_element, 'included',
                'Package.PackageContent')

        content = QrcDirectory(name, included) if isdir else QrcFile(name, included)

        if isdir:
            content.contents = _load_mfs_contents(content_element)

        contents.append(content)

    return contents


def _load_package(package_element):
    """ Return a populated QrcPackage instance. """

    package = QrcPackage()

    package.name = package_element.get('name')
    _assert(package.name is not None, "Missing 'Package.name' attribute.")

    package.contents = _load_mfs_contents(package_element)

    package.exclusions = []
    for exclude_element in package_element.iterfind('Exclude'):
        name = exclude_element.get('name', '')
        _assert(name != '',
                "Missing or empty 'Package.Exclude.name' attribute.")
        package.exclusions.append(name)

    return package


def _replace_scopes(value):
    """ Replace any qmake scopes in a value. """

    value = value.replace('linux-*', 'linux')
    value = value.replace('macx', 'macos')
    value = value.replace('win32', 'win')

    return value
