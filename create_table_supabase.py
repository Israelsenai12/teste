import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from app import app

# ✅ Pega variáveis diretamente do ambiente (Render injeta)
DB_NAME = os.environ["NEON_DB"]
DB_USER = os.environ["NEON_USER"]
DB_PASSWORD = os.environ["NEON_PASSWORD"]
DB_HOST = os.environ["NEON_HOST"]
DB_PORT = os.environ.get("NEON_PORT", 5432)

print("🔐 Conectando ao host:", DB_HOST)

# 🔌 Conexão com Neon
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    sslmode="require"
)

# 🛠️ Criar tabelas
def criar_tabelas():
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT UNIQUE,
            senha TEXT,
            criado_em TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'America/Sao_Paulo')
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS saves (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
            slot TEXT DEFAULT 'slot1',
            game_data JSONB NOT NULL,
            salvo_em TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'America/Sao_Paulo')
        );
        """)
        conn.commit()

# ➕ Cadastrar usuário
def cadastrar_usuario(username, email, senha="1234"):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cur.fetchone():
            print("⚠️ Usuário já existe.")
            return
        cur.execute("""
            INSERT INTO usuarios (username, email, senha)
            VALUES (%s, %s, %s)
        """, (username, email, senha))
        conn.commit()
        print("✅ Usuário cadastrado!")

# 💾 Salvar progresso
def salvar_jogo(email, progresso_dict, slot="slot1"):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        user = cur.fetchone()
        if not user:
            print("❌ Usuário não encontrado.")
            return
        user_id = user[0]
        cur.execute("""
            INSERT INTO saves (user_id, slot, game_data)
            VALUES (%s, %s, %s)
        """, (user_id, slot, json.dumps(progresso_dict)))
        conn.commit()
        print("✅ Progresso salvo!")

# 🔄 Carregar progresso
def carregar_jogo(email, slot="slot1"):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT s.game_data
            FROM saves s
            JOIN usuarios u ON u.id = s.user_id
            WHERE u.email = %s AND s.slot = %s
            ORDER BY s.salvo_em DESC
            LIMIT 1;
        """, (email, slot))
        save = cur.fetchone()
        return save["game_data"] if save else None

def apagar_tabelas_neon():
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS saves CASCADE;")
        cur.execute("DROP TABLE IF EXISTS usuarios CASCADE;")
        conn.commit()
        print("💣 Tabelas do banco Neon foram apagadas.")

def apagar_banco_local(sqlite_db_path="meubanco.db"):
    if os.path.exists(sqlite_db_path):
        os.remove(sqlite_db_path)
        print(f"🗑️ Banco SQLite local '{sqlite_db_path}' apagado.")
    else:
        print("📂 Banco SQLite local não encontrado para apagar.")

def apagar_online_e_local(sqlite_db_path="meubanco.db"):
    apagar_tabelas_neon()
    apagar_banco_local(sqlite_db_path)

# 🧪 Testes locais ou específicos (não roda no Render por padrão)
if __name__ == "__main__":
    if os.environ.get("TESTAR") == "1":  # só roda se TESTAR=1 estiver setado
        criar_tabelas()
        cadastrar_usuario("Thaynos", "thaynos@rpg.com")

        progresso = {
            "level": 7,
            "xp": 420,
            "vida": 35,
            "itens": ["adaga sombria", "poção de cura"],
            "local": "Castelo Esquecido"
        }

        salvar_jogo("thaynos@rpg.com", progresso)
        dados = carregar_jogo("thaynos@rpg.com")

        print("\n🧠 Último progresso carregado:")
        print(json.dumps(dados, indent=2))

        apagar_online_e_local()

    # ✅ Sobe a aplicação Flask no Render
    app.run(host="0.0.0.0", port=5000)
