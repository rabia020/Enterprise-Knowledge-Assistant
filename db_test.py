import psycopg2

conn = psycopg2.connect(
    dbname="agent_memory",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)

cur = conn.cursor()

cur.execute("SELECT * FROM memory;")
rows = cur.fetchall()

print(rows)

conn.close()