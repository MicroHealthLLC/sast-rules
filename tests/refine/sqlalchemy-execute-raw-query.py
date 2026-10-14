# Fixture for the sqlalchemy-execute-raw-query refinement; never executed.
import psycopg2
from psycopg2 import sql
from psycopg2 import sql as pgsql


def schema(cur, s, x, opts):
    # ok: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
    cur.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(s)))
    # ok: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
    cur.execute(psycopg2.sql.SQL("DROP TABLE {}").format(sql.Identifier(s)))
    # ok: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
    cur.execute(sql.SQL("SELECT * FROM ") + sql.Identifier(s))
    stmt = pgsql.SQL("CREATE EXTENSION IF NOT EXISTS {};").format(pgsql.Identifier(s))
    # ok: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
    cur.execute(stmt)
    # ruleid: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
    cur.execute(sql.SQL("CREATE ROLE {} " + opts).format(sql.Identifier(s)))
    # ruleid: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query ruleid: mh.opengrep.python.lang.security.audit.formatted-sql-query.formatted-sql-query
    cur.execute("SELECT * FROM t WHERE a = '%s'" % x)
    # ruleid: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query ruleid: mh.opengrep.python.lang.security.audit.formatted-sql-query.formatted-sql-query
    cur.execute(f"SELECT * FROM t WHERE a = '{x}'")
    other = "SELECT * FROM t WHERE a = '{}'".format(x)
    # ruleid: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query ruleid: mh.opengrep.python.lang.security.audit.formatted-sql-query.formatted-sql-query
    cur.execute(other)
