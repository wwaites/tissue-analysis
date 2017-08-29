import logging

log = logging.getLogger("clusters")

class Cluster(object):
    def __init__(self, ctype, members):
        self.ctype = ctype
        self.members = members
    def __str__(self):
        return "Cluster(%s, %s)" % (self.ctype, self.members)
    def __len__(self):
        return len(self.members)

def _explore_cluster(mesh, i, seen = None, ctype = None):
    """
    Utility function that does a depth-first search to find
    the set of cells with the same type as the i-th cell
    """
    if seen is None:
        seen = set()
    if ctype is None:
        ctype = mesh.types[i]
    if i in seen:
        return seen
    if mesh.types[i] == ctype:
        seen.add(i)
        for n in mesh.neighbours(i):
            new = _explore_cluster(mesh, n, seen, ctype)
            seen = seen.union(new)
    return seen

def clusters(mesh):
    """
    returns a list of all clusters in the mesh
    """
    clusters = []
    seen = set()
    for i in range(len(mesh)):
        if i in seen: continue
        members = _explore_cluster(mesh, i)
        seen = seen.union(members)
        clusters.append(Cluster(mesh.types[i], members))
    return clusters

def clusterstats(db, m):
    log.info("calculating cluster stats %s", m)
    mid = db.meshfile(m.filename)
    cur = db.conn.cursor()
    cur.execute("DELETE FROM clusters WHERE mesh=?", (mid,))
    for c in clusters(m):
        cur.execute(
            "INSERT INTO clusters(mesh, type, size) VALUES(?, ?, ?)",
            (mid, c.ctype, len(c))
        )
