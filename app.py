from flask import Flask
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Carrega variáveis do Render (se existir)
load_dotenv('/etc/secrets/.env')

@app.route("/")
def home():
    return "Servidor funcionando no Render! 🎉"
