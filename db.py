import psycopg2


DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "agent_memory",
    "user": "postgres",
    "password": "postgres"
}


def get_connection():
    """
    Returns a PostgreSQL connection.
    """
    return psycopg2.connect(**DB_CONFIG)