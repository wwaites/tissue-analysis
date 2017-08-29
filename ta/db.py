import sqlite3
import logging
import re
from os import path
log = logging.getLogger("db")

tables = {
    "meshfiles": """
        CREATE TABLE meshfiles (
            id INTEGER PRIMARY KEY,
            file VARCHAR,
            name VARCHAR,
            time VARCHAR,
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
        cur.execute("SELECT id FROM meshfiles WHERE file=?;", (filename,))
        row = cur.fetchone()
        if row is None:
            basename = path.basename(filename)
            m = re.match(r"^.*[^0-9]([0-9]*)\.vtu$", basename)
            time, = m.groups()
            cur.execute(
                "INSERT INTO meshfiles(file, name, time) VALUES(?, ?, ?);",
                (filename, basename, int(time))
            )
            cur.execute("SELECT id FROM meshfiles WHERE file=?;", (filename,))
            row = cur.fetchone()
        return row[0]
