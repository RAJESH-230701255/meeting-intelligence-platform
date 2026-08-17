import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    conn = psycopg2.connect(user='postgres', password='postgres', host='localhost', port='5432')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'meeting_intelligence_db'")
    exists = cur.fetchone()
    if not exists:
        cur.execute('CREATE DATABASE meeting_intelligence_db')
        print('Database created successfully')
    else:
        print('Database already exists')
    cur.close()
    conn.close()
except Exception as e:
    print('Failed to connect or create DB:', e)
