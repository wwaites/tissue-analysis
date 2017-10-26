import argparse
import csv
import json
import pytess
from sys import float_info

def rows_csv(filename, delimiter):
    """
    Designed to read data from Elise' CSV files
    """
    for row in csv.reader(open(filename), delimiter=delimiter):
        if row[0].strip() == '': continue
        mean = float(row[2])
        x, y = float(row[6]), float(row[7])
        if mean > 300: kind = 0
        else: kind = 1
        yield ((x, y), kind)

def voronoi(rows):

    def edge(x0, x1):
        if x0[0] < x1[0]:
            return (x0, x1)
        if x0[0] > x1[0]:
            return (x1, x0)
        if x0[1] < x1[1]:
            return (x0, x1)
        if x0[1] > x1[1]:
            return (x1, x0)
        return (x0, x1)

    def edges(pts, first):
        if len(pts) == 1:
            yield edge(pts[0], first)
            return

        yield edge(pts[0], pts[1])

        if first is None:
            first = pts[0]
        for e in edges(pts[1:], first):
            yield e

    kindx = {}
    centroids = []
    for pt, kind in rows:
        kindx[pt] = kind
        centroids.append(pt)

    minx = float_info.max
    miny = float_info.max
    maxx = float_info.min
    maxy = float_info.min
    for (x, y) in centroids:
        if x < minx: minx = x
        if x > maxx: maxx = x
        if y < miny: miny = y
        if y > maxy: maxy = y

    def oob(polygon):
        for (x,y) in polygon:
            if x < minx: return True
            if x > maxx: return True
            if y < miny: return True
            if y > maxy: return True
        return False

    polyx = dict(pytess.voronoi(centroids))
    centroids = []
    polygons = []
    edgex = {}
    for centroid, poly in polyx.items():
        if centroid is None:
            continue
        if oob(poly):
            continue
        for e in edges(poly, None):
            edgex.setdefault(e, []).append(centroid)
        centroids.append(centroid)
        polygons.append(poly)

    n = len(centroids)
    lattice = {
        "types": list(kindx[c] for c in centroids),
        "polygons": polygons,
        "adjacencies": [],
        "shape": (n, n)
    }

    centx = {}
    for i in range(len(centroids)):
        centx[centroids[i]] = i

    for adj in edgex.values():
        if len(adj) == 2:
            i = centx[adj[0]]
            j = centx[adj[1]]
            lattice["adjacencies"].append((i,j))
            lattice["adjacencies"].append((j,i))

    return lattice

def main():
    parser = argparse.ArgumentParser(prog='pvoronoi')
    parser.add_argument('data', help='dataset')
    parser.add_argument('-d', default='\t', help="CSV delimiter")
    args = parser.parse_args()
    data = voronoi(rows_csv(args.data, delimiter=args.d))

    print json.dumps(data)
