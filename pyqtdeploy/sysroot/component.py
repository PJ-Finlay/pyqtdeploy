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
from html.parser import HTMLParser
import os
import shutil
from urllib.error import HTTPError
from urllib.request import urlopen

from .abstract_component import AbstractComponent
from .component_option import ComponentOption


class Component(AbstractComponent):
    """ The base class for the implemenation of component plugins that can be
    installed from a source package.
    """

    ###########################################################################
    # The following make up the public API to be used by component plugins.
    ###########################################################################

    # Set if installing from source is mandatory.
    must_install_from_source = False

    def get_archive(self):
        """ Return the pathname of a local copy of a source archive.  The
        source directories specified by the --source-dir command line option
        are searched first.  If the archive was not found then it is downloaded
        from the optional URL.
        """

        archive_name = self.get_archive_name()

        # Search any source directories.
        archive = self.get_file(archive_name)
        if archive is not None:
            return archive

        # Search the download cache.
        cache_dir = os.path.join(os.path.expanduser('~'), '.pyqtdeploy',
                'cache')

        archive = os.path.join(cache_dir, archive_name)
        if os.path.isfile(archive):
            self.verbose("found '{0}' in download cache".format(archive_name))
            return archive

        # Try and download the archive into the cache.
        urls = self.get_archive_urls()
        if urls:
            self.create_dir(cache_dir)

            for url in urls:
                archive_url = url + archive_name

                self.progress(
                        "downloading '{0}' from {1}".format(archive_name, url))

                try:
                    with urlopen(archive_url) as response, open(archive, 'wb') as f:
                        shutil.copyfileobj(response, f)
                except HTTPError:
                    self.verbose("'{0}' was not found".format(archive_url))
                    continue
                except Exception as e:
                    self.verbose(
                            "unable to download '{0}'".format(archive_url))
                    continue

                self.verbose("downloaded '{0}'".format(archive_url))

                return archive

        self.error("unable to find '{0}'".format(archive))

    @abstractmethod
    def get_archive_name(self):
        """ Return the filename of the source archive. """

    def get_archive_urls(self):
        """ Return the list of URLs where the source archive might be
        downloaded from.
        """

        # This default implementation does not support downloads.
        return []

    def get_pypi_urls(self, pypi_project):
        """ Return a list of URLs (excluding the source archive name) where a
        source archive may be downloaded from a PyPI project.
        """

        # The PyPI URL of the project page of the required version.
        url = 'https://pypi.org/project/{}/{}/'.format(pypi_project,
                self.version)

        self.verbose("reading '{0}'".format(url))

        try:
            with urlopen(url) as response:
                page = response.read().decode('utf-8')
        except Exception as e:
            self.error("unable to read '{0}'".format(url), detail=str(e))

        parser = PyPIPageParser(self.get_archive_name())
        parser.feed(page)

        if parser.archive_url is None:
            self.verbose(
                    "unable to find link to '{0}' in '{1}'".format(
                            self.get_archive_name(), url))
            return []

        return [parser.archive_url]

    def unpack_archive(self, archive, chdir=True):
        """ An archive is unpacked in the current directory.  If requested its
        top level directory becomes the current directory.  The name of the
        directory (not its pathname) is returned.
        """

        # Windows has a problem extracting the Qt source archive (probably the
        # long pathnames).  As a work around we copy it to the current
        # directory and extract it from there.
        self.copy_file(archive, '.')
        archive_name = os.path.basename(archive)

        # Unpack the archive.
        self.verbose("unpacking '{}'".format(archive_name))

        try:
            shutil.unpack_archive(archive_name)
        except Exception as e:
            self.error("unable to unpack {0}".format(archive_name),
                    detail=str(e))

        # Assume that the name of the extracted directory is the same as the
        # archive without the extension.
        archive_root = None
        for _, extensions, _ in shutil.get_unpack_formats():
            for ext in extensions:
                if archive_name.endswith(ext):
                    archive_root = archive_name[:-len(ext)]
                    break

            if archive_root:
                break
        else:
            # This should never happen if we have got this far.
            self.error("'{0}' has an unknown extension".format(archive))

        # Validate the assumption by checking the expected directory exists.
        if not os.path.isdir(archive_root):
            self.error(
                    "unpacking {0} did not create a directory called '{1}' as "
                            "expected".format(archive_name, archive_root))

        # Delete the copied archive.
        os.remove(archive_name)

        # Change to the extracted directory if required.
        if chdir:
            os.chdir(archive_root)

        return archive_root

    ###########################################################################
    # The following are not part of the public API used by component plugins.
    ###########################################################################

    def get_options(self):
        """ Return a list of ComponentOption objects that define the components
        configurable options.
        """

        options = super().get_options()

        if not self.must_install_from_source:
            options.append(
                    ComponentOption('install_from_source', type=bool,
                            default=True,
                            help="Install from a source package rather an "
                                    "existing installation."))

        return options


class PyPIPageParser(HTMLParser):
    """ An HTML parser for extract a source archive name from a PyPI project
    page.
    """

    def __init__(self, archive):
        """ Initialise the parser. """

        super().__init__()

        self._archive = archive
        self.archive_url = None

    def handle_starttag(self, tag, attrs):
        """ Reimplemented to handle a start tag. """

        if tag == 'a':
            for name, value in attrs:
                if name == 'href' and value.endswith(self._archive):
                    self.archive_url = value[:-len(self._archive)]
                    break
