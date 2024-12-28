from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'R9YaV9fRYkjEMczi')

# Configuração do MongoDB
def get_database():
    try:
        connection_string = os.environ.get('MONGODB_URI', "mongodb+srv://dragonsky134:R9YaV9fRYkjEMczi@cluster0.arpj1.mongodb.net/fogo_e_lenha_db?retryWrites=true&w=majority")
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            maxPoolSize=1
        )
        
        db = client.get_database()
        db.command('ping')
        return db
        
    except Exception as e:
        print(f"Erro na conexão MongoDB: {str(e)}")
        raise

# Rotas da API
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        usuario = data.get('usuario')
        senha = data.get('senha')
        
        db = get_database()
        usuario_encontrado = db.usuarios.find_one({
            "nome": usuario,
            "senha": senha
        })
        
        if usuario_encontrado:
            session['usuario_id'] = str(usuario_encontrado['_id'])
            return jsonify({
                'success': True,
                'nivel_acesso': usuario_encontrado.get('nivel_acesso', 'usuario'),
                'nome': usuario_encontrado['nome']
            })
        
        return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/anotacoes', methods=['GET', 'POST'])
def anotacoes():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    try:
        db = get_database()
        
        if request.method == 'POST':
            data = request.json
            hora_criacao = datetime.now()
            
            documento = {
                "anotacao": data['anotacao'],
                "hora": hora_criacao.strftime("%H:%M"),
                "data_criacao": hora_criacao,
                "usuario": data['usuario'],
                "pontos": calcular_pontos(hora_criacao),
                "pago": False
            }
            
            resultado = db.anotacoes.insert_one(documento)
            return jsonify({'success': True, 'id': str(resultado.inserted_id)})
            
        else:  # GET
            anotacoes = list(db.anotacoes.find().sort("data_criacao", -1))
            for anotacao in anotacoes:
                anotacao['_id'] = str(anotacao['_id'])
                anotacao['data_criacao'] = anotacao['data_criacao'].strftime("%Y-%m-%d %H:%M:%S")
            
            return jsonify({'success': True, 'anotacoes': anotacoes})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def calcular_pontos(hora_criacao):
    try:
        db = get_database()
        anotacao = db.anotacoes.find_one({"data_criacao": hora_criacao})
        
        if anotacao and anotacao.get('pago', False):
            return anotacao.get('pontos', 5)
        
        hora_atual = datetime.now()
        diferenca = hora_atual - hora_criacao
        diferenca_horas = diferenca.total_seconds() / 3600
        
        pontos_total = 5
        for hora in range(int(diferenca_horas)):
            pontos_total += 2
        
        return pontos_total
        
    except Exception as e:
        print(f"Erro ao calcular pontos: {str(e)}")
        return 5

@app.route('/api/marcar-pago/<id>', methods=['POST'])
def marcar_pago(id):
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    try:
        db = get_database()
        resultado = db.anotacoes.update_one(
            {"_id": id},
            {"$set": {"pago": True}}
        )
        
        return jsonify({'success': True, 'modified': resultado.modified_count > 0})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/relatorio', methods=['GET'])
def gerar_relatorio():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    try:
        db = get_database()
        pipeline = [
            {
                "$match": {
                    "pago": True
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%d/%m/%Y",
                            "date": "$data_criacao"
                        }
                    },
                    "total_placas": {"$sum": 1},
                    "total_ganho": {"$sum": "$pontos"},
                    "registros": {"$push": "$$ROOT"}
                }
            },
            {"$sort": {"_id": -1}}
        ]
        
        resultados = list(db.anotacoes.aggregate(pipeline))
        return jsonify({'success': True, 'relatorio': resultados})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)