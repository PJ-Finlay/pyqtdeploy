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

from ..parts import DataFile, PythonModule


class QrcPackage():
    """ The encapsulation of a memory-filesystem package. """

    def __init__(self):
        """ Initialise the package. """

        self.name = None
        self.contents = []
        self.exclusions = ['*.pyc', '*.pyd', '*.pyo', '*.pyx', '*.pxi',
                '__pycache__', '*-info', 'EGG_INFO', '*.so']

    @property
    def parts(self):
        """ Return the package as a dict of parts. """

        parts = {}

        for node in self.contents:
            self._add_part(node, os.path.basename(self.name), parts)

        return parts

    def _add_part(self, node, parent_name, parts):
        """ Add a single file or directory to the parts dict. """

        if node.included:
            node_name = parent_name + '.' + node.name

            if isinstance(node, QrcDirectory):
                for child in node.contents:
                    self._add_part(child, node_name, parts)
            else:
                if node_name.endswith('.py'):
                    key = node_name[:-3]
                    part = PythonModule()
                else:
                    key = parent_name + '/' + node.name
                    part = DataFile(node.name)

                parts[key] = part


class QrcFile():
    """ The encapsulation of a memory-filesystem file. """

    def __init__(self, name, included=True):
        """ Initialise the file. """

        self.name = name
        self.included = included


class QrcDirectory(QrcFile):
    """ The encapsulation of a memory-filesystem directory. """

    def __init__(self, name, included=True):
        """ Initialise the directory. """

        super().__init__(name, included)

        self.contents = []
