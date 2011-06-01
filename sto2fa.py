#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# sto2fa.py :: converts a stockholm multiple sequence alignment file to fasta
# format.
# 
# Copyright (C) 2011 N Lance Hepler <nlhepler@gmail.com> 
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import os, sys

from os.path import basename, dirname, exists, join, realpath

import platform
if platform.system().lower() == 'darwin':
    __subpath = join('python%d%d' % sys.version_info[:2], 'lib', 'python')
    # numpy must go first 
    for module in ('biopython-1.56',):
        path = join(dirname(realpath(__file__)), 'contrib', module, __subpath)
        if exists(path):
            sys.path.insert(0, path)

from Bio import AlignIO


def main(name=None, argv=None):

    if name is None:
        name = basename(sys.argv[0])

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print >> sys.stderr, 'usage: %s <infile>' % name
        return -1

    ih = open(argv[0], 'r')

    alignments = AlignIO.parse(ih, 'stockholm')
    AlignIO.write(alignments, sys.stdout, 'fasta')

    ih.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())