import argparse
from glob import glob
from os import path, system
from sys import exit
from mesh import VtuMesh, DictMesh
from PIL import Image, ImageDraw
from ta.colours import colours
import json
import re

def main():
    parser = argparse.ArgumentParser(prog='eplot')
    parser.add_argument('-o', dest='output', help='output directory')
    parser.add_argument('data', help='data spec (file prefix, up to -pop)')

    args = parser.parse_args()

    pop_re = re.compile(r'%s-pop([0-9]+\.[0-9]+).*.entropy.dat' % args.data)
    def pop(f):
        m = pop_re.match(f)
        if m is not None:
            return f, m.groups()[0]
    pops = list(pop(f) for f in glob("%s-pop*.entropy.dat" % (args.data)))
    pops.sort(lambda x, y: cmp(x[1], y[1]))

    base = path.basename(args.data)

    def plotline(pop):
        dat, pop = pop
        return '\t"%s" using 1:2 with lines title "%s"' % (dat, pop)

    plot = path.join(args.output, "%s.plt" % base)
    with open(plot, "w") as fp:
        fp.write("""
set terminal png
set output "%s.png"

plot \\
""" % path.join(args.output, base))
        fp.write(", \\\n".join(plotline(pop) for pop in pops))
        fp.write("\n")
    system("gnuplot %s" % plot)

def mesh():
    parser = argparse.ArgumentParser(prog='pmesh')
    parser.add_argument('-g', dest='geometry', default="640x480", help='image geometry')
    parser.add_argument('-f', dest='format', default='vtu',
                        help='input format, VTU or JSON')
    parser.add_argument('-o', dest='outline', action='store_true', default=False,
                        help='show cell outlines')
    parser.add_argument('-i', dest='index', action='store_true', default=False,
                        help='show cell indices')
    parser.add_argument('-c', dest='colours', type=int, default=None,
                        help='generate a colour plot')
    parser.add_argument('input', help='input file')
    parser.add_argument('output', help='output file')

    args = parser.parse_args()
    gre = re.match(r"^([0-9]+)x([0-9]+)$", args.geometry)
    if gre is None:
        print("invalid geometry: %s" % args.geometry)
        exit(255)

    try:
        _, ext = args.output.rsplit(".", 1)
    except ValueError:
        print("invalid image filename: %s" % args.output)
        exit(255)

    width, height = map(int, gre.groups())
    image = Image.new("RGB", (width, height), (255, 255, 255))


    if args.format.lower() == 'vtu':
        mesh = VtuMesh(args.input)
    else:
        with open(args.input) as fp:
            data = json.loads(fp.read())
        mesh = DictMesh(data)

    xmin, xmax, ymin, ymax = 2**32, 0, 2**32, 0
    for gon in mesh.polygons:
        for x, y in gon:
            if x < xmin: xmin = x
            if x > xmax: xmax = x
            if y < ymin: ymin = y
            if y > ymax: ymax = y

    def scale((x, y)):
        return (
            int(width * (x - xmin) / (xmax - xmin)),
            int(height * (y - ymin) / (ymax - ymin))
            )

    mint, maxt = 2**32, 0
    for f in mesh.types:
        if f < mint: mint = f
        if f > maxt: maxt = f

    def cmap(f):
        c = int(args.colours * (f - mint)/(maxt - mint))
        return colours[c]

    def gmap(f):
        g = int(255 * (f - mint)/(maxt - mint))
        return (g, g, g)

    def onekind(f):
        return (255, 255, 255)

    def mute(c):
        return tuple( ((c + 128) % 255) for c in cmap(f) )

    if mint == maxt:
        cmap = onekind
    if args.colours is None:
        cmap = gmap

    canvas = ImageDraw.Draw(image)
    kv = {}

    def centroid(gon):
        xs = [x[0] for x in gon]
        ys = [y[1] for y in gon]
        return (sum(xs)/len(gon), sum(ys)/len(gon))

    for i in range(len(mesh)):
        gon = mesh.polygons[i]
        flavour = mesh.types[i]
        if args.outline:
            kv["outline"] = mute(cmap(flavour))
        canvas.polygon(map(scale, gon), fill=cmap(flavour), **kv)
        if args.index:
            canvas.text(scale(centroid(gon)), str(i), (0,0,0))

    image.save(args.output, ext.upper())
