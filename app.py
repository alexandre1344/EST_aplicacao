import os
from flask import Flask, render_template, request, jsonify, session, send_file
from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd
import io
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'uma-chave-secreta-muito-segura')

# Configuração do MongoDB para AWS
def get_database():
    MONGODB_URI = os.getenv('MONGODB_URI')
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI não configurado!")
    
    client = MongoClient(MONGODB_URI)
    return client[os.getenv('DB_NAME', 'estacionamento')]

# Configuração do health check para AWS App Runner
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health_check():
    try:
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# Configuração para produção
if __name__ == '__main__':
    # Usar a porta da variável de ambiente
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)