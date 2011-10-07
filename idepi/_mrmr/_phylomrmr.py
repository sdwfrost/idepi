#
# idepi :: (IDentify EPItope) python libraries containing some useful machine
# learning interfaces for regression and discrete analysis (including
# cross-validation, grid-search, and maximum-relevance/mRMR feature selection)
# and utilities to help identify neutralizing antibody epitopes via machine
# learning.
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

# import multiprocessing as mp

from exceptions import StandardError
from re import match
from operator import itemgetter
from sys import exit, stderr, stdout

import numpy as np

from _fakepool import FakePool
from _basemrmr import BaseMrmr


__all__ = ['PhyloMrmr']


def _compute_mi_inner_log2(nrow, v, variables, targets_t, p=None):
    p_t = float(np.sum(targets_t)) / nrow # p(X == t)
    p_v = np.sum((v - (variables > 0.)) if v == 1 else variables > 0., axis=0).astype(float) / nrow # p(Y == v)
    p_tv = np.sum(np.multiply(targets_t, variables).astype(float), axis=0) / np.sum(targets_t) # p(X == t, Y == v)
    mi = np.nan_to_num(np.multiply(p_tv, np.log2(p_tv / (p_t * p_v))))
    h = -np.nan_to_num(np.multiply(p_tv, np.log2(p_tv)))

    # print 'targets:', targets_t.T.astype(int), 'class:', v, 'p_t:', p_t, 'p_v:', p_v, 'p_tv:', p_tv, 'mi:', mi

    if p is not None:
        p.value += 1

    return mi, h


def _compute_mi_inner_log10(nrow, v, variables, targets_t, p=None):
    p_t = float(np.sum(targets_t)) / nrow # p(X == t)
    p_v = np.sum((v - variables if v > 0 else variables) > 0., axis=0).astype(float) / nrow # p(Y == v)
    p_tv = np.sum(np.multiply(targets_t, variables), axis=0).astype(float) / nrow # p(X == t, Y == v)
    mi = np.nan_to_num(np.multiply(p_tv, np.log10(p_tv / (p_t * p_v))))
    h = -np.nan_to_num(np.multiply(p_tv, np.log10(p_tv)))

    if p is not None:
        p.value += 1

    return mi, h


class PhyloMrmr(BaseMrmr):

    def __init__(self, *args, **kwargs):
        super(PhyloMrmr, self).__init__(*args, **kwargs)

    @classmethod
    def _compute_mi(cls, variables, targets, ui=None):

        nrow, ncol = variables.shape

        logmod = None
        maxclasses = np.ones(variables.shape, dtype=int) + 1 # this is broken, methinx: np.maximum(np.max(variables, axis=0), np.max(targets)) + 1

        if np.all(maxclasses == 2):
            workerfunc = _compute_mi_inner_log2
        else:
            workerfunc = _compute_mi_inner_log10
            logmod = np.log10(maxclasses)

        vclasses = xrange(1) # vclasses never assesses the ! case in phylomrmr 
        tclasses = set(targets > 0.)

        targets = np.atleast_2d(targets)

        # transpose if necessary (likely if coming from array)
        if targets.shape[0] == 1 and targets.shape[1] == variables.shape[0]:
            targets = targets.T
        elif targets.shape[1] != 1 or targets.shape[0] != variables.shape[0]:
            raise ValueError('`y\' should have as many entries as `x\' has rows.')

        # initialized later
        tcache = {}

        progress = None
        if ui:
            progress = ui.progress

        res = {}

        pool = FakePool() # mp.Pool(mp.cpu_count())

        for v in vclasses:
            for t in tclasses:
                if t not in tcache:
                    tcache[t] = t - (targets > 0.) if t else targets > 0.
                res[(t, v)] = pool.apply_async(workerfunc, (nrow, v, variables, tcache[t], progress))

        pool.close()
        pool.join()

        mi, h = np.zeros((ncol,), dtype=float), np.zeros((ncol,), dtype=float)

        for r in res.values():
            mi_, h_ = r.get()
            mi += mi_
            h += h_
            if progress is not None:
                progress.value += 1

        if logmod is not None:
            mi /= logmod
            h  /= logmod

        return np.nan_to_num(mi), np.nan_to_num(h)

    @staticmethod
    def _prepare(x, y, ui=None):

        if x.dtype != float and np.all(0. <= x) and np.all(x <= 1.):
            raise ValueError('X must have real values of type `float\' that are probabilities in [0., 1.]')

        if (y.dtype != int and y.dtype != bool) or not set(y).issubset(set((-1, 0, 1))):
            raise ValueError('Y must belong to discrete classes of type `int\' in (-1, 0, 1)')

        vars = np.copy(x)
        targets = np.copy(y)

        targets = targets > 0. # targets just became bool

        if ui is not None:
            ui.complete.value *= 8

        return vars, targets, None