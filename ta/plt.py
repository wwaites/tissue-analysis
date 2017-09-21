import argparse
from glob import glob
from os import path, system
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
