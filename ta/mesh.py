import argparse, json
from vtk import *
from scipy.sparse import dok_matrix
import numpy as np
from math import sqrt, pi, cos
from sys import argv, stdout
from math import *
import logging
import re
log = logging.getLogger("mesh")

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
    def __len__(self):
        return len(self.types)
    def neighbours(self, i):
        return [j for (_, j) in self.adjacencies[i, :].keys()]


class VtuMesh(Mesh):
    def __init__(self, file_name):
        self.filename = file_name
        reader = vtkXMLUnstructuredGridReader()
        reader.SetFileName(file_name)
        reader.Update()
        self.ug = reader.GetOutput()

    def __str__(self):
        return "VtuMesh(%s)" % repr(self.filename)

    @memoize
    def shape(self):
        return (len(self), len(self))
    def __len__(self):
        return self.ug.GetNumberOfCells()

    @property
    def timestamp(self):
        m = re.match(r"^.*[^0-9]([0-9]*)\.vtu$", self.filename)
        time, = m.groups()
        return time

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
    def polygons(self):
        def _poly():
            for i in range(len(self)):
                points = vtkIdList()
                self.ug.GetCellPoints(i, points)
                gon = []
                for p in range(points.GetNumberOfIds()):
                    (x, y, _) = self.ug.GetPoint(points.GetId(p))
                    gon.append((x, y))
                yield gon
        return list(_poly())

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
        from math import log 
        demo = self.demographics
        nstats = self.neighbourStats
        dist = []
        for i in range(len(demo)):
            for j in range(len(demo)):
                dist.append(demo[i] * nstats[i,j])
        return -1 * sum(p * log(p, 2) for p in dist)

class DictMesh(Mesh):
    def __init__(self, data):
        self.__dict__.update(data)
        if isinstance(self.shape, list):
            self.shape = tuple(self.shape)
        if isinstance(self.adjacencies, list):
            keys = self.adjacencies
            self.adjacencies = dok_matrix(self.shape, dtype=bool)
            for (i,j) in keys: self.adjacencies[i,j] = True

def mklattice(n, m):
    R = sqrt(2.0 / (3*sqrt(3)))
    r = R*cos(pi/6)
    def hexagon(x, y):
        for angle in [0, pi/3, 2*pi/3, pi, 4*pi/3, 5*pi/3]:
            yield (x + R + cos(angle)*R, y + sin(angle)*R)

    def ident(i, j):
        return j*n + i

    lattice = {
        "types": [],
        "polygons": [],
        "shape": (n*m,n*m),
        "adjacencies": dok_matrix((n*m,n*m), dtype=bool)
    }
    def inbox(i):
        return i >= 0 and i < n*m
    def leftof(i, j):
        return i % n >= j % n
    def rightof(i, j):
        return i % n <= j % n
    for j in range(m):
        for i in range(n):
            lattice["types"].append(0)
            xshift = 0 if j % 2 == 0 else 1.5*R
            xoffset = i*(2*R + R) + xshift
            yoffset = j*r + r
            lattice["polygons"].append(list(hexagon(xoffset, yoffset)))

            cid = ident(i,j)

            nn  = cid - 2*n
            ss  = cid + 2*n

            evenrow = j % 2 == 0
            evencol = i % 2 == 0
            if evenrow:
                se = cid + n
                nw = cid - n - 1
            else:
                se = cid + n + 1
                nw = cid - n
            sw = se - 1
            ne = nw + 1

            if inbox(nn): lattice["adjacencies"][cid, nn] = True
            if inbox(ne) and rightof(cid, ne): lattice["adjacencies"][cid, ne] = True
            if inbox(se) and rightof(cid, se): lattice["adjacencies"][cid, se] = True
            if inbox(ss): lattice["adjacencies"][cid, ss] = True
            if inbox(sw) and leftof(cid, sw): lattice["adjacencies"][cid, sw] = True
            if inbox(nw) and leftof(cid, nw): lattice["adjacencies"][cid, nw] = True

    return DictMesh(lattice)

def lattice():
    parser = argparse.ArgumentParser(prog='plattice')
    parser.add_argument('-n', dest='n', default="4", type=int, help='lattice size')
    parser.add_argument('-m', dest='m', default="16", type=int, help='lattice size')
    parser.add_argument('-p', dest='pattern', default="checker", help='lattice pattern')

    args = parser.parse_args()

    lat = mklattice(args.n, args.m)
    data = lat.__dict__
    data["adjacencies"] = data["adjacencies"].keys()

    if args.pattern == "stripes":
        for i in range(len(lat.types)):
            for k in range(3):
                if (i/args.m) % 3 == k:
                    lat.types[i] = k
    elif args.pattern == "tstripes":
        for i in range(len(lat.types)):
            for k in range(3):
                if (i/args.m/3) % 3 == k:
                    lat.types[i] = k
    elif args.pattern == "checker":
        for i in range(len(lat.types)):
            for k in range(3):
                if (i/args.n) % 3 == k:
                    lat.types[i] = k
    elif args.pattern == "random":
        from random import seed, choice
        from time import time
        seed(time())
        for i in range(len(lat.types)):
            lat.types[i] = choice([0,1,2])

    print json.dumps(data)

def meshstats(db, m):
    log.info("calculating mesh stats %s", m)
    mid = db.meshfile(m.filename)
    cur = db.conn.cursor()
    cur.execute("""
    UPDATE meshfiles
    SET time=?, size=?, entropy=?
    WHERE id=?
    """, (m.timestamp, len(m), m.entropy, mid))
