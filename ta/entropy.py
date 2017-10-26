import argparse
from mesh import VtuMesh, DictMesh
import json
from math import log

def paths(mesh, n):
    def _paths(c, l, head):
        if l == 0:
            yield tuple(head)
            return
        for n in mesh.neighbours(c):
            if n in head: continue
            copy = list(head)
            copy.append(n)
            for p in _paths(n, l-1, copy):
                yield p

    for c in range(len(mesh)):
        for p in _paths(c, n-1, [c]):
            yield p

def colour(mesh, path):
    return tuple(mesh.types[i] for i in path)

def distribution(mesh, ps):
    Xmap = {}
    for p in [colour(mesh, p) for p in ps]:
        Xmap[p] = Xmap.get(p, 0) + 1
    total = sum(Xmap.values())
    def prob(x):
        return float(x)/total
    dist = {}
    for k, v in Xmap.items():
        dist[k] = prob(v)
    return dist

def entropy(dist):
    return -1 * sum(p * log(p, 2) for p in dist.values())
 
def relentropy(dist, rel):
    keys = set(dist.keys()).union(rel.keys())
    rent = 0.0
    for k in keys:
        p = dist.get(k, 0.0)
        q = rel.get(k, 0.0)
        rent += p * log(p/q, 2)
    return rent

def main():
    parser = argparse.ArgumentParser(prog='pentropy')
    parser.add_argument('-n', dest='number', default=2, type=int, help='Path entropy series term')
    parser.add_argument('-r', dest='relative', default=None,
                        help='reference for relative entropy')
    parser.add_argument('input', help='input file')

    args = parser.parse_args()


    if args.input.endswith('.vtu'):
        mesh = VtuMesh(args.input)
    else:
        with open(args.input) as fp:
            data = json.loads(fp.read())
        mesh = DictMesh(data)

    dist = distribution(mesh, paths(mesh, args.number))

    if args.relative is not None:
        if args.relative.endswith('.vtu'):
            rel = VtuMesh(args.relative)
        else:
            with open(args.relative) as fp:
                data = json.loads(fp.read())
            rel = DictMesh(data)
        rdist = distribution(rel, paths(rel, args.number))

        print relentropy(dist, rdist)
    else:
        print entropy(dist)


