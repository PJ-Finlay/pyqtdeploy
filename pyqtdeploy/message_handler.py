# Copyright (c) 2017, Riverbank Computing Limited
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
import sys


class MessageHandler:
    """ The MessageHandler class handles progress and verbose progress
    messages.  This base implementation issues messages to the console.
    """

    def __init__(self, quiet, verbose):
        """ Initialise the object.  quiet is set if all progress messages
        should be disabled.  verbose is set if verbose progress messages should
        be enabled.  Messages do not have trailing newlines.
        """

        self.quiet = quiet
        self.verbose = verbose

    @classmethod
    def error(cls, message):
        """ Handle an error message. """

        print("{0}: {1}".format(os.path.basename(sys.argv[0]), message),
                file=sys.stderr, flush=True)

    def exception(self, e):
        """ Handle an exception. """

        if self.verbose and e.detail != '':
            self.error("{0}: {1}".format(e.text[:-1], e.detail))
        else:
            self.error(e.text)

    def message(self, message):
        """ Handle a message.  This method may be reimplemented to send the
        message to somewhere other that stdout.
        """

        print(message, flush=True)

    def progress_message(self, message):
        """ Handle a progress message. """

        if not self.quiet:
            # There should already be one trailing period.
            self.message(message + '..')

    def verbose_message(self, message):
        """ Handle a verbose progress message. """

        if self.verbose and not self.quiet:
            self.message(message)

    def warning(self, message):
        """ Handle a warning message. """

        if not self.quiet:
            self.message("WARNING: " + message)
