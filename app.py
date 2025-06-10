import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

DB_NAME = os.environ.get("NEON_DB", "neondb")
DB_USER = os.environ.get("NEON_USER", "user")
DB_PASSWORD = os.environ.get("NEON_PASSWORD", "senha")
DB_HOST = os.environ.get("NEON_HOST", "localhost")
DB_PORT = int(os.environ.get("NEON_PORT", 5432))
sslmode = "require" if os.environ.get("NEON_USE_SSL", "false").lower() == "true" else "disable"

@app.route("/salvar", methods=["POST"])
def salvar():
    try:
        data = request.json
        email = data.get("email")
        slot = data.get("slot", "slot1")
        progresso = json.dumps(data.get("progresso", {}))

        with psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode=sslmode
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
                user = cur.fetchone()
                if not user:
                    cur.execute("INSERT INTO usuarios (email) VALUES (%s) RETURNING id", (email,))
                    user = cur.fetchone()
                user_id = user[0]

                cur.execute("""
                    INSERT INTO saves (user_id, slot, game_data, salvo_em)
                    VALUES (%s, %s, %s, now())
                    ON CONFLICT (user_id, slot) DO UPDATE
                    SET game_data = EXCLUDED.game_data,
                        salvo_em = now()
                """, (user_id, slot, progresso))
                conn.commit()

        return jsonify({"status": "salvo com sucesso"})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/carregar", methods=["GET"])
def carregar():
    email = request.args.get("email")
    slot = request.args.get("slot", "slot1")

    try:
        with psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode=sslmode
        ) as conn:
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
                    return jsonify({"progresso": json.loads(row["game_data"])})
                return jsonify({"erro": "não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/")
def home():
    # Coleta as informações de conexão
    db_name = os.environ.get("NEON_DB", "neondb")
    db_user = os.environ.get("NEON_USER", "user")
    db_password = os.environ.get("NEON_PASSWORD", "senha")
    db_host = os.environ.get("NEON_HOST", "localhost")
    db_port = int(os.environ.get("NEON_PORT", 5432))
    sslmode = "require" if os.environ.get("NEON_USE_SSL", "false").lower() == "true" else "disable"

    # Monta a mensagem com as informações
    info = (
        "API do jogo está online!\n\n"
        "Configurações do Banco de Dados:\n"
        f"DB_NAME: {db_name}\n"
        f"DB_USER: {db_user}\n"
        f"DB_PASSWORD: {db_password}\n"
        f"DB_HOST: {db_host}\n"
        f"DB_PORT: {db_port}\n"
        f"SSL Mode: {sslmode}"
    )
    return info

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
