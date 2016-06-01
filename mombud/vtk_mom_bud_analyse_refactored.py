# -*- coding: utf-8 -*-
"""
module to analyze mom bud asymmetry
"""
import sys
import os
import os.path as op
import cPickle as pickle
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from mombud.functions import vtk_mbfuncs as vf
import wrappers as wr
# pylint: disable=C0103

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.close('all')

#==============================================================================
# Data directory prep
#==============================================================================
datadir = op.join(os.getcwd(), 'mutants', 'transformedData', 'filtered')
datadir_old = op.join(os.getcwd(), 'data', 'transformedData')

with open(op.join(datadir, 'mombudtrans_new.pkl'), 'rb') as inpt:
    dfmb = pickle.load(inpt)  # has columns base, neck, tip, media, bud, mom

with open(op.join(datadir_old, 'mombudtrans.pkl'), 'rb') as inpt:
    dfmb_o = pickle.load(inpt)  # has columns base, neck, tip, media, bud, mom

rejectfold = op.join(datadir, os.pardir, 'reject')
reject = wr.swalk(rejectfold, '*png', stop=-4)

try:
    filext = "*vtk"
    vtkF = wr.ddwalk(datadir, filext, stop=-4)
except LookupError:
    sys.exit("error filetypes %s not found in %s" % (filext, datadir))

try:
    filext = "*vtk"
    vtkF_old = wr.swalk(datadir_old, filext, stop=-4)
except LookupError:
    sys.exit("error filetypes %s not found in %s" % (filext, datadir))


filekeys_old = {item: vtkF_old[item] for item
                in sorted(vtkF_old.keys()) if item.split('_')[0] != 'YPD'}

filekeys = {item: vtkF[media][item] for media
            in sorted(vtkF.keys()) for item
            in sorted(vtkF[media].keys())}

filekeys_f = {f:filekeys[f] for f in filekeys if f not in reject}
filekeys_f.update(filekeys_old)  # add YPE to dict
# dataframe of neck, mom and bud tip positions, bud and mom volumes
dfmb = dfmb.append(dfmb_o[dfmb_o.media != 'YPD'])

 #=============================================================================
 # Dataframe and binning setup
 #=============================================================================
# bins for binning the bud progression ratio
binsbudprog = np.r_[np.arange(0, 1.1, .1), 2]
binsaxis = np.linspace(0., 1., 6)  # pos. along mom/bud cell
binsaxisbig = np.linspace(0, 1., 21)  # position along whole cell
binsvolbud = np.linspace(0, 40, 5)  # vol binning for bud
binsvolmom = np.array([0, 30, 40, 80.])  # vol binning for mom

# dataframe for budding progression and budratio, size distribution , fra Δψ
cellall = pd.DataFrame(columns=['mom', 'bud'])

# dataframe for Δψ distributino along mom/bud cell axis
cellposmom = pd.DataFrame()
cellposbud = pd.DataFrame()

# dataframe for average Δψ around the neck region
neckregion = pd.DataFrame()

 #=============================================================================
 # compute Δψ distrbution along cellaxis for each ind cell and collect/append
 # to the dataframes
 #=============================================================================
for key in sorted(filekeys_f)[:]:

    # returns Dataframe of pos along x-axis for inidivual mom and bud cell
    cell = vf.cellpos(filekeys_f[key], dfmb)

    # bin the dataframe according to binxaxis
    cell['ind_cell_pos'] = vf.bincell(cell, 'indcell_xaxis', binsaxis)

    # Series of average Δψ (scaled to cell minmax values, DY_minmax)
    Xmom = cell.ix[cell['type'] == 'mom'].groupby('ind_cell_pos').DY.mean()
    Xbud = cell.ix[cell['type'] == 'bud'].groupby('ind_cell_pos').DY.mean()

    # pos along x-axis for the whole cell
    cell['whole_cell_pos'] = vf.bincell(cell, 'wholecell_xaxis', binsaxisbig)

    # Series of Δψ scaled to min-max of the MOM-BUD cell AXIS
    scaled_dy_wholecell = cell.groupby('whole_cell_pos').DY.mean()

    Xmom = vf.scaleminmax(Xmom, scaled_dy_wholecell)
    Xbud = vf.scaleminmax(Xbud, scaled_dy_wholecell)
    Xbud.name = key
    Xmom.name = key
    medianDY = cell.groupby('type').median().DY
    medianDY.name = key
    cellall = cellall.append(medianDY)
    cellposbud = cellposbud.append(Xbud)
    cellposmom = cellposmom.append(Xmom)
    # temp dict of mean Δψ at +- range of dist from budneck
    tempdic = {dist: vf.neckDY(cell, cell.neckpos, dist)
               for dist in [.15, .3, .5]}
    temp = pd.DataFrame({'bud': pd.Series({k: tempdic[k][0] for k in tempdic}),
                         'mom': pd.Series({k: tempdic[k][1] for k in tempdic}),
                         'cellname': key})
    temp['dist'] = temp.index
    temp.set_index('cellname', inplace=True)
    neckregion = neckregion.append(temp, ignore_index=False)

# cleanup and add. labels for dataframes
cellall['budvol'] = dfmb.bud
cellall['momvol'] = dfmb.mom
cellall = cellall.reset_index()
cellall['type'] = cellall['index'].apply(lambda x: x.split('_')[0])
cellposbud = cellposbud.reset_index()
cellposmom = cellposmom.reset_index()
cellposbud = pd.concat([cellposbud, cellall.ix[:, ['type']]], axis=1)
cellposmom = pd.concat([cellposmom, cellall.ix[:, ['type']]], axis=1)

cellall['frac'] = cellall.ix[:, 'bud'] / cellall.ix[:, 'mom']
Q = cellall.groupby('type').quantile(.90)  # 90th percentile of each cols

#  q90 = 90th percentile bud volume of each media type
cellall['q90'] = cellall.type.apply(lambda x: Q.ix[x].budvol)
gt90 = cellall[cellall['budvol'] > cellall['q90']]
meangt90 = gt90.groupby('type').budvol.mean()
cellall['mean90'] = cellall.type.apply(lambda x: meangt90.ix[x])

#  budvolratio is based on the largest 10% cells
cellall['budvolratio'] = cellall.budvol / cellall.q90
cellposbud['budvol'] = cellall['budvol']
cellposmom['momvol'] = cellall['momvol']

cellposbud['binvol'] = vf.bincell(cellposbud, 'budvol', binsvolbud)
cellposmom['binvol'] = vf.bincell(cellposmom, 'momvol', binsvolmom)
#
# =============================================================================
# cells binned by budding progression
# =============================================================================
cellall['bin_budprog'] = vf.bincell(cellall, 'budvolratio', binsbudprog)
cellall['binbudvol'] = cellposbud['binvol']

# reject super large cells
rejectlist = cellposmom.ix[(np.asarray(cellposmom.momvol) > 100) &
                           (cellposmom.type != 'YPD'), 'index']
cellall = cellall.ix[~ cellall.ix[:, 'index'].isin(rejectlist)]
cellposmom = cellposmom.ix[~cellposmom.ix[:, 'index'].isin(rejectlist)]
cellposbud = cellposbud.ix[~cellposbud.ix[:, 'index'].isin(rejectlist)]

# =============================================================================
# Distribution of bud and mom volumes
# =============================================================================
budvol = cellall.ix[:, ['budvol', 'type', 'N']]
momvol = cellall.ix[:, ['momvol', 'type', 'N']]
budvol['N'] = budvol.groupby("type").transform('count')
momvol['N'] = budvol.groupby("type").transform('count')
N = budvol.groupby("type").count()
N = N.budvol.to_dict()  # dict to hold counts of each type
col_ord = ['MFB1', 'NUM1', 'YPT11', 'WT', 'YPE', 'YPL', 'YPR']

def label_n(handle, labeldic):
    """
    modifies title on facetgrid to include labeldic

    Parameters
    ----------

    handle : FacetGrid ref
        handle to FacetGrid obj

    labeldic : dict
        dictionary of text labels to be added to handle's title

    """
    for ax in handle.axes.flat:
        oldtitle = ax.get_title().split('=')[1].strip()
        ax.set_title('%s, N=%d' % (oldtitle, labeldic[oldtitle]))

sns.set_style('whitegrid')
with sns.plotting_context('talk', font_scale=1.1):
    g = sns.FacetGrid(budvol,
                      col="type",
                      col_wrap=4,
                      hue="type",
                      col_order=col_ord)
    g = (g.map(sns.distplot, "budvol")).set(xlim=(0.))
    label_n(g, N)
    g.savefig(op.join(datadir, 'budsize_dist.png'))

    h = sns.FacetGrid(momvol,
                      col="type",
                      col_wrap=4,
                      hue="type",
                      col_order=col_ord)
    h = (h.map(sns.distplot, "momvol")).set(xlim=(0.))
    label_n(h, N)
    h.savefig(op.join(datadir, 'momsize_dist.png'))

# =============================================================================
# Progression of Δψ as move along the bud axis
# =============================================================================
bigbinsmom = pd.melt(cellposmom,
                     id_vars=['type', 'binvol'],
                     var_name='mom axis position',
                     value_name=r'$\Delta\Psi$ scaled gradient',
                     value_vars=binsaxis.tolist())
bigbinsmom = bigbinsmom.dropna()
bigbinsbud = pd.melt(cellposbud,
                     id_vars=['type', 'binvol'],
                     var_name='bud axis position',
                     value_name=r'$\Delta\Psi$ scaled gradient',
                     value_vars=binsaxis.tolist())
bigbinsbud = bigbinsbud.dropna()

with sns.plotting_context('talk', font_scale=1.):
    h = sns.FacetGrid(bigbinsmom,
                      col="type",
                      hue='type',
                      col_wrap=4,
                      sharex=True,
                      col_order=col_ord)
    h = h.map(sns.pointplot,
              'mom axis position',
              r'$\Delta\Psi$ scaled gradient').set(ylim=(0, 1.))
    h.savefig(op.join(datadir, 'mom_cell_dy.png'))

    m0 = sns.FacetGrid(bigbinsbud,
                       row="type",
                       col="binvol",
                       hue='type',
                       row_order=col_ord,
                       col_order=binsvolbud[1:])

    m0 = m0.map(sns.pointplot,
                'bud axis position',
                r'$\Delta\Psi$ scaled gradient').set(ylim=(0, 1.), )
    m0.savefig(op.join(datadir, 'bud_cell_dy_facetted.png'))
    # without facetting by budvol
    m1 = sns.FacetGrid(bigbinsbud,
                       col="type",
                       hue='type',
                       col_wrap=4,
                       col_order=col_ord)

    m1 = m1.map(sns.pointplot,
              'bud axis position',
              r'$\Delta\Psi$ scaled gradient').set(ylim=(0, 1.))
    m1.savefig(op.join(datadir, 'bud_cell_dy.png'))
# =============================================================================
# frac Δψ as function of budratio
# =============================================================================
with sns.plotting_context('talk'):
    _, ax2 = plt.subplots(1, 1)
    h = (sns.pointplot(x='bin_budprog',
                      y='frac',
                      hue='type',
                      data=cellall.dropna(),
                      ax=ax2))
    h.set(ylim=(0,3),
          title=u"Δψ vs bud progression\n ",
          xlabel="bud progression",
          ylabel=u"Δψ bud/Δψ mom")
    leg = h.get_legend()
    plt.setp(leg, bbox_to_anchor=(0.85,0.7, .3,.3))
    plt.savefig(op.join(datadir, "DY vs bud progression.png"))


    p = sns.FacetGrid(cellall.dropna(),
                      col="type",
                      hue='type',
                      col_wrap=4,
                      col_order=col_ord)
    p = p.map(sns.pointplot, 'bin_budprog', 'frac')
    p.savefig(op.join(datadir, "DY_bud_prog_facetted.png"))
# =============================================================================
#     Δψ at the bud neck region
# =============================================================================
with sns.plotting_context('talk'):
    A = pd.melt(neckregion,
                id_vars=['dist'],
                value_vars=['bud', 'mom'])
A.dropna(inplace=True)
with sns.plotting_context('talk', font_scale=1.4):
    _, ax1 = plt.subplots(1, 1)
    q1 = sns.barplot(x='dist', y='value',
                    hue='variable',
                    data=A,
                    ax=ax1)
    leg = q1.get_legend()
    plt.setp(leg, bbox_to_anchor=(0.85,0.7, .3,.3))
    plt.savefig(op.join(datadir, "neckregionDY.png"))

#  ============================================================================
#  frac Δψ violinplots by media
#  ============================================================================
BIG = pd.melt(cellall,
              id_vars=['type'],
              value_vars=['frac'])
groups = BIG.groupby('type')

with sns.plotting_context('talk'):
    _, ax4 = plt.subplots(1, 1)
    j = sns.violinplot(x='type',
                       y='value',
                       hue='type',
                       data=BIG,
                       order=col_ord,
                       ax=ax4)
    j.set_ylim(0, 2.5)
    j.get_legend().set_visible(False)

    g = sns.stripplot(x='type',
                      split=True,
                      y='value',
                      hue='type',
                      order=col_ord,
                      data=BIG,
                      jitter=.15,
                      ax=ax4)
    g.get_legend().set_visible(False)
    labels = [xl.get_text().strip() for xl in  j.axes.get_xticklabels()]
    new_labels = ['%s\n N=%d'% (old_lab, N[old_lab]) for old_lab in labels]
    j.axes.set_xticklabels(new_labels)
    plt.savefig(op.join(datadir, "violin_fracDY.png"))
# ============================================================================
# violinplot mom vs bud Δψ scaled

BIG2 = pd.melt(cellall,
               id_vars=['type'],
               value_vars=['mom', 'bud'])

with sns.plotting_context('talk', font_scale=1.):
    _, ax3 = plt.subplots(1, 1)
    h = sns.violinplot(x='type',
                       y='value',
                       hue='variable',
                       order=col_ord,
                       data=BIG2,
                       ax=ax3)
    sns.stripplot(x='type',
                  y='value',
                  hue='variable',
                  jitter=.15,
                  size=4,
                  order=col_ord,
                  data=BIG2,
                  ax=ax3)
    h.set_ylim(0, 1.)
    h.get_legend().set_visible(False)

    labels = [xl.get_text().strip() for xl in  h.axes.get_xticklabels()]
    new_labels = ['%s\n N=%d'% (old_lab, N[old_lab]) for old_lab in labels]
    h.axes.set_xticklabels(new_labels)
    plt.savefig(op.join(datadir, "Violin Mom_Bud_DY.png"))
# =============================================================================
# frac Δψ as function of budvol
# =============================================================================
# with sns.plotting_context('talk', font_scale=1.4):
##    _, ax10 = plt.subplots(1, 1)
###    g = sns.FacetGrid(cellall.dropna(), col="type")
###    g = g.map(sns.regplot, "budvol", "frac")
##    datacell = cellall[cellall.bud <= bins2[-1]]
# h = sns.pointplot(x='binbudratio',
# y='bud',
# hue='type',
# data=datacell.dropna(),
# ax=ax10)
# h.get_legend().set_visible(False)
##
# for i in ['YPD', 'YPE', 'YPL', 'YPR']:
##        data = cellall[(cellall.type == i) & (cellall.frac < 2)]
# slope, _, r, p, _ = sp.linregress(data['budvol'],
# data['frac'])
# print 'slope= %6.4f r=%6.4f p=%6.4f' % (slope, r, p)
#
# =============================================================================
# Dy as budneckregion and budratio
# =============================================================================
# with sns.plotting_context('talk', font_scale=1.4):
##    _, ax2 = plt.subplots(1, 1)
# h = sns.pointplot(x='bin_budprog',
# y='DYneck',
# hue='type',
# data=cellall.dropna(),
# ax=ax2)
# h.get_legend().set_visible(False)
#
#
# with sns.plotting_context('talk', font_scale=1.4):
##    _, ax1 = plt.subplots(1, 1)
# h = sns.pointplot(x='posx',
# y='DY',
# ci=None,
# markers='o',
# join=False,
# hue='type',
# data=cell,
# size=1,
# ax=ax1)
# h.get_legend().set_visible(False)
##    h.set_xticks(np.linspace(cell.pos.min(), cell.pos.max(),11))
##    h.set_xticklabels(np.arange(0, 1.1 ,.1))
#
# ==============================================================================
# budratio
# ==============================================================================
##c2 = cellall.drop(cellall.index[[5, 15, 63, 46]])
# slope, _, r, p, std_err = sp.linregress(c2.ix[:, 'budratio'],
# c2.ix[:, 'neck'])
# with sns.plotting_context('talk', font_scale=1.4):
##    _, ax5 = plt.subplots(1, 1)
# h = sns.regplot(x='budratio',
# y='neck',
# data=c2[c2.neck>0.505],
# ax=ax5)
# h.get_legend().set_visible(False)
