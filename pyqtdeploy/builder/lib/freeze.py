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
import marshal
import os
import sys


def freeze_as_data(py_filename, data_filename, embedded_name):
    """ Freeze a Python source file and save it as data. """

    code = _get_marshalled_code(py_filename, embedded_name)

    data_file = open(data_filename, 'wb')
    data_file.write(code)
    data_file.close()


def freeze_as_c(py_filename, c_filename, embedded_name):
    """ Freeze a Python source file and save it as C source code. """

    code = _get_marshalled_code(py_filename, os.path.basename(py_filename))

    c_file = open(c_filename, 'wt')

    c_file.write(
            'static unsigned char frozen_%s[] = {' % embedded_name)

    for i in range(0, len(code), 16):
        c_file.write('\n    ')
        for j in code[i:i + 16]:
            c_file.write('%d, ' % j)

    c_file.write('\n};\n')

    c_file.close()


def _get_marshalled_code(py_filename, embedded_name):
    """ Convert a Python source file to a marshalled code object. """

    try:
        source_file = open(py_filename, 'rb')
    except Exception as e:
        sys.stderr.write("{0}: {1}\n".format(py_filename, str(e)))
        sys.exit(1)

    source = source_file.read()
    source_file.close()

    co = compile(source, embedded_name, 'exec')

    return marshal.dumps(co)


# Parse the command line.
if len(sys.argv) != 2:
    sys.stderr.write("Invalid command line\n")
    sys.exit(2)

job_filename = sys.argv[1]

# Read the jobs file.
job_file = open(job_filename, newline='')

job_reader = csv.reader(job_file)

for label, out_filename, py_filename, embedded_name, conversion in job_reader:
    sys.stdout.write("Freezing {0}...\n".format(label))
    sys.stdout.flush()

    if conversion == 'C':
        freeze_as_c(py_filename, out_filename, embedded_name)
    else:
        freeze_as_data(py_filename, out_filename, embedded_name)

job_file.close()
