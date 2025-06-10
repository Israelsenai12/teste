import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

# Use the database URL directly (ensure it's securely set in your environment)
DB_URL = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_auPRq40myNjS@ep-tight-night-achloga2-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require")

def create_table_if_not_exists():
    """Cria as tabelas caso não existam."""
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            # Criação da tabela de usuários caso não exista
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL
                )
            """)
            # Criação da tabela de saves caso não exista
            cur.execute("""
                CREATE TABLE IF NOT EXISTS saves (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES usuarios(id),
                    slot VARCHAR(50),
                    game_data JSONB,
                    salvo_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, slot)
                )
            """)
            conn.commit()

# Chama a função para garantir que as tabelas existam
create_table_if_not_exists()

@app.route("/salvar", methods=["POST"])
def salvar():
    try:
        data = request.json
        email = data.get("email")
        if not email:
            return jsonify({"erro": "Email é obrigatório"}), 400
        slot = data.get("slot", "slot1")
        progresso = json.dumps(data.get("progresso", {}))

        # Connect using the connection URL
        with psycopg2.connect(DB_URL) as conn:
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

    except psycopg2.Error as e:
        print(f"Erro no banco de dados: {e}")
        return jsonify({"erro": f"Erro no banco de dados: {str(e)}"}), 500

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 500


@app.route("/carregar", methods=["GET"])
def carregar():
    email = request.args.get("email")
    slot = request.args.get("slot", "slot1")

    try:
        # Connect using the connection URL
        with psycopg2.connect(DB_URL) as conn:
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
    return "API do jogo está online!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
