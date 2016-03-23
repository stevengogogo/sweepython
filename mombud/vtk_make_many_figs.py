# -*- coding: utf-8 -*-
"""
Batch visualize skel and surface vtk files
"""
import sys
import os
import os.path as op
import matplotlib.pyplot as plt
from mayavi import mlab
from pipeline.make_networkx import makegraph as mg
from mombud.vtk_viz import vtkvizfuncs as vf
import wrappers as wr

# pylint: disable=C0103
plt.close('all')
mlab.close(all=True)
inputdir = op.join(os.getcwd(), 'input')
rawdir = op.join(os.getcwd(), 'output')


# filelist and graph list
if __name__ == '__main__':
    try:
        vtkF = wr.ddwalk(op.join(rawdir, 'normSkel'),
                         '*skeleton.vtk', start=5, stop=-13)
        vtkS = wr.ddwalk(op.join(inputdir, 'surfaceFiles'),
                         '*surface.vtk', stop=-12)

    except Exception:
            print "Error: check your filepaths"
            sys.exit()

    filekeys = {item: vtkF[media][item] for media
                in sorted(vtkF.keys()) for item
                in sorted(vtkF[media].keys())}

    for key in sorted(filekeys.keys())[2::25]:
        data = vf.callreader(vtkF[key[:3]][key])
        node_data, edge_data, nxgrph = mg(data, key)
        figone = mlab.figure(figure=key,
                             size=(800, 600),
                             bgcolor=(.15, .15, .15))
        vtkobj, _ = vf.cellplot(figone, filekeys[key])
        vf.rendsurf(vtkS[key[:3]][key[4:]])
        vf.labelbpoints(nxgrph, bsize=0.08, esize=0.08)
