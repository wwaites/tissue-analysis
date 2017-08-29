import sqlite3
import logging
log = logging.getLogger("db")

tables = {
    "meshfiles": """
        CREATE TABLE meshfiles (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            size INTEGER,
            entropy DOUBLE
        );
    """,
    "clusters": """
        CREATE TABLE clusters (
            mesh INTEGER REFERENCES meshfiles(id) ON DELETE CASCADE,
            type DOUBLE,
            size INTEGER
        )
    """,
}

class Database(object):
    def __init__(self, dbfile):
        self.conn = sqlite3.connect(dbfile)
        self.init_schema()

    def init_schema(self):
        for name, create in tables.items():
            cur = self.conn.cursor()
            try:
                cur.execute("SELECT * FROM %s" % name)
            except sqlite3.OperationalError:
                log.info("creating table %s", name)
                cur.execute(create)
        self.conn.commit()

    def meshfile(self, filename):
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM meshfiles WHERE name=?;", (filename,))
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO meshfiles(name) VALUES(?);", (filename,))
            cur.execute("SELECT id FROM meshfiles WHERE name=?;", (filename,))
            row = cur.fetchone()
        return row[0]
