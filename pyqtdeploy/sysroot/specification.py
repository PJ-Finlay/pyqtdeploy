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


from  collections import OrderedDict
import importlib
import importlib.util
import os
import shutil
import toml

from ..platforms import Architecture
from ..user_exception import UserException

from .abstract_component import AbstractComponent
from .abstract_python_component import AbstractPythonComponent
from .abstract_qt_component import AbstractQtComponent
from .abstract_sip_component import AbstractSIPComponent


# Certain well known components must implement specific interfaces.
_COMPONENT_TYPES = {
    'Python': AbstractPythonComponent,
    'Qt': AbstractQtComponent,
    'SIP': AbstractSIPComponent,
}


class SysrootSpecification:
    """ Encapsulate the specification of a system root directory. """

    def __init__(self, specification_file, required=False):
        """ Initialise the object. """

        self.specification_file = specification_file

        self._plugins = {}
        self._spec = {}

        # Load the TOML file.
        try:
            with open(self.specification_file) as f:
                try:
                    self._spec = toml.load(f, _dict=OrderedDict)
                except Exception as e:
                    raise UserException(
                            "{0}: {1}".format(self.specification_file, str(e)))
        except IsADirectoryError:
            if required:
                raise UserException(
                        "{0} is a directory".format(self.specification_file))

            # The specification will be empty.
        except FileNotFoundError:
            if required:
                raise UserException(
                        "{0} was not found".format(self.specification_file))

            # The specification will be empty.
            return

        # Do a high level parse and import the plugins (ie. component
        # factories).
        default_plugin_dir = os.path.dirname(self.specification_file)
        package_root = '.'.join(__name__.split('.')[:-1])

        for name, value in self._spec.items():
            # At the moment every name is a component name and every value is a
            # component configuration.
            if not isinstance(value, OrderedDict):
                raise UserException("unexpected option '{0}'".format(name))

            # Find the component's plugin.  First search the directory
            # containing the specification file.
            plugin = self._plugin_from_file(name, default_plugin_dir)

            # Search the bundled plugin packages.
            if plugin is None:
                for package in ('.plugins', '.plugins.contrib'):
                    plugin = self._plugin_from_package(name, package,
                            package_root)
                    if plugin is not None:
                        break
                else:
                    raise UserException(
                            "unable to find a plugin for '{0}'".format(name))

            # Certain components must implement specific interfaces.
            plugin_type = _COMPONENT_TYPES.get(name)
            if plugin_type is not None and not issubclass(plugin, plugin_type):
                raise UserException(
                        "the {0} plugin must implement a subclass of "
                                "{1}".format(name, plugin_type.__name__))

            self._plugins[name] = plugin

    def create_components_for_target(self, target, sysroot):
        """ Return the list of target-specific components according to this
        specification.
        """

        components = []

        for name, value in self._spec.items():
            # Ignore the component if it is disabled for this target.
            disabled_targets = value.get('disabled_targets')
            if disabled_targets is not None:
                if target.is_targeted(disabled_targets):
                    continue

                del value['disabled_targets']

            # Ignore the component if it not explicity enabled.
            enabled_targets = value.get('enabled_targets')
            if enabled_targets is not None:
                if not target.is_targeted(enabled_targets):
                    continue

                del value['enabled_targets']

            # Identify the default configuration and any target-specific
            # configuration.
            default_config = OrderedDict()
            target_config = None

            for config_name, config_value in value.items():
                if isinstance(config_value, OrderedDict):
                    if target.is_targeted(config_name):
                        target_config = config_value
                else:
                    default_config[config_name] = config_value

            # Apply any defaults to the target configuration.
            if target_config is not None:
                default_config.update(target_config)

            target_config = default_config

            # Create the component using the corresponding plugin.
            plugin = self._plugins[name]
            component = plugin(name, target_config, sysroot)

            components.append(component)

        return components

    def _plugin_from_file(self, name, plugin_dir):
        """ Try and load a component plugin from a file. """

        plugin_file = os.path.join(plugin_dir, name + '.py')
        spec = importlib.util.spec_from_file_location(name, plugin_file)
        plugin_module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(plugin_module)
        except FileNotFoundError:
            return None

        return self._plugin_from_module(name, plugin_module)

    def _plugin_from_package(self, name, package, package_root):
        """ Try and load a component plugin from a Python package. """

        rel_name = package + '.' + name

        try:
            plugin_module = importlib.import_module(rel_name,
                    package=package_root)
        except ImportError:
            return None

        return self._plugin_from_module(package_root + rel_name, plugin_module)

    def _plugin_from_module(self, fq_name, plugin_module):
        """ Get any plugin implementation from a module. """

        fq_name_parts = fq_name.split('.')

        for component_type in plugin_module.__dict__.values():
            if isinstance(component_type, type):
                if issubclass(component_type, AbstractComponent):
                    # Make sure the type is defined in the plugin and not
                    # imported by it.  Allow for a plugin implemented as a
                    # sub-package.
                    if component_type.__module__.split('.')[:len(fq_name_parts)] == fq_name_parts:
                        return component_type

        return None

    def show_options(self, components, message_handler):
        """ Show the options for a sequence of components. """

        headings = ("Component", "Option [*=required]", "Type", "Description")
        widths = [len(h) for h in headings]
        options = OrderedDict()

        # Collect the options for each component while working out the required
        # column widths.
        for component in components:
            name_len = len(component.name)
            if widths[0] < name_len:
                widths[0] = name_len

            # Allow sub-classes to override super-classes.
            component_options = OrderedDict()

            for option in component.get_options():
                component_options[option.name] = option

                name_len = len(option.name)
                if option.required:
                    name_len == 1

                if widths[1] < name_len:
                    widths[1] = name_len

            options[component.name] = component_options

        # Display the formatted options.
        self._show_row(headings, widths, message_handler)

        ulines = ['-' * len(h) for h in headings]
        self._show_row(ulines, widths, message_handler)

        # Calculate the room available for the description column.
        avail = shutil.get_terminal_size()[0] - 1

        for w in widths[:-1]:
            avail -= 2 + w

        avail = max(avail, widths[-1])

        for component_name, component_options in options.items():
            component_col = component_name

            for option_name, option in component_options.items():
                if option.required:
                    option_name += '*'

                row = [component_col, option_name]

                if option.type is int:
                    type_name = 'int'
                elif option.type is str:
                    type_name = 'str'
                elif option.type is bool:
                    type_name = 'bool'
                elif option.type is list:
                    type_name = 'list'
                elif option.type is dict:
                    type_name = 'dict'
                else:
                    type_name = "???"

                row.append(type_name)

                row.append('')
                line = ''
                for word in option.help.split():
                    if len(line) + len(word) < avail:
                        # There is room for the word on this line.
                        if line:
                            line += ' ' + word
                        else:
                            line = word
                    else:
                        if line:
                            # Show what we have so far.
                            row[-1] = line
                            line = word
                        else:
                            # The word is too long so truncate it.
                            row[-1] = word[:avail]

                        self._show_row(row, widths, message_handler)

                        # Make the row blank for the next word.
                        row = [''] * len(headings)

                if line:
                    # The last line.
                    row[-1] = line
                    self._show_row(row, widths, message_handler)

                # Don't repeat the component name.
                component_col = ''

    @staticmethod
    def _show_row(columns, widths, message_handler):
        """ Show one row of the options table. """

        row = ['{:{width}}'.format(columns[i], width=w) 
                for i, w in enumerate(widths)]

        message_handler.message('  '.join(row))
