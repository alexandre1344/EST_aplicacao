import os
os.environ['ANDROID_DNS_MODE'] = 'local-only'
import json
from datetime import datetime, timedelta
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView  # Importando ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from pymongo import MongoClient
from bson import ObjectId
import dns.resolver
from kivy.uix.checkbox import CheckBox
from kivy.clock import Clock
# Definição das cores (você pode adicionar no topo do arquivo)
CORES = {
    'preto': (0.1, 0.1, 0.1, 1),
    'preto_claro': (0.15, 0.15, 0.15, 1),
    'branco': (1, 1, 1, 1),
    'laranja': (1, 0.65, 0, 1),  # Laranja mais vibrante
    'vermelho': (0.8, 0.2, 0.2, 1),
    'verde': (0.2, 0.7, 0.2, 1)
}

def get_download_folder():
    """Retorna o caminho da pasta Downloads no Android."""
    return "/storage/emulated/0/Download"

def get_database():
    """Conecta ao MongoDB e retorna a database"""
    try:
        # Primeiro tenta configurar DNS manualmente
        import dns.resolver
        dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
        dns.resolver.default_resolver.nameservers = ['8.8.8.8']  # Usando apenas um DNS
        
        # Configurações mais robustas para a conexão MongoDB
        connection_string = "mongodb+srv://dragonsky134:R9YaV9fRYkjEMczi@cluster0.arpj1.mongodb.net/fogo_e_lenha_db?retryWrites=true&w=majority"
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            maxPoolSize=1
        )
        
        # Tenta fazer uma operação simples para verificar a conexão
        db = client.get_database()
        db.command('ping')
        
        return db
        
    except Exception as e:
        print(f"Erro detalhado na conexão MongoDB: {str(e)}")
        if "SSL: CERTIFICATE_VERIFY_FAILED" in str(e):
            raise Exception("Erro de certificado SSL. Verifique a data e hora do dispositivo.")
        elif "No servers found" in str(e):
            raise Exception("Não foi possível encontrar o servidor MongoDB. Verifique sua conexão.")
        else:
            raise Exception(f"Erro ao conectar ao banco de dados: {str(e)}")

# No início do arquivo, após os imports
class MainApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.usuario_atual = None  # Adicionar variável para armazenar usuário atual

    def build(self):
        self.login_screen = LoginApp(self)  # Passa a referência do MainApp
        return self.login_screen.build()

    def switch_to_login(self):
        self.usuario_atual = None  # Limpa o usuário ao voltar para login
        self.root.clear_widgets()
        self.login_screen = LoginApp(self)
        self.root.add_widget(self.login_screen.build())

    def switch_to_anotacao(self, usuario):
        self.usuario_atual = usuario  # Armazena o usuário atual
        self.root.clear_widgets()
        anotacao_screen = AnotacaoApp(self)
        self.root.add_widget(anotacao_screen.build())

    def switch_to_admin(self, usuario):
        self.usuario_atual = usuario  # Armazena o usuário atual
        self.root.clear_widgets()
        admin_screen = AdminApp(self)
        self.root.add_widget(admin_screen.build())

# Variável global para a instância principal
main_application = None

class LoginApp(App):
    def __init__(self, main_app, **kwargs):
        super().__init__(**kwargs)
        self.main_app = main_app

    def build(self):
        global main_app
        main_app = self
        self.title = "Sistema de Login"
        Window.clearcolor = CORES['preto']  # Fundo preto

        # Layout principal
        main_layout = BoxLayout(orientation='vertical')
        
        # Container centralizado
        outer_layout = BoxLayout(orientation='horizontal')
        left_spacer = Widget(size_hint_x=0.1)
        right_spacer = Widget(size_hint_x=0.1)
        
        center_layout = BoxLayout(
            orientation='vertical', 
            padding=40, 
            spacing=30,
            size_hint=(0.8, 0.9)
        )
        
        # Adiciona o logo e título
        logo_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=300,
            spacing=-40,
            pos_hint={'top': 1.2}
        )
        
        titulo_principal = Label(
            text="[b]Fogo e Lenha[/b]",
            font_size=172,
            size_hint_y=None,
            height=200,
            color=CORES['laranja'],
            markup=True
        )
        
        subtitulo = Label(
            text="[i]Gourmet[/i]",
            font_size=116,
            size_hint_y=None,
            height=100,
            color=CORES['laranja'],
            markup=True
        )
        
        logo_layout.add_widget(titulo_principal)
        logo_layout.add_widget(subtitulo)
        center_layout.add_widget(logo_layout)
        
        # Título do app
        titulo = Label(
            text="Sistema de Gestão",
            font_size=48,
            size_hint_y=None,
            height=100,
            color=CORES['laranja']  # Título em laranja
        )
        center_layout.add_widget(titulo)

        # Campos de login
        campos_login = BoxLayout(
            orientation="vertical", 
            spacing=15, 
            size_hint_y=None, 
            height=400
        )
        
        # Campo usuário
        label_usuario = Label(
            text="Usuário:",
            font_size=32,
            size_hint_y=None,
            height=40,
            color=CORES['branco'],  # Texto em branco
            halign='left'
        )
        campos_login.add_widget(label_usuario)

        self.input_usuario = TextInput(
            hint_text="Digite seu usuário",
            font_size=28,
            multiline=False,
            background_color=CORES['preto_claro'],  # Fundo mais claro
            foreground_color=CORES['branco'],  # Texto em branco
            size_hint_y=None,
            height=60,
            padding=[20, 15],
            cursor_color=CORES['laranja']  # Cursor laranja
        )
        campos_login.add_widget(self.input_usuario)

        # Campo senha
        label_senha = Label(
            text="Senha:",
            font_size=32,
            size_hint_y=None,
            height=40,
            color=CORES['branco'],  # Texto em branco
            halign='left'
        )
        campos_login.add_widget(label_senha)

        self.input_senha = TextInput(
            hint_text="Digite sua senha",
            font_size=28,
            multiline=False,
            password=True,
            background_color=CORES['preto_claro'],  # Fundo mais claro
            foreground_color=CORES['branco'],  # Texto em branco
            size_hint_y=None,
            height=60,
            padding=[20, 15],
            cursor_color=CORES['laranja']  # Cursor laranja
        )
        campos_login.add_widget(self.input_senha)

        # Botões
        campos_login.add_widget(Label(size_hint_y=None, height=20))  # Espaçador
        
        btn_entrar = Button(
            text="ENTRAR",
            font_size=36,
            background_color=CORES['verde'],
            size_hint_y=None,
            height=70,
            background_normal='',
            bold=True
        )
        btn_entrar.bind(on_press=self.verificar_login)
        campos_login.add_widget(btn_entrar)
        
        btn_sair = Button(
            text="SAIR",
            font_size=28,
            background_color=CORES['vermelho'],
            size_hint_y=None,
            height=50,
            background_normal='',
            bold=True
        )
        btn_sair.bind(on_press=self.sair_aplicativo)
        campos_login.add_widget(btn_sair)

        # Montagem final do layout
        center_layout.add_widget(campos_login)
        outer_layout.add_widget(left_spacer)
        outer_layout.add_widget(center_layout)
        outer_layout.add_widget(right_spacer)
        
        main_layout.add_widget(Widget())
        main_layout.add_widget(outer_layout)
        main_layout.add_widget(Widget())

        return main_layout

    def sair_aplicativo(self, instance):
        App.get_running_app().stop()

    def verificar_login(self, instance):
        usuario = self.input_usuario.text.strip()
        senha = self.input_senha.text.strip()

        if not usuario or not senha:
            self.mostrar_popup("Erro", "Usuário e senha são obrigatórios!")
            return

        try:
            # Primeiro verifica se é o admin principal
            if usuario == "alexAD" and senha == "Alex0134":
                self.mostrar_popup(
                    "Sucesso", 
                    "Login de administrador bem-sucedido!", 
                    lambda *args: self.main_app.switch_to_admin({
                        "nome": usuario, 
                        "nivel_acesso": "administrador"
                    })
                )
                return

            # Tenta conectar ao banco de dados
            db = get_database()
            colecao_usuarios = db['usuarios']
            
            # Busca o usuário
            usuario_encontrado = colecao_usuarios.find_one({
                "nome": usuario
            })
            
            if not usuario_encontrado:
                self.mostrar_popup("Erro", "Usuário não encontrado!")
                return
            
            # Verifica a senha
            if usuario_encontrado.get('senha') != senha:
                self.mostrar_popup("Erro", "Senha incorreta!")
                return
            
            # Login bem-sucedido - verifica o nível de acesso
            nivel_acesso = usuario_encontrado.get('nivel_acesso', 'usuario')
            
            if nivel_acesso == 'administrador':
                self.mostrar_popup(
                    "Sucesso", 
                    "Login de administrador bem-sucedido!", 
                    lambda *args: self.main_app.switch_to_admin(usuario_encontrado)
                )
            else:
                self.mostrar_popup(
                    "Sucesso", 
                    "Login bem-sucedido!", 
                    lambda *args: self.main_app.switch_to_anotacao(usuario_encontrado)
                )
            
        except Exception as e:
            erro_msg = str(e)
            if "SSL: CERTIFICATE_VERIFY_FAILED" in erro_msg:
                self.mostrar_popup("Erro", "Erro de certificado SSL.\nVerifique a data e hora do dispositivo.")
            elif "No servers found" in erro_msg:
                self.mostrar_popup("Erro", "Não foi possível conectar ao servidor.\nVerifique sua conexão com a internet.")
            else:
                self.mostrar_popup("Erro", f"Erro ao verificar login:\n{erro_msg}")
            print(f"Erro detalhado na conexão MongoDB: {erro_msg}")

    def registrar_usuario(self, instance):
        popup = Popup(title="Registrar Usuário", size_hint=(0.9, 0.9))
        layout = BoxLayout(orientation="vertical", padding=20, spacing=20)

        label_nome = Label(text="Nome do Usuário:", font_size=30)
        layout.add_widget(label_nome)

        input_nome = TextInput(hint_text="Digite o nome do usuário", font_size=25, multiline=False)
        layout.add_widget(input_nome)

        label_senha = Label(text="Senha do Usuário:", font_size=30)
        layout.add_widget(label_senha)

        input_senha = TextInput(hint_text="Digite a senha do usuário", font_size=25, multiline=False, password=True)
        layout.add_widget(input_senha)

        botoes_layout = BoxLayout(size_hint_y=0.3, spacing=10)

        btn_criar = Button(
            text="Criar",
            background_color=(0.1, 0.6, 0.2, 1),
            font_size=30
        )
        btn_criar.bind(on_press=lambda _: self.salvar_usuario(input_nome.text.strip(), input_senha.text.strip(), popup))
        botoes_layout.add_widget(btn_criar)

        btn_cancelar = Button(
            text="Cancelar",
            background_color=(0.7, 0.16, 0.18, 1),
            font_size=30
        )
        btn_cancelar.bind(on_press=popup.dismiss)
        botoes_layout.add_widget(btn_cancelar)

        layout.add_widget(botoes_layout)
        popup.content = layout
        popup.open()

    def salvar_usuario(self, nome, senha, popup):
        if not nome or not senha:
            self.mostrar_popup("Erro", "Nome e senha são obrigatórios!")
            return

        try:
            db = get_database()
            colecao_usuarios = db['usuarios']
            
            # Verifica se usuário já existe
            if colecao_usuarios.find_one({"nome": nome}):
                self.mostrar_popup("Erro", "Usuário já existe!")
                return
            
            # Insere novo usuário
            colecao_usuarios.insert_one({
                "nome": nome,
                "senha": senha,
                "data_criacao": datetime.now()
            })
            
            popup.dismiss()
            self.mostrar_popup("Sucesso", "Usuário registrado com sucesso!")
            
        except Exception as e:
            self.mostrar_popup("Erro", f"Erro ao registrar usuário: {str(e)}")

    def mostrar_popup(self, titulo, mensagem, callback=None):
        """Popup refinado com suporte a callback"""
        popup = Popup(
            title=titulo,
            size_hint=(0.7, 0.4),
            title_size='20sp',
            title_align='center',
            separator_color=CORES['laranja'],
            background_color=CORES['preto'],
            title_color=CORES['laranja']
        )
        
        content_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        mensagem_label = Label(
            text=mensagem,
            font_size=32,
            color=CORES['branco'],
            size_hint_y=0.7
        )
        
        btn_fechar = Button(
            text="Fechar",
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={'center_x': 0.5},
            background_color=CORES['vermelho'],
            background_normal='',
            font_size=24,
            bold=True
        )
        
        def on_fechar(instance):
            popup.dismiss()
            if callback:
                callback()
        
        btn_fechar.bind(on_release=on_fechar)
        
        content_layout.add_widget(mensagem_label)
        content_layout.add_widget(btn_fechar)
        
        popup.content = content_layout
        popup.background = 'atlas://data/images/defaulttheme/button_pressed'
        popup.open()


class AnotacaoApp(App):
    def __init__(self, main_app, **kwargs):
        super().__init__(**kwargs)
        self.main_app = main_app
        self.atualizacao_ativa = True  # Novo atributo para controlar a atualização

    def build(self):
        Window.clearcolor = CORES['preto']

        # Layout principal
        main_layout = BoxLayout(orientation='vertical')
        
        # Adiciona o Clock para atualizar os pontos a cada segundo
        Clock.schedule_interval(self.atualizar_pontos, 1)

        # Barra superior com informações do usuário
        barra_superior = BoxLayout(
            size_hint_y=None,
            height=50,
            padding=[10, 5],
            spacing=10
        )
        
        # Adiciona fundo à barra superior
        with barra_superior.canvas.before:
            Color(*CORES['preto_claro'])
            Rectangle(pos=barra_superior.pos, size=barra_superior.size)
        
        # Atualiza o retângulo quando o tamanho/posição mudar
        def update_rect(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*CORES['preto_claro'])
                Rectangle(pos=instance.pos, size=instance.size)
        
        barra_superior.bind(pos=update_rect, size=update_rect)
        
        # Label com informações do usuário
        usuario_info = Label(
            text=f"Usuário: {self.main_app.usuario_atual['nome']}",
            font_size=24,
            color=CORES['laranja'],
            size_hint_x=0.9,
            halign='left'
        )
        usuario_info.bind(size=usuario_info.setter('text_size'))
        
        barra_superior.add_widget(usuario_info)
        main_layout.add_widget(barra_superior)

        # Container centralizado
        outer_layout = BoxLayout(orientation='horizontal')
        left_spacer = Widget(size_hint_x=0.1)
        right_spacer = Widget(size_hint_x=0.1)
        
        center_layout = BoxLayout(
            orientation='vertical',
            padding=30,
            spacing=25,
            size_hint=(0.8, 0.9)
        )

        # Adiciona o logo e título
        logo_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=160,
            spacing=0
        )
        
        titulo_principal = Label(
            text="[b]Fogo e Lenha[/b]",
            font_size=72,
            size_hint_y=None,
            height=100,
            color=CORES['laranja'],
            markup=True
        )
        
        subtitulo = Label(
            text="[i]Gourmet[/i]",
            font_size=48,
            size_hint_y=None,
            height=60,
            color=CORES['laranja'],
            markup=True
        )
        
        logo_layout.add_widget(titulo_principal)
        logo_layout.add_widget(subtitulo)
        center_layout.add_widget(logo_layout)

        # Cabeçalho
        header = BoxLayout(size_hint_y=None, height=100)
        self.label = Label(
            text="Minhas Anotações",
            font_size=42,
            color=CORES['laranja'],  # Título em laranja
            bold=True
        )
        header.add_widget(self.label)
        center_layout.add_widget(header)

        # Campo de texto
        self.input = TextInput(
            hint_text="Digite sua anotação aqui...",
            multiline=True,
            font_size=32,
            size_hint_y=None,
            height=250,
            background_color=CORES['preto_claro'],
            foreground_color=CORES['branco'],
            padding=[20, 15],
            cursor_color=CORES['laranja']
        )
        center_layout.add_widget(self.input)

        # Botões
        botoes_layout = BoxLayout(size_hint_y=None, height=80, spacing=20)
        
        btn_salvar = Button(
            text="Salvar Anotação",
            font_size=32,
            background_color=CORES['laranja'],
            background_normal='',
            bold=True
        )
        btn_salvar.bind(on_press=self.salvar_anotacao)
        botoes_layout.add_widget(btn_salvar)

        btn_visualizar = Button(
            text="Visualizar Anotações",
            font_size=32,
            background_color=CORES['laranja'],
            background_normal='',
            bold=True
        )
        btn_visualizar.bind(on_press=self.visualizar_anotacoes)
        botoes_layout.add_widget(btn_visualizar)

        center_layout.add_widget(botoes_layout)

        # Botão Voltar
        btn_voltar = Button(
            text="Voltar para Login",
            font_size=32,
            background_color=CORES['vermelho'],
            size_hint_y=None,
            height=60,
            background_normal='',
            bold=True
        )
        btn_voltar.bind(on_release=self.voltar_login)
        center_layout.add_widget(btn_voltar)
        
        # Montagem final do layout
        outer_layout.add_widget(left_spacer)
        outer_layout.add_widget(center_layout)
        outer_layout.add_widget(right_spacer)
        
        main_layout.add_widget(Widget())
        main_layout.add_widget(outer_layout)
        main_layout.add_widget(Widget())

        return main_layout

    def salvar_anotacao(self, instance):
        anotacao = self.input.text.strip()
        if not anotacao:
            self.label.text = "Anotação vazia. Tente novamente."
            return

        try:
            db = get_database()
            colecao_anotacoes = db['anotacoes']
            
            nova_anotacao = {
                "hora": datetime.now().strftime("%H:%M:%S"),
                "anotacao": anotacao,
                "data_criacao": datetime.now(),
                "pontos": 5
            }
            
            colecao_anotacoes.insert_one(nova_anotacao)
            self.label.text = "Anotação salva com sucesso!"
            self.input.text = ""
        
        except Exception as e:
            self.label.text = f"Erro ao salvar: {str(e)}"

    def visualizar_anotacoes(self, instance):
        """Exibe popup para visualizar anotações"""
        self.atualizacao_ativa = False  # Pausa a atualização
        
        try:
            db = get_database()
            colecao_anotacoes = db['anotacoes']
            
            # Agrupa as anotações por data
            pipeline = [
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$data_criacao"
                            }
                        },
                        "anotacoes": {"$push": "$$ROOT"}
                    }
                },
                {"$sort": {"_id": -1}}  # Ordena por data decrescente
            ]
            
            dados = {}
            for grupo in colecao_anotacoes.aggregate(pipeline):
                data = grupo['_id']
                dados[data] = grupo['anotacoes']

            popup = Popup(
                title="Anotações Salvas",
                size_hint=(0.85, 0.9),
                title_size='24sp',
                title_align='center',
                separator_color=CORES['laranja'],
                background_color=CORES['preto'],
                title_color=CORES['laranja']
            )

            layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
            scroll_view = ScrollView(size_hint=(1, 0.95))
            anotacoes_layout = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                spacing=15,
                padding=10
            )
            anotacoes_layout.bind(minimum_height=anotacoes_layout.setter('height'))

            for data, anotacoes in dados.items():
                data_label = Label(
                    text=f"[{data}]",
                    font_size=44,
                    color=CORES['laranja'],
                    bold=True,
                    size_hint_y=None,
                    height=60,
                    halign='center'
                )
                anotacoes_layout.add_widget(data_label)
                
                for item in anotacoes:
                    # Container para cada anotação
                    container = BoxLayout(
                        size_hint_y=None,
                        height=150,
                        spacing=20,
                        padding=10
                    )
                    
                    # Fundo do container
                    with container.canvas.before:
                        Color(*CORES['preto_claro'])
                        Rectangle(pos=container.pos, size=container.size)
                    
                    # Atualização do retângulo
                    def update_rect(instance, value):
                        instance.canvas.before.clear()
                        with instance.canvas.before:
                            Color(*CORES['preto_claro'])
                            Rectangle(pos=instance.pos, size=instance.size)
                    
                    container.bind(pos=update_rect, size=update_rect)
                    
                    # Layout interno para o conteúdo da anotação
                    conteudo_layout = BoxLayout(
                        orientation='vertical',
                        size_hint_x=0.8,
                        padding=[10, 5],
                        pos_hint={'center_x': 0.5}
                    )
                    
                    # Hora e pontos
                    info_label = Label(
                        text=f"[b]{item['hora']}[/b] • {item['pontos']} pontos",
                        font_size=32,
                        color=CORES['laranja'],
                        size_hint_y=None,
                        height=40,
                        halign='center',
                        markup=True,
                        pos_hint={'center_x': 0.5}
                    )
                    
                    # Texto da anotação
                    texto_label = Label(
                        text=f"{item['anotacao']}",
                        font_size=36,
                        color=CORES['branco'],
                        halign='center',
                        valign='middle',
                        text_size=(None, None),
                        size_hint_x=1,
                        pos_hint={'center_x': 0.5}
                    )
                    
                    conteudo_layout.add_widget(info_label)
                    conteudo_layout.add_widget(texto_label)

                    # Layout para os botões
                    botoes_layout = BoxLayout(
                        orientation='vertical',
                        size_hint_x=0.2,
                        spacing=5
                    )

                    # Botão excluir
                    btn_excluir = Button(
                        text="Excluir",
                        size_hint_y=0.5,
                        font_size=30,
                        background_color=CORES['vermelho'],
                        background_normal=''
                    )
                    btn_excluir.bind(on_press=lambda _, item=item: self.confirmar_exclusao(item, popup))

                    # Botão pagar
                    btn_pagar = Button(
                        text="Pagar" if not item.get('pago', False) else "Pago",
                        size_hint_y=0.5,
                        font_size=30,
                        background_color=CORES['verde'] if not item.get('pago', False) else (0.5, 0.5, 0.5, 1),
                        background_normal=''
                    )
                    btn_pagar.bind(on_press=lambda _, item=item, btn=btn_pagar: self.marcar_como_pago(item, btn))

                    botoes_layout.add_widget(btn_excluir)
                    botoes_layout.add_widget(btn_pagar)

                    container.add_widget(conteudo_layout)
                    container.add_widget(botoes_layout)
                    anotacoes_layout.add_widget(container)

            scroll_view.add_widget(anotacoes_layout)
            layout.add_widget(scroll_view)

            # Botão fechar
            btn_fechar = Button(
                text="Fechar",
                size_hint=(None, None),
                size=(200, 60),
                pos_hint={'center_x': 0.5},
                background_color=CORES['vermelho'],
                background_normal='',
                font_size=28,
                bold=True
            )
            
            btn_fechar.bind(on_press=popup.dismiss)
            layout.add_widget(btn_fechar)

            popup.content = layout
            popup.open()

        except Exception as e:
            self.atualizacao_ativa = True  # Garante que a atualização seja retomada em caso de erro
            self.mostrar_popup("Erro", f"Erro ao carregar anotações: {str(e)}")

    def confirmar_exclusao(self, item, parent_popup):
        """Popup de confirmação refinado"""
        confirm_popup = Popup(
            title="Confirmação",
            size_hint=(0.7, 0.4),
            title_size='22sp',
            title_align='center',
            separator_color=CORES['laranja'],
            background_color=CORES['preto'],
            title_color=CORES['laranja']
        )
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        label = Label(
            text="Deseja excluir esta anotação?",
            font_size=32,
            color=CORES['branco']
        )
        
        botoes_layout = BoxLayout(
            size_hint_y=None,
            height=60,
            spacing=20,
            padding=[10, 0]
        )

        # Botões refinados
        for texto, cor, acao in [
            ("Sim", CORES['verde'], lambda _: self.excluir_anotacao(item, confirm_popup, parent_popup)),
            ("Não", CORES['vermelho'], confirm_popup.dismiss)
        ]:
            btn = Button(
                text=texto,
                background_color=cor,
                background_normal='',
                font_size=28,
                bold=True,
                size_hint_x=0.5
            )
            btn.bind(on_press=acao)
            botoes_layout.add_widget(btn)

        layout.add_widget(label)
        layout.add_widget(botoes_layout)
        confirm_popup.content = layout
        confirm_popup.background = 'atlas://data/images/defaulttheme/button_pressed'
        confirm_popup.open()

    def excluir_anotacao(self, item, confirm_popup, parent_popup):
        """Exclui a anotação selecionada do MongoDB."""
        try:
            db = get_database()
            colecao_anotacoes = db['anotacoes']
            
            # Excluir usando o ObjectId do MongoDB
            colecao_anotacoes.delete_one({"_id": item["_id"]})
            
            confirm_popup.dismiss()
            parent_popup.dismiss()
            self.visualizar_anotacoes(None)
            
        except Exception as e:
            self.mostrar_popup("Erro", f"Erro ao excluir: {str(e)}")

    def calcular_pontos(self, item):
        """Calcula os pontos para a anotação com base no tempo."""
        try:
            agora = datetime.now()
            data_criacao = item['data_criacao']  # Já é um objeto datetime do MongoDB
            
            # Calcula a diferença de tempo
            delta = agora - data_criacao
            
            # Calcula as horas totais (incluindo frações de hora)
            horas_totais = delta.total_seconds() / 3600
            
            # Pontos base + 2 pontos por hora adicional
            pontos = 5 + (2 * int(horas_totais))
            
            return pontos
            
        except Exception as e:
            print(f"Erro ao calcular pontos: {str(e)}")
            return 5  # Retorna pontos base em caso de erro

    def voltar_login(self, instance):
        try:
            self.main_app.switch_to_login()
        except Exception as e:
            print(f"Erro ao voltar para login: {str(e)}")

    def atualizar_pontos(self, dt):
        """Atualiza os pontos das anotações a cada segundo"""
        if not self.atualizacao_ativa:  # Verifica se a atualização está ativa
            return
        
        try:
            db = get_database()
            colecao_anotacoes = db['anotacoes']
            
            # Busca todas as anotações
            anotacoes = colecao_anotacoes.find()
            
            # Atualiza os pontos de cada anotação
            for anotacao in anotacoes:
                pontos_atualizados = self.calcular_pontos(anotacao)
                
                # Atualiza no banco de dados
                colecao_anotacoes.update_one(
                    {'_id': anotacao['_id']},
                    {'$set': {'pontos': pontos_atualizados}}
                )
                
        except Exception as e:
            print(f"Erro ao atualizar pontos: {str(e)}")

    def marcar_como_pago(self, item, btn):
        """Marca uma anotação como paga"""
        try:
            db = get_database()
            colecao_anotacoes = db['anotacoes']
            
            # Atualizar o campo 'pago' para True
            colecao_anotacoes.update_one(
                {'_id': item['_id']},
                {'$set': {'pago': True}}
            )
            
            btn.text = "Pago"
            btn.background_color = (0.5, 0.5, 0.5, 1)
            
            self.visualizar_anotacoes(None)
            
        except Exception as e:
            self.mostrar_popup("Erro", f"Erro ao marcar como pago: {str(e)}")


class AdminApp(App):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.nivel_acesso = "usuário"

    def build(self):
        Window.clearcolor = CORES['preto']

        # Layout principal
        main_layout = BoxLayout(
            orientation='vertical',
            padding=[20, 20],
            spacing=20
        )

        # Barra superior com informações do usuário
        top_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=80,
            padding=[15, 5],
            spacing=10
        )
        
        with top_bar.canvas.before:
            Color(*CORES['preto_claro'])
            self.top_bar_rect = Rectangle()
        
        def update_rect(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*CORES['preto_claro'])
                Rectangle(pos=instance.pos, size=instance.size)
        
        top_bar.bind(pos=update_rect, size=update_rect)

        # Informações do usuário
        usuario_label = Label(
            text=f"[b]Administrador: {self.main_app.usuario_atual['nome']}[/b]",
            markup=True,
            font_size='24sp',
            color=CORES['laranja'],
            size_hint_x=0.7,
            halign='left'
        )
        usuario_label.bind(size=usuario_label.setter('text_size'))

        # Botão Sair
        sair_btn = Button(
            text="Sair",
            size_hint=(0.3, 1),
            font_size='22sp',
            background_color=CORES['vermelho'],
            background_normal=''
        )
        sair_btn.bind(on_press=self.voltar_login)

        top_bar.add_widget(usuario_label)
        top_bar.add_widget(sair_btn)
        main_layout.add_widget(top_bar)

        # Container para módulos
        modulos_container = BoxLayout(
            orientation='vertical',
            spacing=150,
            size_hint_y=None,
            height=1000,
            padding=[0, 50, 0, 50]
        )

        # Módulo de Cadastro
        cadastro_container = BoxLayout(
            orientation='vertical',
            spacing=80,  # Aumentado significativamente
            size_hint_y=None,
            height=900,  # Aumentado significativamente
            padding=[40, 100, 40, 100]  # Padding vertical muito maior
        )
        
        with cadastro_container.canvas.before:
            Color(*CORES['preto_claro'])
            self.cadastro_rect = Rectangle()
        cadastro_container.bind(pos=lambda *args: setattr(self.cadastro_rect, 'pos', cadastro_container.pos),
                              size=lambda *args: setattr(self.cadastro_rect, 'size', cadastro_container.size))

        # Título do módulo de cadastro com mais espaço
        cadastro_titulo = Label(
            text="[b]Cadastro de Usuário[/b]",
            markup=True,
            font_size='24sp',
            color=CORES['laranja'],
            size_hint_y=None,
            height=100  # Aumentado
        )
        cadastro_container.add_widget(cadastro_titulo)

        # Ajuste nos campos de entrada com mais espaço vertical
        for label_text, input_attr in [("Usuário:", "usuario_input"), ("Senha:", "senha_input")]:
            field_container = BoxLayout(
                orientation='vertical',
                spacing=40,  # Aumentado
                size_hint_y=None,
                height=220  # Aumentado significativamente
            )
            
            label = Label(
                text=label_text,
                font_size='24sp',  # Aumentado
                color=CORES['laranja'],
                halign='left',
                valign='bottom',
                size_hint_y=None,
                height=80  # Aumentado
            )
            label.bind(size=label.setter('text_size'))
            
            text_input = TextInput(
                multiline=False,
                font_size='24sp',  # Aumentado
                size_hint_y=None,
                height=100,  # Aumentado
                background_color=CORES['preto'],
                foreground_color=CORES['branco'],
                cursor_color=CORES['laranja'],
                padding=[30, 25]  # Aumentado
            )
            
            if label_text == "Senha:":
                text_input.password = True
            
            setattr(self, input_attr, text_input)
            field_container.add_widget(label)
            field_container.add_widget(text_input)
            cadastro_container.add_widget(field_container)

        # Ajuste nos botões de cadastro
        botoes_cadastro = BoxLayout(
            orientation='horizontal',
            spacing=30,  # Aumentado
            size_hint_y=None,
            height=100  # Aumentado
        )

        self.nivel_btn = Button(
            text="Nível: Usuário",
            font_size='24sp',  # Aumentado
            background_color=CORES['laranja'],
            background_normal=''
        )
        self.nivel_btn.bind(on_press=self.mudar_nivel_acesso)

        cadastrar_btn = Button(
            text="Cadastrar",
            font_size='24sp',  # Aumentado
            background_color=CORES['verde'],
            background_normal=''
        )
        cadastrar_btn.bind(on_press=self.cadastrar_usuario)

        botoes_cadastro.add_widget(self.nivel_btn)
        botoes_cadastro.add_widget(cadastrar_btn)
        cadastro_container.add_widget(botoes_cadastro)

        modulos_container.add_widget(cadastro_container)

        # Módulo de Gerenciamento
        gerenciamento_container = BoxLayout(
            orientation='vertical',
            spacing=40,  # Aumentado
            size_hint_y=None,
            height=350,  # Ajustado para o novo spacing
            padding=[40, 60, 40, 40]  # Aumentado significativamente
        )
        
        with gerenciamento_container.canvas.before:
            Color(*CORES['preto_claro'])
            self.gerenciamento_rect = Rectangle()
        gerenciamento_container.bind(pos=lambda *args: setattr(self.gerenciamento_rect, 'pos', gerenciamento_container.pos),
                                   size=lambda *args: setattr(self.gerenciamento_rect, 'size', gerenciamento_container.size))

        # Título do módulo de gerenciamento
        gerenciamento_titulo = Label(
            text="[b]Gerenciamento[/b]",
            markup=True,
            font_size='22sp',
            color=CORES['laranja'],
            size_hint_y=None,
            height=40
        )
        gerenciamento_container.add_widget(gerenciamento_titulo)

        # Botão Gerenciar Usuários
        gerenciar_btn = Button(
            text="Gerenciar Usuários",
            font_size='18sp',
            background_color=CORES['laranja'],
            background_normal='',
            size_hint_y=None,
            height=60
        )
        gerenciar_btn.bind(on_press=self.mostrar_gerenciar_usuarios)
        gerenciamento_container.add_widget(gerenciar_btn)

        # Botões de relatório
        for btn_text, btn_color, btn_action in [
            ("Relatório de Vendas", CORES['laranja'], self.gerar_relatorio),
            ("Relatório Excel", CORES['verde'], self.gerar_relatorio_excel)
        ]:
            btn = Button(
                text=btn_text,
                font_size='18sp',
                background_color=btn_color,
                background_normal='',
                size_hint_y=None,
                height=60
            )
            btn.bind(on_press=btn_action)
            gerenciamento_container.add_widget(btn)

        modulos_container.add_widget(gerenciamento_container)
        main_layout.add_widget(Widget())  # Espaçador flexível
        main_layout.add_widget(modulos_container)
        main_layout.add_widget(Widget())  # Espaçador flexível

        return main_layout

    def cadastrar_usuario(self, instance):
        usuario = self.usuario_input.text.strip()
        senha = self.senha_input.text.strip()

        if not usuario or not senha:
            self.mostrar_popup("Erro", "Usuário e senha são obrigatórios!")
            return

        try:
            db = get_database()
            colecao_usuarios = db['usuarios']
            
            if colecao_usuarios.find_one({"nome": usuario}):
                self.mostrar_popup("Erro", "Usuário já existe!")
                return
            
            colecao_usuarios.insert_one({
                "nome": usuario,
                "senha": senha,
                "nivel_acesso": self.nivel_acesso,
                "data_criacao": datetime.now()
            })
            
            self.mostrar_popup("Sucesso", "Usuário criado com sucesso!")
            self.usuario_input.text = ""
            self.senha_input.text = ""
            self.mostrar_gerenciar_usuarios()
            
        except Exception as e:
            self.mostrar_popup("Erro", f"Erro ao criar usuário: {str(e)}")

    def mostrar_gerenciar_usuarios(self, instance):
        """Exibe popup para gerenciar usuários"""
        try:
            # Criar layout do popup
            layout = BoxLayout(
                orientation='vertical',
                spacing=20,
                padding=[20, 20]
            )

            # Título
            titulo = Label(
                text="[b]Gerenciar Usuários[/b]",
                markup=True,
                font_size='24sp',
                size_hint_y=None,
                height=50,
                color=CORES['laranja']
            )
            layout.add_widget(titulo)

            # Lista de usuários
            lista_usuarios = BoxLayout(
                orientation='vertical',
                spacing=15,
                size_hint_y=None
            )
            lista_usuarios.bind(minimum_height=lista_usuarios.setter('height'))

            # Buscar usuários do banco
            db = get_database()
            usuarios = db['usuarios'].find()

            # Cores por nível
            cores_nivel = {
                'usuário': (1, 1, 0, 1),  # Amarelo
                'administrador': (1, 0, 0, 1)  # Vermelho
            }

            for usuario in usuarios:
                # Container para cada usuário
                usuario_container = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=60,  # Reduzido pois agora só mostra uma linha
                    spacing=10
                )

                with usuario_container.canvas.before:
                    Color(*CORES['preto_claro'])
                    Rectangle(pos=usuario_container.pos, size=usuario_container.size)

                # Determinar a cor baseada no nível
                nivel_acesso = usuario.get('nivel_acesso', 'usuário')
                cor_usuario = cores_nivel.get(nivel_acesso, cores_nivel['usuário'])

                # Nome do usuário com cor baseada no nível
                nome_label = Label(
                    text=f"[b]{usuario['nome']}[/b]",
                    markup=True,
                    font_size='22sp',
                    halign='left',
                    valign='middle',
                    size_hint_x=0.7,
                    color=cor_usuario
                )
                nome_label.bind(size=nome_label.setter('text_size'))

                # Botão excluir
                excluir_btn = Button(
                    text="Excluir",
                    size_hint_x=0.3,
                    background_color=CORES['vermelho'],
                    background_normal='',
                    font_size='18sp'
                )
                excluir_btn.bind(
                    on_press=lambda btn, user_id=usuario['_id']: 
                    self.excluir_usuario(user_id, popup)
                )

                usuario_container.add_widget(nome_label)
                usuario_container.add_widget(excluir_btn)
                lista_usuarios.add_widget(usuario_container)

            # ScrollView para a lista
            scroll = ScrollView(size_hint=(1, 0.8))
            scroll.add_widget(lista_usuarios)
            layout.add_widget(scroll)

            # Botão fechar
            fechar_btn = Button(
                text="Fechar",
                size_hint_y=None,
                height=60,
                background_color=CORES['laranja'],
                background_normal='',
                font_size='20sp'
            )
            
            # Criar popup
            popup = Popup(
                title="Gerenciar Usuários",
                content=layout,
                size_hint=(0.9, 0.9),
                title_color=CORES['laranja'],
                title_size='24sp',
                separator_color=CORES['laranja']
            )
            
            fechar_btn.bind(on_press=popup.dismiss)
            layout.add_widget(fechar_btn)
            
            popup.open()

        except Exception as e:
            self.mostrar_popup("Erro", f"Erro ao carregar usuários: {str(e)}")

    def excluir_usuario(self, user_id, popup):
        """Exclui um usuário do sistema"""
        try:
            # Confirmar exclusão
            confirmar_layout = BoxLayout(
                orientation='vertical',
                spacing=20,
                padding=[20, 20]
            )
            
            msg = Label(
                text="Tem certeza que deseja excluir este usuário?",
                color=CORES['branco']
            )
            confirmar_layout.add_widget(msg)
            
            botoes = BoxLayout(
                orientation='horizontal',
                spacing=20,
                size_hint_y=None,
                height=50
            )
            
            # Botão confirmar
            confirmar_btn = Button(
                text="Confirmar",
                background_color=CORES['vermelho'],
                background_normal=''
            )
            
            # Botão cancelar
            cancelar_btn = Button(
                text="Cancelar",
                background_color=CORES['laranja'],
                background_normal=''
            )
            
            confirmar_popup = Popup(
                title="Confirmar Exclusão",
                content=confirmar_layout,
                size_hint=(0.8, 0.4)
            )
            
            def confirmar_exclusao(instance):
                try:
                    db = get_database()
                    db['usuarios'].delete_one({'_id': user_id})
                    confirmar_popup.dismiss()
                    popup.dismiss()
                    self.mostrar_popup("Sucesso", "Usuário excluído com sucesso!")
                except Exception as e:
                    self.mostrar_popup("Erro", f"Erro ao excluir usuário: {str(e)}")
            
            confirmar_btn.bind(on_press=confirmar_exclusao)
            cancelar_btn.bind(on_press=confirmar_popup.dismiss)
            
            botoes.add_widget(confirmar_btn)
            botoes.add_widget(cancelar_btn)
            confirmar_layout.add_widget(botoes)
            
            confirmar_popup.open()

        except Exception as e:
            self.mostrar_popup("Erro", f"Erro ao processar exclusão: {str(e)}")

    def voltar_login(self, instance):
        try:
            self.main_app.switch_to_login()
        except Exception as e:
            print(f"Erro ao voltar para login: {str(e)}")

    def mostrar_popup(self, titulo, mensagem):
        """Exibe um popup com mensagem"""
        popup = Popup(
            title=titulo,
            content=Label(text=mensagem),
            size_hint=(None, None),
            size=(400, 200)
        )
        popup.open()

    def gerar_relatorio(self, instance):
        try:
            # Criar popup para seleção de registros
            popup = Popup(
                title="Selecionar Registros para Relatório",
                size_hint=(0.9, 0.9),
                title_size='24sp',
                title_align='center',
                separator_color=CORES['laranja'],
                background_color=CORES['preto'],
                title_color=CORES['laranja']
            )

            layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
            
            # Área de scroll para os registros
            scroll = ScrollView()
            self.registros_layout = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                spacing=10,
                padding=10
            )
            self.registros_layout.bind(minimum_height=self.registros_layout.setter('height'))
            
            try:
                db = get_database()
                colecao_anotacoes = db['anotacoes']
                
                # Pipeline para agrupar por data
                pipeline = [
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
                    {"$sort": {"_id": -1}}  # Ordenar por data decrescente
                ]
                
                self.dados_registros = {}  # Armazenar dados para uso posterior
                
                for grupo in colecao_anotacoes.aggregate(pipeline):
                    data = grupo['_id']
                    container = BoxLayout(
                        size_hint_y=None,
                        height=80,
                        spacing=10,
                        padding=[5, 5]
                    )
                    
                    with container.canvas.before:
                        Color(*CORES['preto_claro'])
                        Rectangle(pos=container.pos, size=container.size)
                    
                    checkbox = CheckBox(
                        size_hint_x=0.1,
                        color=CORES['laranja']
                    )
                    
                    info_text = (
                        f"[b]{data}[/b]\n"
                        f"Placas: {grupo['total_placas']} • "
                        f"Total: R$ {grupo['total_ganho']:.2f}"
                    )
                    
                    info_label = Label(
                        text=info_text,
                        markup=True,
                        font_size=24,
                        color=CORES['branco'],
                        size_hint_x=0.9,
                        halign='left'
                    )
                    info_label.bind(size=info_label.setter('text_size'))
                    
                    container.add_widget(checkbox)
                    container.add_widget(info_label)
                    
                    self.registros_layout.add_widget(container)
                    
                    self.dados_registros[data] = {
                        'checkbox': checkbox,
                        'dados': grupo
                    }
            
            except Exception as e:
                self.mostrar_popup("Erro", f"Erro ao carregar registros: {str(e)}")
                return
            
            scroll.add_widget(self.registros_layout)
            layout.add_widget(scroll)
            
            # Botões de ação
            botoes_layout = BoxLayout(
                size_hint_y=None,
                height=60,
                spacing=10
            )
            
            btn_selecionar_todos = Button(
                text="Selecionar Todos",
                background_color=CORES['laranja'],
                background_normal='',
                font_size=24
            )
            btn_selecionar_todos.bind(on_press=self.selecionar_todos_registros)
            
            btn_gerar = Button(
                text="Gerar Relatório",
                background_color=CORES['verde'],
                background_normal='',
                font_size=24
            )
            btn_gerar.bind(on_press=lambda x: self.salvar_relatorio_mongodb(popup))
            
            btn_cancelar = Button(
                text="Cancelar",
                background_color=CORES['vermelho'],
                background_normal='',
                font_size=24
            )
            btn_cancelar.bind(on_press=popup.dismiss)
            
            botoes_layout.add_widget(btn_selecionar_todos)
            botoes_layout.add_widget(btn_gerar)
            botoes_layout.add_widget(btn_cancelar)
            
            layout.add_widget(botoes_layout)
            popup.content = layout
            popup.open()

        except Exception as e:
            self.mostrar_popup("Erro", f"Erro ao preparar seleção: {str(e)}")

    def salvar_relatorio_mongodb(self, popup):
        """Salva o relatório diretamente no MongoDB"""
        try:
            # Verificar se há registros selecionados
            if not hasattr(self, 'dados_registros') or not self.dados_registros:
                self.mostrar_popup("Erro", "Nenhum registro encontrado")
                return

            registros_selecionados = [
                dados['dados'] for data, dados in self.dados_registros.items()
                if dados['checkbox'].active
            ]
            
            if not registros_selecionados:
                self.mostrar_popup("Erro", "Selecione pelo menos um registro")
                return

            # Preparar o relatório
            relatorio = {
                "data_geracao": datetime.now(),
                "gerado_por": self.main_app.usuario_atual['nome'],
                "registros": []
            }

            total_geral_placas = 0
            total_geral_ganho = 0

            # Processar cada registro selecionado
            for item in registros_selecionados:
                registro_dia = {
                    "data": item['_id'],
                    "total_placas": item['total_placas'],
                    "total_ganho": float(item['total_ganho']),
                    "detalhes": []
                }

                for reg in item['registros']:
                    registro_dia["detalhes"].append({
                        "hora": reg['hora'],
                        "anotacao": reg['anotacao'],
                        "pontos": float(reg['pontos']),
                        "data_criacao": reg['data_criacao']
                    })

                total_geral_placas += item['total_placas']
                total_geral_ganho += float(item['total_ganho'])
                relatorio["registros"].append(registro_dia)

            # Adicionar totais gerais
            relatorio["total_geral"] = {
                "placas": total_geral_placas,
                "ganho": total_geral_ganho
            }

            # Salvar no MongoDB
            db = get_database()
            colecao_relatorios = db['relatorios']
            resultado = colecao_relatorios.insert_one(relatorio)

            if resultado.inserted_id:
                popup.dismiss()
                self.mostrar_popup(
                    "Sucesso", 
                    f"Relatório gerado com sucesso!\nID: {resultado.inserted_id}"
                )
            else:
                self.mostrar_popup("Erro", "Falha ao salvar o relatório")

        except Exception as e:
            self.mostrar_popup("Erro", f"Erro ao gerar relatório: {str(e)}")

    def selecionar_todos_registros(self, instance):
        """Seleciona ou desmarca todos os registros"""
        # Verificar se algum está selecionado para determinar a ação
        algum_selecionado = any(dados['checkbox'].active for dados in self.dados_registros.values())
        
        # Se algum estiver selecionado, desmarca todos. Caso contrário, seleciona todos
        for dados in self.dados_registros.values():
            dados['checkbox'].active = not algum_selecionado

    def mudar_nivel_acesso(self, instance):
        """Alterna entre níveis de acesso disponíveis"""
        if self.nivel_acesso == "usuário":
            self.nivel_acesso = "administrador"
            self.nivel_btn.text = "Nível: Administrador"
            self.nivel_btn.background_color = CORES['vermelho']
        else:
            self.nivel_acesso = "usuário"
            self.nivel_btn.text = "Nível: Usuário"
            self.nivel_btn.background_color = CORES['laranja']

    def gerar_relatorio_excel(self, instance):
        """Gera relatório em formato Excel"""
        try:
            # Verificar se há registros selecionados
            if not hasattr(self, 'dados_registros') or not self.dados_registros:
                self.mostrar_popup("Erro", "Nenhum registro encontrado")
                return

            registros_selecionados = [
                dados['dados'] for data, dados in self.dados_registros.items()
                if dados['checkbox'].active
            ]
            
            if not registros_selecionados:
                self.mostrar_popup("Erro", "Selecione pelo menos um registro")
                return

            # Preparar dados para o Excel
            dados_excel = []
            for item in registros_selecionados:
                for reg in item['registros']:
                    dados_excel.append({
                        'Data': item['_id'],
                        'Hora': reg['hora'],
                        'Anotação': reg['anotacao'],
                        'Pontos': reg['pontos']
                    })

            # Gerar nome do arquivo
            data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_arquivo = f"relatorio_{data_atual}.xlsx"
            caminho_arquivo = os.path.join(get_download_folder(), nome_arquivo)

            # Criar DataFrame e salvar Excel
            import pandas as pd
            df = pd.DataFrame(dados_excel)
            
            # Adicionar linha de totais
            total_pontos = sum(float(reg['pontos']) for item in registros_selecionados for reg in item['registros'])
            df.loc[len(df)] = ['TOTAL', '', '', total_pontos]

            # Salvar arquivo
            df.to_excel(caminho_arquivo, index=False, engine='openpyxl')

            self.mostrar_popup(
                "Sucesso", 
                f"Relatório Excel gerado com sucesso!\nSalvo em: {caminho_arquivo}"
            )

        except Exception as e:
            self.mostrar_popup("Erro", f"Erro ao gerar relatório Excel: {str(e)}")

if __name__ == '__main__':
    main_application = MainApp()
    main_application.run()