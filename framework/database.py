import psycopg2


class Database:
    """One reusable PostgreSQL connection for an entire report run."""

    def __init__(self, config):
        self.config = config
        self.conn = None

    def connect(self):
        db = self.config["database"]
        self.conn = psycopg2.connect(
            dbname=db["database"],
            user=db["user"],
            password=db.get("password", ""),
            host=db["host"],
            port=db.get("port", 5432),
        )
        return self.conn

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def execute(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)

    def fetchone(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def fetchall(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
