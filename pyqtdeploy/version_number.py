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


from collections import namedtuple

from .user_exception import UserException


class VersionNumber:
    """ A parsed version number.  The major, minor and patch attributes are
    integers and the suffix attribute is a string.  Instances can be compared
    to determine the chronology of releases.
    """

    def __init__(self, major, minor=0, patch=0, suffix=''):
        """ Initialise the version number. """

        self.major = major
        self.minor = minor
        self.patch = patch
        self.suffix = suffix

    def __str__(self):
        """ Return the version number as a string. """

        return "{}.{}.{}{}".format(self.major, self.minor, self.patch,
                self.suffix)

    def __eq__(self, other):
        """ Return True if this version number is equal to another. """

        other = self._resolve_other(other)
        if other is None:
            return NotImplemented

        major, minor, patch, suffix = other

        if self.major != major:
            return False

        if minor is None:
            return True

        if self.minor != minor:
            return False

        if patch is None:
            return True

        if self.patch != patch:
            return False

        if suffix is None:
            return True

        return self.suffix == suffix

    def __ge__(self, other):
        """ Return True if this version number is greater than or equal to
        another.
        """

        other = self._resolve_other(other)
        if other is None:
            return NotImplemented

        major, minor, patch, suffix = other

        if self.major < major:
            return False

        if self.major > major:
            return True

        if minor is None:
            return True

        if self.minor < minor:
            return False

        if self.minor > minor:
            return True

        if patch is None:
            return True

        if self.patch < patch:
            return False

        if self.patch > patch:
            return True

        if suffix is None:
            return True

        return self.suffix >= suffix

    def __gt__(self, other):
        """ Return True if this version number is greater than another. """

        other = self._resolve_other(other)
        if other is None:
            return NotImplemented

        major, minor, patch, suffix = other

        if self.major > major:
            return True

        if self.major < major or minor is None:
            return False

        if self.minor > minor:
            return True

        if self.minor < minor or patch is None:
            return False

        if self.patch > patch:
            return True

        if self.patch < patch or suffix is None:
            return False

        return self.suffix > suffix

    def __le__(self, other):
        """ Return True if this version number is less than or equal to
        another.
        """

        other = self._resolve_other(other)
        if other is None:
            return NotImplemented

        major, minor, patch, suffix = other

        if self.major > major:
            return False

        if self.major < major:
            return True

        if minor is None:
            return True

        if self.minor > minor:
            return False

        if self.minor < minor:
            return True

        if patch is None:
            return True

        if self.patch > patch:
            return False

        if self.patch < patch:
            return True

        if suffix is None:
            return True

        return self.suffix <= suffix

    def __lt__(self, other):
        """ Return True if this version number is less than another. """

        other = self._resolve_other(other)
        if other is None:
            return NotImplemented

        major, minor, patch, suffix = other

        if self.major < major:
            return True

        if self.major > major or minor is None:
            return False

        if self.minor < minor:
            return True

        if self.minor > minor or patch is None:
            return False

        if self.patch < patch:
            return True

        if self.patch > patch or suffix is None:
            return False

        return self.suffix < suffix

    @classmethod
    def parse_version_number(cls, version_nr):
        """ Parse a string, encoded integer or tuple and return the
        corresponding VersionNumber object.  version_nr is the version number.
        UserException is raised if it couldn't be parsed.
        """

        if isinstance(version_nr, VersionNumber):
            return version_nr

        if isinstance(version_nr, tuple):
            return VersionNumber(*version_nr)

        if isinstance(version_nr, int):
            major = (version_nr >> 16) & 0xff
            minor = (version_nr >> 8) & 0xff
            patch = version_nr & 0xff

            return VersionNumber(major, minor, patch)

        assert isinstance(version_nr, str)

        # Split into 3 parts at the most.
        version_parts = version_nr.split('.', maxsplit=2)

        # Split the last part into any leading integer part and any suffix.
        last_part = version_parts.pop()
        int_part = ''
        suffix = ''

        for i, ch in enumerate(last_part):
            if ch.isdigit():
                int_part += ch
            else:
                suffix = last_part[i:]
                break

        if int_part:
            version_parts.append(int_part)
        elif len(version_parts) == 0:
            raise UserException(
                    "'{0}' has no major number".format(version_nr))

        # Make sure there are 3 integer parts.
        while len(version_parts) < 3:
            version_parts.append('0')

        # Convert the integer parts.
        try:
            major = int(version_parts[0])
        except ValueError:
            raise UserException(
                    "the major number of '{0}' is invalid".format(version_nr))

        try:
            minor = int(version_parts[1])
        except ValueError:
            raise UserException(
                    "the minor number of '{0}' is invalid".format(version_nr))

        try:
            patch = int(version_parts[2])
        except ValueError:
            raise UserException(
                    "the patch number of '{0}' is invalid".format(version_nr))

        # Create the VersionNumber object.
        return cls(major, minor, patch, suffix)

    def _resolve_other(self, other):
        """ Return an appropriate 4-tuple from the value provided as the right
        hand side of an operator.
        """

        # See if it just the major version number.
        if isinstance(other, int):
            return (other, None, None, None)

        # See if it is a parsed version number.
        if isinstance(other, VersionNumber):
            return (other.major, other.minor, other.patch, other.suffix)

        # See if it is a tuple.
        if isinstance(other, tuple):
            nr = len(other)

            if nr < 1 or nr > 4:
                raise ValueError(
                        "a comparison tuple must have between 1 and 4 elements")

            # The number of elements in the tuple determines the precision of
            # the comparison.
            major = other[0]
            minor = None
            patch = None
            suffix = None

            if nr > 1:
                minor = other[1]

                if nr > 2:
                    patch = other[2]

                    if nr > 3:
                        suffix = other[3]

            return (major, minor, patch, suffix)

        # We don't support the type.
        return None
