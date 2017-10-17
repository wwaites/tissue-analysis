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

def main():
    parser = argparse.ArgumentParser(prog='pentropy')
    parser.add_argument('-n', dest='number', default=2, type=int, help='Path entropy series term')
    parser.add_argument('-f', dest='format', default='vtu',
                        help='input format, VTU or JSON')
    parser.add_argument('input', help='input file')

    args = parser.parse_args()

    if args.format.lower() == 'vtu':
        mesh = VtuMesh(args.input)
    else:
        with open(args.input) as fp:
            data = json.loads(fp.read())
        mesh = DictMesh(data)

    Xmap = {}
    for path in [colour(mesh, p) for p in paths(mesh, args.number)]:
        Xmap[path] = Xmap.get(path, 0) + 1

    total = sum(Xmap.values())
    def prob(x):
        return float(x)/total

#    print map(prob, Xmap.values())
    print -1 * sum( p * log(p, 2) for p in map(prob, Xmap.values()) )

