from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os, json

app = Flask(__name__)
CORS(app)

# Configuração do banco (recomendado usar variáveis de ambiente)
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

@app.route("/salvar", methods=["POST"])
def salvar():
    data = request.json
    email = data.get("email")
    slot = data.get("slot", "slot1")
    progresso = json.dumps(data.get("progresso", {}))

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        user = cur.fetchone()
        if not user:
            cur.execute("INSERT INTO usuarios (email) VALUES (%s) RETURNING id", (email,))
            user = cur.fetchone()
        user_id = user[0]

        cur.execute("""
            INSERT INTO saves (user_id, slot, game_data)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, slot) DO UPDATE
            SET game_data = EXCLUDED.game_data
        """, (user_id, slot, progresso))
        conn.commit()

    return jsonify({"status": "salvo com sucesso"})

@app.route("/carregar", methods=["GET"])
def carregar():
    email = request.args.get("email")
    slot = request.args.get("slot", "slot1")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT s.game_data
            FROM saves s
            JOIN usuarios u ON s.user_id = u.id
            WHERE u.email = %s AND s.slot = %s
            ORDER BY s.salvo_em DESC
            LIMIT 1
        """, (email, slot))
        row = cur.fetchone()
        if row:
            return jsonify({"progresso": row["game_data"]})
        return jsonify({"erro": "não encontrado"}), 404

@app.route("/")
def home():
    return "API do jogo está online!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)