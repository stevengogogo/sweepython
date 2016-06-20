# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 16:45:59 2016
Functions for mom bud analysis in module vtk_mom_bud_analyse.py
@author: sweel
"""
import os.path as op
from collections import defaultdict
import cPickle as pickle
import pandas as pd
from tvtk.api import tvtk
import vtk
# pylint: disable=C0103


class UsageError(Exception):
    """
    Class for user-facing (non-programming) errors
    """
    pass


def gen_data(regen=False, **kwargs):
    """
    wrapper func to call mungedata, pass default params in kwargs and
    regenerate individual vtk DataFrames via vf.cellpos()

    Kwargs
    ------

    inpdatpath : Str
        filepath to celldata pickle file, if not specified then `dfvoldata` and
        `fkeys` must be specified

    dfvoldata : DataFrame
        cell volume data

    fkeys : dict
        dictionary of filepaths to individual cell VTK data

    Returns
    -------

    F : dict
        dictionary of DataFrames data for individual cells, output of calling
        cellpos()
    """

    fpath = kwargs.get('inpdatpath')

    # regenerates pickle file if not exist
    if regen or not op.isfile(fpath):
        F = {}

        for k in ['dfvoldata', 'fkeys']:
            if k not in kwargs:
                raise UsageError('Missing {}'.format(k))
        dfvol = kwargs.get('dfvoldata')
        filepaths = kwargs.get('fkeys')

        for k in sorted(filepaths):
            F[k] = cellpos(filepaths[k], dfvol)
        with open(fpath, 'wb') as out:
            pickle.dump(F, out)
    else:
        with open(fpath, 'rb') as inp:
            F = pickle.load(inp)
    return F


def vtkopen(fpath):
    """
    wrapper to open polydata files
    """
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(fpath)
    reader.Update()
    data = reader.GetOutput()
    return data


def cellpos(cellname, df, **kwargs):
    """
    Return DataFrame of cell along mom-bud axis coords.

    Parameters
    ----------
    cellname : str
               Name of cell
    df : dataFrame
         Dataframe of mom,bud,neck coords

    kwargs:
    -------
    dyscale : str
        `DY_minmax` (default)

    dyraw : str
        `DY_raw` (default)

    Returns
    -------
    celldf : DataFrame
        Columns `DY`, `x`, `wholecell_xaxis`, `type`, `indcell_xaxis`

    """
    dyscale = kwargs.pop("dyscale", "DY_minmax")
#    dyraw = kwargs.pop("dyraw", "DY_raw")
    dyraw = kwargs.pop("dyraw", "bkstGFP")
    outdic = {}

    cellkey = cellname.rsplit('\\', 1)[1][:-4]
    data = vtkopen(cellname)
    data = tvtk.to_tvtk(data)
    # is a column vec of R^3 (coordinates in the skel)
    npx = data.points.to_array()
    # indices of npx that would sort npx according to the x-axis
    xind = npx[:, 0].argsort()
    dy = data.point_data.get_array(dyscale).to_array()
    dy_raw = data.point_data.get_array(dyraw).to_array()

    #  individual skeletons xyz and Δψ
    celldf = pd.DataFrame({'x': npx[:, 0][xind],
                           'DY': dy[xind],
                           'DY_abs': dy_raw[xind]})
    xn, _, _ = df.ix[cellkey, 'neck']
    xb, _, _ = df.ix[cellkey, 'base']
    xt, _, _ = df.ix[cellkey, 'tip']

    outdic['neckpos_scaled'] = (xn - celldf.ix[0, 'x']) / (xt - xb)

    celldf['whole_cell_axis'] = ((celldf.ix[:, 'x'] -
                                  celldf.ix[0, 'x']) / (xt - xb))
    celldf['type'] = ''
    celldf.loc[celldf.x > xn, ['type']] = 'bud'
    celldf.loc[celldf.x <= xn, ['type']] = 'mom'
    #
    celldf.loc[celldf.type == 'bud',
               'ind_cell_axis'] = (celldf.ix[:, 'x']-xn) / (xt-xn)
    celldf.loc[celldf.type ==
               'mom', 'ind_cell_axis'] = (celldf.ix[:, 'x']-xb) / (xn-xb)
    celldf.index.name = cellkey

    outdic['bud_diameter'] = xt - xn
    outdic['mom_diameter'] = xn - xb
    outdic['neckpos'] = xn
    outdic['type'] = cellkey.split('_')[0]
    outdic['date'] = cellkey.split('_')[1]
    outdic['whole_cell_mean'] = celldf.DY.mean()
    outdic['whole_cell_abs'] = celldf.DY_abs.mean()
    return dict(df=celldf, celldata=outdic)


def bincell(cellname, col, bins):
    """
    Return a cell DataFrame  and `col` according to `bins`.

    Parameters
    ----------
    cellname : str
           name of cell
    col  : str
           col to be binned
    bins : list
           sequence of scalars for the bin edges

    Returns
    -------
    column of categorical labels for the bins
    """
    binnedcell = pd.cut(cellname.ix[:, col],
                        bins,
                        labels=bins[1:])

    return binnedcell


def neckDY(fname, celldf, neck_position, outdic, dist=None):
    """
    Return two Series of points within a range of +-dist from neck
    """
    if dist is None:
        dist = [.15, .3, .5]
    tempdic = defaultdict(dict)
    tempdic[fname]['bud'] = {}
    tempdic[fname]['mom'] = {}

    for d in dist:
        tempdic[fname]['bud'][d] = celldf.loc[(celldf.x >= neck_position) &
                                              (celldf.x <
                                               (neck_position + d))].DY.mean()
        tempdic[fname]['mom'][d] = celldf.loc[(celldf.x < neck_position) &
                                              (celldf.x >=
                                               (neck_position - d))].DY.mean()
    return outdic.update(tempdic)


def xcell(x, f):
    """
    return DataFrame of mom binned Δψ + first point of bud
    """
    x['temp'] = x.index.astype('float')

    if len(f.DY.values):
        x = x.append(pd.Series({'DY': f.get_value(0, 'DY')}),
                     ignore_index=True)
    else:
        x = x.append(pd.Series({'DY': 0}),
                     ignore_index=True)

    x.loc[max(x.index), 'temp'] = 'fp'
    x['cellaxis_mom_budfp'] = x.temp.astype('category', ordered=True)
    return x
