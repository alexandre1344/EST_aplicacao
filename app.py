from flask import Flask, render_template, request, jsonify, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
import pandas as pd
import io
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sua_chave_secreta')

# Configuração MongoDB
def get_database():
    try:
        client = MongoClient("mongodb+srv://dragonsky134:R9YaV9fRYkjEMczi@cluster0.arpj1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
        db = client.estacionamento_db
        return db
    except Exception as e:
        print(f"Erro na conexão MongoDB: {str(e)}")
        raise

# Rotas da API
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        db = get_database()
        usuario = db.usuarios.find_one({
            "username": data['usuario']
        })
        
        if usuario and check_password_hash(usuario['senha'], data['senha']):
            session['usuario_id'] = str(usuario['_id'])
            session['nivel_acesso'] = usuario['nivel_acesso']
            return jsonify({
                'success': True,
                'nivel_acesso': usuario['nivel_acesso'],
                'nome': usuario['nome']
            })
        
        return jsonify({'success': False, 'message': 'Credenciais inválidas'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/usuarios', methods=['GET', 'POST', 'PUT', 'DELETE'])
def gerenciar_usuarios():
    try:
        # Verificar se o usuário está logado
        if 'usuario_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Usuário não autenticado'
            }), 401

        # Verificar se é admin
        if session.get('nivel_acesso') != 'admin':
            return jsonify({
                'success': False,
                'message': 'Acesso negado'
            }), 403

        db = get_database()
        
        if request.method == 'GET':
            # Buscar todos os usuários, excluindo o campo senha
            usuarios = list(db.usuarios.find({}, {'senha': 0}))
            
            # Converter ObjectId para string em cada usuário
            for usuario in usuarios:
                usuario['_id'] = str(usuario['_id'])
            
            return jsonify({
                'success': True,
                'usuarios': usuarios
            })
            
        elif request.method == 'POST':
            data = request.json
            novo_usuario = {
                "username": data['username'],
                "senha": generate_password_hash(data['senha'], method='sha256'),
                "nome": data['nome'],
                "nivel_acesso": data['nivel_acesso']
            }
            db.usuarios.insert_one(novo_usuario)
            return jsonify({'success': True})
            
    except Exception as e:
        print(f"Erro ao gerenciar usuários: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao gerenciar usuários: {str(e)}'
        }), 500

@app.route('/api/veiculos', methods=['GET', 'POST'])
def gerenciar_veiculos():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401

    db = get_database()
    
    if request.method == 'POST':
        data = request.json
        novo_veiculo = {
            "placa": data['placa'].upper(),
            "entrada": datetime.now(),
            "status": "ativo",
            "registrado_por": session['usuario_id']
        }
        db.veiculos.insert_one(novo_veiculo)
        return jsonify({'success': True})

    elif request.method == 'GET':
        try:
            # Buscar veículos ativos
            veiculos = list(db.veiculos.find({"status": "ativo"}))
            
            # Converter ObjectId para string em cada veículo
            for veiculo in veiculos:
                veiculo['_id'] = str(veiculo['_id'])
                if 'registrado_por' in veiculo:
                    veiculo['registrado_por'] = str(veiculo['registrado_por'])
                # Converter datetime para string
                if 'entrada' in veiculo:
                    veiculo['entrada'] = veiculo['entrada'].strftime('%Y-%m-%dT%H:%M:%S')
                if 'saida' in veiculo:
                    veiculo['saida'] = veiculo['saida'].strftime('%Y-%m-%dT%H:%M:%S')
            
            return jsonify({
                'success': True, 
                'veiculos': veiculos
            })
            
        except Exception as e:
            print(f"Erro ao buscar veículos: {str(e)}")
            return jsonify({
                'success': False, 
                'message': f'Erro ao buscar veículos: {str(e)}'
            }), 500

@app.route('/api/veiculos/busca', methods=['GET'])
def buscar_veiculo():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
        
    try:
        placa = request.args.get('placa', '').upper()
        db = get_database()
        veiculo = db.veiculos.find_one({"placa": placa})
        
        if veiculo:
            # Converter ObjectId para string
            veiculo['_id'] = str(veiculo['_id'])
            if 'registrado_por' in veiculo:
                veiculo['registrado_por'] = str(veiculo['registrado_por'])
                
        return jsonify({'success': True, 'veiculo': veiculo})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/veiculos/<id>/pagar', methods=['POST'])
def finalizar_estadia(id):
    try:
        from bson.objectid import ObjectId
        db = get_database()
        
        # Busca o veículo
        veiculo = db.veiculos.find_one({"_id": ObjectId(id)})
        if not veiculo:
            return jsonify({
                'success': False,
                'message': 'Veículo não encontrado'
            }), 404
            
        # Calcula o tempo de permanência e valor
        entrada = veiculo['entrada']
        saida = datetime.now()
        tempo_total = saida - entrada
        
        # Calcula horas totais (arredondando para cima)
        horas_totais = int((tempo_total.total_seconds() + 3599) // 3600)  # Arredonda para cima
        
        # Calcula valor a pagar
        if horas_totais <= 1:
            valor = 5.00  # Primeira hora
        else:
            valor = 5.00 + ((horas_totais - 1) * 2.00)  # Primeira hora + horas adicionais
        
        # Atualiza o veículo com horário de saída, status e valor
        veiculo = db.veiculos.find_one_and_update(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "status": "pago",
                    "saida": saida,
                    "data_pagamento": datetime.now(),
                    "valor_pago": valor,
                    "tempo_permanencia": str(tempo_total).split('.')[0],  # Remove microssegundos
                    "horas_cobradas": horas_totais
                }
            },
            return_document=True
        )
        
        if veiculo:
            # Converter ObjectId para string
            veiculo['_id'] = str(veiculo['_id'])
            if 'registrado_por' in veiculo:
                veiculo['registrado_por'] = str(veiculo['registrado_por'])
            # Converter datas para string
            if 'entrada' in veiculo:
                veiculo['entrada'] = veiculo['entrada'].strftime('%Y-%m-%dT%H:%M:%S')
            if 'saida' in veiculo:
                veiculo['saida'] = veiculo['saida'].strftime('%Y-%m-%dT%H:%M:%S')
            if 'data_pagamento' in veiculo:
                veiculo['data_pagamento'] = veiculo['data_pagamento'].strftime('%Y-%m-%dT%H:%M:%S')
                
            return jsonify({
                'success': True,
                'message': 'Pagamento registrado com sucesso',
                'veiculo': veiculo
            })
            
    except Exception as e:
        print(f"Erro ao registrar pagamento: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao registrar pagamento: {str(e)}'
        }), 500

@app.route('/api/veiculos/<id>', methods=['DELETE'])
def excluir_veiculo(id):
    try:
        from bson.objectid import ObjectId
        db = get_database()
        
        resultado = db.veiculos.delete_one({"_id": ObjectId(id)})
        
        if resultado.deleted_count > 0:
            return jsonify({
                'success': True,
                'message': 'Veículo excluído com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Veículo não encontrado'
            }), 404
            
    except Exception as e:
        print(f"Erro ao excluir veículo: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao excluir veículo: {str(e)}'
        }), 500

@app.route('/api/relatorio/excel')
def gerar_relatorio_excel():
    if session.get('nivel_acesso') != 'admin':
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403

    try:
        db = get_database()
        
        # Pegar a data e tipo do relatório dos parâmetros
        data_str = request.args.get('data')
        tipo_relatorio = request.args.get('tipo', 'hoje')
        
        # Se não houver data específica, usar data atual
        if not data_str:
            data_base = datetime.now()
        else:
            try:
                # Converter a data recebida para datetime
                data_base = datetime.strptime(data_str, '%Y-%m-%d')
                # Se a data for futura, usar data atual
                if data_base > datetime.now():
                    data_base = datetime.now()
            except ValueError:
                data_base = datetime.now()
            
        # Definir período do relatório baseado no tipo
        if tipo_relatorio == 'hoje':
            inicio_periodo = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            fim_periodo = inicio_periodo + timedelta(days=1)
            titulo = f'Relatório de Vendas - {datetime.now().strftime("%d/%m/%Y")}'
        elif tipo_relatorio == 'ontem':
            inicio_periodo = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            fim_periodo = inicio_periodo + timedelta(days=1)
            titulo = f'Relatório de Vendas - {inicio_periodo.strftime("%d/%m/%Y")}'
        elif tipo_relatorio == 'semana':
            fim_periodo = datetime.now()
            inicio_periodo = (fim_periodo - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            titulo = f'Relatório de Vendas - {inicio_periodo.strftime("%d/%m/%Y")} a {fim_periodo.strftime("%d/%m/%Y")}'
        elif tipo_relatorio == 'mes':
            fim_periodo = datetime.now()
            inicio_periodo = (fim_periodo - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
            titulo = f'Relatório de Vendas - {inicio_periodo.strftime("%d/%m/%Y")} a {fim_periodo.strftime("%d/%m/%Y")}'
        else:  # personalizado
            inicio_periodo = data_base.replace(hour=0, minute=0, second=0, microsecond=0)
            fim_periodo = inicio_periodo + timedelta(days=1)
            titulo = f'Relatório de Vendas - {data_base.strftime("%d/%m/%Y")}'

        print(f"Buscando veículos de {inicio_periodo} até {fim_periodo}")  # Debug
        
        # Query simplificada para pegar todos os veículos pagos no período
        query = {
            "status": "pago",
            "saida": {
                "$gte": inicio_periodo,
                "$lt": fim_periodo
            }
        }
        
        print(f"Query: {query}")  # Debug
        
        # Buscar veículos e ordenar por data de saída
        veiculos = list(db.veiculos.find(query).sort("saida", 1))
        
        print(f"Encontrados {len(veiculos)} veículos")  # Debug
        
        # Preparar dados para o relatório
        dados_relatorio = []
        total_geral = 0
        
        # Processar cada veículo encontrado
        for veiculo in veiculos:
            print(f"Processando veículo: {veiculo.get('placa', '')}")  # Debug
            
            # Garantir que todos os campos necessários existam
            entrada = veiculo.get('entrada')
            saida = veiculo.get('saida')
            valor_pago = veiculo.get('valor_pago', 0)
            
            if isinstance(valor_pago, str):
                valor_pago = float(valor_pago.replace('R$', '').replace(',', '.').strip())
            else:
                valor_pago = float(valor_pago)
            
            # Adicionar ao relatório independente do valor
            dados_relatorio.append({
                'Placa': veiculo.get('placa', '').upper(),
                'Entrada': entrada.strftime('%d/%m/%Y %H:%M') if entrada else '',
                'Saída': saida.strftime('%d/%m/%Y %H:%M') if saida else '',
                'Tempo Total': veiculo.get('tempo_permanencia', ''),
                'Horas Cobradas': veiculo.get('horas_cobradas', 0),
                'Valor Pago': valor_pago,
                'Hora Pagamento': saida.strftime('%H:%M') if saida else ''
            })
            total_geral += valor_pago
            
            print(f"Adicionado ao relatório: {veiculo.get('placa', '')}")  # Debug
        
        print(f"Total de registros no relatório: {len(dados_relatorio)}")  # Debug
        print(f"Total geral calculado: R$ {total_geral:.2f}")  # Debug
        
        # Verificar se todos os registros foram processados
        if len(dados_relatorio) != len(veiculos):
            print("ALERTA: Número de registros processados diferente do número de veículos encontrados!")
            print(f"Veículos encontrados: {len(veiculos)}")
            print(f"Registros processados: {len(dados_relatorio)}")

        # Criar DataFrame com todos os registros
        df = pd.DataFrame(dados_relatorio)
        
        print(f"Tamanho do DataFrame antes do Excel: {len(df)}")  # Debug
        
        # Criar arquivo Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Adicionar dados principais com uma linha extra para o título
            df.to_excel(writer, sheet_name='Relatório Diário', index=False, startrow=1)
            
            workbook = writer.book
            worksheet = writer.sheets['Relatório Diário']
            
            # Debug - Verificar número de linhas na planilha
            print(f"Número de linhas na planilha: {worksheet.dim_rowmax}")
            
            # Formatos melhorados
            titulo_format = workbook.add_format({
                'bold': True,
                'font_size': 16,
                'font_name': 'Arial',
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True
            })
            
            header_format = workbook.add_format({
                'bold': True,
                'font_size': 11,
                'font_name': 'Arial',
                'bg_color': '#366092',
                'font_color': 'white',
                'border': 1,
                'border_color': '#D9D9D9',
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True
            })
            
            # Adicionar título
            worksheet.merge_range('A1:G1', titulo, titulo_format)
            
            # Formatar células com cores alternadas
            for row_num in range(len(df)):
                print(f"Processando linha {row_num + 2}")  # Debug
                row_format = workbook.add_format({
                    'font_size': 10,
                    'font_name': 'Arial',
                    'border': 1,
                    'border_color': '#D9D9D9',
                    'align': 'center',
                    'valign': 'vcenter',
                    'text_wrap': True,
                    'bg_color': '#F2F2F2' if row_num % 2 else 'white'
                })
                
                money_row_format = workbook.add_format({
                    'font_size': 10,
                    'font_name': 'Arial',
                    'border': 1,
                    'border_color': '#D9D9D9',
                    'num_format': 'R$ #,##0.00',
                    'align': 'center',
                    'valign': 'vcenter',
                    'bg_color': '#F2F2F2' if row_num % 2 else 'white'
                })
                
                for col_num, value in enumerate(df.iloc[row_num]):
                    cell_row = row_num + 2  # Linha atual para os dados
                    if col_num == 5:  # Coluna 'Valor Pago'
                        worksheet.write(cell_row, col_num, float(value), money_row_format)
                    else:
                        worksheet.write(cell_row, col_num, value, row_format)
            
            # Adicionar total geral na última linha (ajustado o cálculo)
            ultima_linha = len(df) + 3  # Aumentado em 1 para dar espaço para todos os dados
            print(f"Escrevendo total na linha {ultima_linha}")  # Debug
            
            total_format = workbook.add_format({
                'bold': True,
                'font_size': 11,
                'font_name': 'Arial',
                'bg_color': '#366092',
                'font_color': 'white',
                'border': 1,
                'border_color': '#D9D9D9',
                'num_format': 'R$ #,##0.00',
                'align': 'center',
                'valign': 'vcenter'
            })

            total_label_format = workbook.add_format({
                'bold': True,
                'font_size': 11,
                'font_name': 'Arial',
                'bg_color': '#366092',
                'font_color': 'white',
                'border': 1,
                'border_color': '#D9D9D9',
                'align': 'right',
                'valign': 'vcenter'
            })
            
            worksheet.merge_range(f'A{ultima_linha}:E{ultima_linha}', 'Total Geral:', total_label_format)
            worksheet.merge_range(f'F{ultima_linha}:G{ultima_linha}', total_geral, total_format)
            
            # Ajustar largura das colunas
            worksheet.set_column('A:A', 13)
            worksheet.set_column('B:C', 20)
            worksheet.set_column('D:D', 15)
            worksheet.set_column('E:E', 15)
            worksheet.set_column('F:F', 15)
            worksheet.set_column('G:G', 15)
            
            # Ajustar altura das linhas (incluindo a linha extra)
            worksheet.set_row(0, 35)  # Título
            for row in range(1, ultima_linha + 1):
                worksheet.set_row(row, 25)
            
            # Congelar painéis
            worksheet.freeze_panes(2, 0)
            
            print(f"Finalizado processamento do Excel com {ultima_linha} linhas")  # Debug

        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'relatorio_vendas_{data_base.strftime("%Y%m%d")}.xlsx'
        )
    
    except Exception as e:
        print(f"Erro ao gerar relatório: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao gerar relatório: {str(e)}'}), 500

@app.route('/test_db')
def test_db():
    try:
        db = get_database()
        db.command('ping')
        return jsonify({'success': True, 'message': 'Conexão bem sucedida!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_admin')
def create_admin():
    try:
        db = get_database()
        
        # Verifica se o usuário já existe
        if not db.usuarios.find_one({"username": "Alex"}):
            admin_user = {
                "username": "Alex",
                "senha": generate_password_hash("0134", method='sha256'),  # Especificando método sha256
                "nome": "Alex",
                "nivel_acesso": "admin"
            }
            
            db.usuarios.insert_one(admin_user)
            return jsonify({'success': True, 'message': 'Usuário administrador criado com sucesso!'})
        else:
            return jsonify({'success': False, 'message': 'Usuário administrador já existe!'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/usuarios/<id>', methods=['DELETE'])
def excluir_usuario(id):
    if session.get('nivel_acesso') != 'admin':
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
    try:
        from bson.objectid import ObjectId
        db = get_database()
        
        # Não permitir excluir o próprio usuário
        if str(session.get('usuario_id')) == id:
            return jsonify({
                'success': False,
                'message': 'Não é possível excluir seu próprio usuário'
            }), 400
        
        resultado = db.usuarios.delete_one({"_id": ObjectId(id)})
        
        if resultado.deleted_count > 0:
            return jsonify({
                'success': True,
                'message': 'Usuário excluído com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Usuário não encontrado'
            }), 404
            
    except Exception as e:
        print(f"Erro ao excluir usuário: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao excluir usuário: {str(e)}'
        }), 500

@app.route('/api/check_session')
def check_session():
    try:
        if 'usuario_id' in session:
            db = get_database()
            usuario = db.usuarios.find_one({"_id": ObjectId(session['usuario_id'])})
            
            if usuario:
                return jsonify({
                    'success': True,
                    'nome': usuario['nome'],
                    'nivel_acesso': usuario['nivel_acesso'],
                    'usuario_id': str(usuario['_id'])
                })
        
        return jsonify({
            'success': False,
            'message': 'Sessão inválida'
        }), 401
        
    except Exception as e:
        print(f"Erro ao verificar sessão: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/logout')
def logout():
    try:
        session.clear()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Erro ao fazer logout: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

# Configurar sessão para durar mais tempo (opcional)
app.permanent_session_lifetime = timedelta(days=7)  # Sessão dura 7 dias

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    if session.get('nivel_acesso') != 'admin':
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
    try:
        db = get_database()
        
        # Data de início do dia atual
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Estatísticas
        veiculos_ativos = db.veiculos.count_documents({"status": "ativo"})
        
        # Total de veículos processados hoje
        veiculos_hoje = db.veiculos.count_documents({
            "data_pagamento": {
                "$gte": hoje,
                "$lt": hoje + timedelta(days=1)
            }
        })
        
        # Total em dinheiro hoje
        total_hoje = sum(veiculo.get('valor_pago', 0) for veiculo in db.veiculos.find({
            "status": "pago",
            "data_pagamento": {
                "$gte": hoje,
                "$lt": hoje + timedelta(days=1)
            }
        }))
        
        # Total de usuários ativos
        total_usuarios = db.usuarios.count_documents({})
        
        return jsonify({
            'success': True,
            'veiculos_ativos': veiculos_ativos,
            'veiculos_hoje': veiculos_hoje,
            'total_hoje': total_hoje,
            'total_usuarios': total_usuarios
        })
        
    except Exception as e:
        print(f"Erro ao carregar estatísticas: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao carregar estatísticas: {str(e)}'
        }), 500

# Configurações de sessão
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = True  # Para HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'

@app.before_request
def make_session_permanent():
    session.permanent = True

if __name__ == '__main__':
    app.run(debug=True)