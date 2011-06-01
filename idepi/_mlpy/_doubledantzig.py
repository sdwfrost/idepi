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

from _dantzig import Dantzig
from _wrappedregressor import WrappedRegressor


__all__ = ['DoubleDantzig']


class DoubleDantzig(WrappedRegressor):
    def __init__(self, tol0=0.001, lam0=1.0, tol=0.001, lam=0.001, **kwargs):
        super(DoubleDantzig, self).__init__(selectorcls=Dantzig, regressorcls=Dantzig, tol0=tol0, lam0=lam0, tol1=tol, lam1=lam, **kwargs)