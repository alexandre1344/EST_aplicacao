// Estado global
let usuarioAtual = null;

// Funções de API
async function api(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include'
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(`/api/${endpoint}`, options);
    return response.json();
}

// Handlers
async function handleLogin(event) {
    event.preventDefault();
    
    const usuario = document.getElementById('usuario').value;
    const senha = document.getElementById('senha').value;

    try {
        const response = await api('login', 'POST', { usuario, senha });
        
        if (response.success) {
            usuarioAtual = {
                nome: response.nome,
                nivel_acesso: response.nivel_acesso
            };
            
            document.getElementById('usuarioNome').textContent = response.nome;
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('mainContent').style.display = 'block';
            
            carregarAnotacoes();
        } else {
            alert('Usuário ou senha inválidos');
        }
    } catch (error) {
        alert('Erro ao fazer login');
        console.error(error);
    }
}

async function handleNovaAnotacao(event) {
    event.preventDefault();
    
    const anotacao = document.getElementById('anotacao').value;

    try {
        const response = await api('anotacoes', 'POST', {
            anotacao,
            usuario: usuarioAtual.nome
        });

        if (response.success) {
            document.getElementById('anotacao').value = '';
            carregarAnotacoes();
        } else {
            alert('Erro ao adicionar anotação');
        }
    } catch (error) {
        alert('Erro ao adicionar anotação');
        console.error(error);
    }
}

async function marcarComoPago(id) {
    try {
        const response = await api(`marcar-pago/${id}`, 'POST');
        if (response.success) {
            carregarAnotacoes();
        } else {
            alert('Erro ao marcar como pago');
        }
    } catch (error) {
        alert('Erro ao marcar como pago');
        console.error(error);
    }
}

async function carregarAnotacoes() {
    try {
        const response = await api('anotacoes');
        
        if (response.success) {
            const container = document.getElementById('listaAnotacoes');
            container.innerHTML = '';

            response.anotacoes.forEach(anotacao => {
                const element = document.createElement('div');
                element.className = 'anotacao-item';
                
                const status = anotacao.pago ? 
                    '<span class="status-pago">PAGO</span>' : 
                    '<span class="status-pendente">PENDENTE</span>';

                element.innerHTML = `
                    <div>
                        <p><strong>${anotacao.hora}</strong> - ${anotacao.anotacao}</p>
                        <p>Usuário: ${anotacao.usuario}</p>
                        <p>${status} - R$ ${anotacao.pontos.toFixed(2)}</p>
                    </div>
                    ${!anotacao.pago ? `
                        <button onclick="marcarComoPago('${anotacao._id}')" class="btn btn-primary">
                            Marcar como Pago
                        </button>
                    ` : ''}
                `;

                container.appendChild(element);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar anotações:', error);
    }
}

function logout() {
    usuarioAtual = null;
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('mainContent').style.display = 'none';
    document.getElementById('usuario').value = '';
    document.getElementById('senha').value = '';
}

// Verificar sessão ao carregar a página
window.onload = async () => {
    try {
        const response = await api('anotacoes');
        if (response.success) {
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('mainContent').style.display = 'block';
            carregarAnotacoes();
        }
    } catch (error) {
        console.error('Erro ao verificar sessão:', error);
    }
}; 