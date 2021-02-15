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


from abc import abstractmethod

from .component import Component


class AbstractPyQtComponent(Component):
    """ The abstract base class for an implementation of a PyQt component
    plugin.
    """

    ###########################################################################
    # The following make up the public API to be used by component plugins.
    ###########################################################################

    @abstractmethod
    def install_pyqt_component(self, component):
        """ Install a PyQt-based component using SIP v5 or later. """

    @property
    @abstractmethod
    def pyqt_platform(self):
        """ The target platform name as recognised by PyQt. """

    @property
    @abstractmethod
    def using_sip_v4(self):
        """ True if SIP v4 is being used. """

    @abstractmethod
    def verify_pyqt_component(self, min_pyqt_version, min_sipbuild_version,
            min_pyqtbuild_version):
        """ Verify a PyQt-based component.  All versions are minimum versions.
        The sipbuild and pyqtbuild version numbers are ignored if SIP v4 is
        being used.
        """
