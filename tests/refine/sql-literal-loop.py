# Fixture for the literal-loop refinement of the Python SQL pattern rules;
# never executed. Every `ok:` interpolates only a loop variable whose values are
# string literals written in the loop or in an assignment above it.
import psycopg2

conn = psycopg2.connect("")
cur = conn.cursor()


def roles(user, opts):
    for role in ("admin", "user"):
        # ok: mh.opengrep.python.lang.security.audit.formatted-sql-query.formatted-sql-query ok: mh.opengrep.python.lang.security.audit.sqli.psycopg-sqli.psycopg-sqli ok: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
        cur.execute(f'GRANT USAGE ON SCHEMA public TO "{role}"')
    schemas = [
        "cron", "graphql",
        "vault",
    ]
    for s in schemas:
        # ok: mh.opengrep.python.lang.security.audit.formatted-sql-query.formatted-sql-query ok: mh.opengrep.python.lang.security.audit.sqli.psycopg-sqli.psycopg-sqli ok: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
        cur.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE")
    pairs = [
        ("anon",          "NOLOGIN NOINHERIT"),
        ("authenticator", "LOGIN NOINHERIT"),
    ]
    for name, flags in pairs:
        # ok: mh.opengrep.python.lang.security.audit.formatted-sql-query.formatted-sql-query ok: mh.opengrep.python.lang.security.audit.sqli.psycopg-sqli.psycopg-sqli ok: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
        cur.execute(f'CREATE ROLE {name} {flags}')
    for table, label in [("wiki_pages", "Wiki"), ("auth.users", "Users")]:
        # ok: mh.opengrep.python.lang.security.audit.formatted-sql-query.formatted-sql-query ok: mh.opengrep.python.lang.security.audit.sqli.psycopg-sqli.psycopg-sqli ok: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
        cur.execute(f"SELECT count(*) FROM {table}")
    for role in ("admin", "user"):
        # ruleid: mh.opengrep.python.lang.security.audit.formatted-sql-query.formatted-sql-query ruleid: mh.opengrep.python.lang.security.audit.sqli.psycopg-sqli.psycopg-sqli ruleid: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
        cur.execute(f'GRANT "{role}" TO "{user}"')
    for role in ("admin", user):
        # ruleid: mh.opengrep.python.lang.security.audit.formatted-sql-query.formatted-sql-query ruleid: mh.opengrep.python.lang.security.audit.sqli.psycopg-sqli.psycopg-sqli ruleid: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
        cur.execute(f'CREATE ROLE "{role}"')
    for name, flags in [("anon", opts)]:
        # ruleid: mh.opengrep.python.lang.security.audit.formatted-sql-query.formatted-sql-query ruleid: mh.opengrep.python.lang.security.audit.sqli.psycopg-sqli.psycopg-sqli ruleid: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
        cur.execute(f'CREATE ROLE {name} {flags}')
    for role in user.split(","):
        # ruleid: mh.opengrep.python.lang.security.audit.formatted-sql-query.formatted-sql-query ruleid: mh.opengrep.python.lang.security.audit.sqli.psycopg-sqli.psycopg-sqli ruleid: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
        cur.execute(f'DROP ROLE "{role}"')
    # ruleid: mh.opengrep.python.lang.security.audit.formatted-sql-query.formatted-sql-query ruleid: mh.opengrep.python.lang.security.audit.sqli.psycopg-sqli.psycopg-sqli ruleid: mh.opengrep.python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query
    cur.execute(f"SELECT * FROM t WHERE a = '{user}'")
