from vtk import *
from scipy.sparse import dok_matrix
from math import log
import numpy as np
from sys import argv, stdout

class TissueGridException(Exception):
    "Something has gone wrong"

class SparseArray(dict):
    def __getitem__(self, i):
        self.get(i, 0)
class SparseMatrix(dict):
    def __getitem__(self, i):
        self.get(i, SparseArray())

def isDist(a):
    return abs(1.0 - sum(a)) < 0.1

def memoize(f):
    def m(self):
        n = "__" + f.__name__ + "_memo__"
        if not hasattr(self, n):
            setattr(self, n, f(self))
        return getattr(self, n)
    return property(m)

class Mesh(object):
    def __init__(self, file_name):
        reader = vtkXMLUnstructuredGridReader()
        reader.SetFileName(file_name)
        reader.Update()
        self.ug = reader.GetOutput()

    @memoize
    def shape(self):
        return (len(self), len(self))
    def __len__(self):
        return self.ug.GetNumberOfCells()

    @memoize
    def types(self):
        celldata = self.ug.GetCellData()
        for i in range(celldata.GetNumberOfArrays()):
            data = celldata.GetArray(i)
            if data.GetName() == "cell type":
                tuples = [data.GetTuple(c) for c in
                          range(data.GetNumberOfTuples())]
                return np.array(list(t for t, in tuples))
        raise TissueGridException("No data about cell types")

    @memoize
    def adjacencies(self):
        def getNeighbours(c):
            neighbours = []
            points = vtkIdList()
            self.ug.GetCellPoints(c, points)
            for i in range(points.GetNumberOfIds()):
                plist = vtkIdList()
                plist.InsertNextId(points.GetId(i))
                nlist = vtkIdList()

                self.ug.GetCellNeighbors(c, plist, nlist)
                for j in range(nlist.GetNumberOfIds()):
                    neighbours.append(nlist.GetId(j))
            return set(neighbours)

        adj = dok_matrix(self.shape, dtype=bool)
        for i in range(len(self)):
            for j in getNeighbours(i):
                adj[i,j] = True
        return adj

    @memoize
    def demographics(self):
        typemap = {}
        for t in self.types:
            typemap[t] = typemap.get(t, 0) + 1
        total = sum(typemap.values())
        ks = typemap.keys()
        ks.sort()
        demo = []
        for k in ks:
            demo.append(float(typemap[k])/total)
        assert isDist(demo)
        return np.array(demo)

    @memoize
    def neighbourStats(self):
        pr = {}
        for i in range(len(self)):
            itype = self.types[i]
            typestats = pr.setdefault(itype, {})
            for j in self.neighbours(i):
                ntype = self.types[j]
                typestats[ntype] = typestats.get(ntype, 0) + 1
        npr = []
        ks = pr.keys()
        ks.sort()
        for i in ks:
            p = []
            total = sum(pr[i].values())
            js = pr[i].keys()
            js.sort()
            for j in js: 
                p.append(float(pr[i][j])/total)
            assert isDist(p)
            npr.append(p)
        return np.array(npr)

    @memoize
    def entropy(self):
        demo = self.demographics
        nstats = self.neighbourStats
        dist = []
        for i in range(len(demo)):
            for j in range(len(demo)):
                dist.append(demo[i] * nstats[i,j])
        return -1 * sum(p * log(p, 2) for p in dist)

    def neighbours(self, i):
        return [j for (_, j) in self.adjacencies[i, :].keys()]

    def _cluster(self, i, seen = None, ctype = None):
        if seen is None:
            seen = set()
        if ctype is None:
            ctype = self.types[i]
        if i in seen:
            return seen
        if self.types[i] == ctype:
            seen.add(i)
            for n in self.neighbours(i):
                new = self._cluster(n, seen, ctype)
                seen = seen.union(new)
        return seen

    @memoize
    def clusters(self):
        clusters = []
        seen = set()
        for i in range(len(self)):
            if i in seen: continue
            members = self._cluster(i)
            seen = seen.union(members)
            clusters.append(Cluster(self.types[i], members))
        return clusters

    @memoize
    def clusterCounts(self):
        cc = {}
        for c in self.clusters:
            cc.setdefault(c.ctype, []).append(len(c.members))
        return cc

class Cluster(object):
    def __init__(self, ctype, members):
        self.ctype = ctype
        self.members = members
    def __str__(self):
        return "Cluster(%s, %s)" % (self.ctype, self.members)
    def __len__(self):
        return len(self.members)

for f in argv[1:]:
    m = Mesh(f)
    stdout.write("%s\t%s" % (f, m.entropy))
    cc = m.clusterCounts
    ctypes = cc.keys()
    ctypes.sort()
    for t in ctypes:
        stdout.write("\t%f\t%f" % (np.mean(cc[t]), np.std(cc[t])))
    print

