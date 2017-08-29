from ta.mesh import Mesh
from ta.db import Database
import os
from os import path
import logging
import argparse

from mesh import meshstats
from clusters import clusterstats

def main():
    parser = argparse.ArgumentParser(prog='clusters')
    parser.add_argument('-d', dest='db', help='Database File')
    parser.add_argument('--meshstats', dest='meshstats', action='store_true')
    parser.add_argument('--clusterstats', dest='clusterstats', action='store_true')
    parser.add_argument('vtudir', help='VTU data directory')
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        level=logging.DEBUG
    )
    args = parser.parse_args()

    db = Database(args.db)

    for d, _, fs in os.walk(args.vtudir):
        for fn in fs:
            if fn.endswith(".vtu"):
                filename = path.join(d, fn)
                m = Mesh(filename)
                if args.meshstats:
                    meshstats(db, m)
                if args.clusterstats:
                    clusterstats(db, m)
                db.conn.commit()
