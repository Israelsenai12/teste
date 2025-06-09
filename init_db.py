import psycopg2
import os

DB_NAME = os.environ.get("NEON_DB", "neondb")
DB_USER = os.environ.get("NEON_USER", "user")
DB_PASSWORD = os.environ.get("NEON_PASSWORD", "senha")
DB_HOST = os.environ.get("NEON_HOST", "localhost")
DB_PORT = os.environ.get("NEON_PORT", 5432)

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    sslmode="require"
)

with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS saves (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
            slot TEXT,
            game_data JSONB NOT NULL,
            salvo_em TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, slot)
        );
    """)
    conn.commit()
    print("📦 Tabelas criadas com sucesso!")