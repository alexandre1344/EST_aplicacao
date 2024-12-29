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

// Funções de Autenticação
async function handleLogin(event) {
    event.preventDefault();
    
    const data = {
        usuario: document.getElementById('usuario').value,
        senha: document.getElementById('senha').value
    };

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error('Erro na autenticação');
        }

        const result = await response.json();

        if (result.success) {
            // Mostrar menu superior
            document.getElementById('topMenu').style.display = 'block';
            document.getElementById('menuUserName').textContent = result.nome;
            document.getElementById('menuUserRole').textContent = 
                result.nivel_acesso === 'admin' ? 'Administrador' : 'Usuário';

            // Esconder login
            document.getElementById('loginForm').style.display = 'none';

            // Mostrar painel apropriado
            if (result.nivel_acesso === 'admin') {
                document.getElementById('adminPanel').style.display = 'block';
                await loadDashboard();  // Aguardar o carregamento do dashboard
            } else {
                document.getElementById('userPanel').style.display = 'block';
                await loadPlacas();
            }
        } else {
            alert('Erro no login: ' + result.message);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao fazer login: ' + error.message);
    }
}

async function logout() {
    try {
        const response = await fetch('/api/logout');
        const data = await response.json();
        
        if (data.success) {
            // Esconder menu superior
            document.getElementById('topMenu').style.display = 'none';
            
            // Esconder painéis
            document.getElementById('adminPanel').style.display = 'none';
            document.getElementById('userPanel').style.display = 'none';
            
            // Mostrar login
            document.getElementById('loginForm').style.display = 'block';
            
            // Limpar campos do login
            document.getElementById('usuario').value = '';
            document.getElementById('senha').value = '';
        }
    } catch (error) {
        console.error('Erro ao fazer logout:', error);
        alert('Erro ao fazer logout');
    }
}

// Funções do Painel Admin
async function loadDashboard() {
    try {
        // Verificar sessão primeiro
        const sessionResponse = await fetch('/api/check_session');
        const sessionData = await sessionResponse.json();
        
        if (!sessionData.success || sessionData.nivel_acesso !== 'admin') {
            throw new Error('Sessão expirada ou usuário sem permissão');
        }

        // Carregar estatísticas
        const statsResponse = await fetch('/api/dashboard/stats');
        const statsData = await statsResponse.json();
        
        if (statsData.success) {
            const adminPanel = document.getElementById('adminPanel');
            const statsHtml = `
                <div class="card dashboard-stats">
                    <h2>Dashboard</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>Veículos Ativos</h3>
                            <p class="stat-number">${statsData.veiculos_ativos}</p>
                        </div>
                        <div class="stat-card">
                            <h3>Total Hoje</h3>
                            <p class="stat-number">${formatarMoeda(statsData.total_hoje)}</p>
                        </div>
                        <div class="stat-card">
                            <h3>Veículos Hoje</h3>
                            <p class="stat-number">${statsData.veiculos_hoje}</p>
                        </div>
                        <div class="stat-card">
                            <h3>Usuários Ativos</h3>
                            <p class="stat-number">${statsData.total_usuarios}</p>
                        </div>
                    </div>
                </div>
            `;
            
            adminPanel.querySelector('.dashboard-stats')?.remove();
            adminPanel.insertAdjacentHTML('afterbegin', statsHtml);
        }

        // Carregar lista de usuários com tratamento de erro melhorado
        const usersResponse = await fetch('/api/usuarios', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });
        
        if (!usersResponse.ok) {
            const contentType = usersResponse.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const errorData = await usersResponse.json();
                throw new Error(errorData.message || 'Erro ao carregar usuários');
            } else {
                throw new Error('Erro de autenticação - Faça login novamente');
            }
        }

        const usersData = await usersResponse.json();
        
        const usersList = document.getElementById('usersList');
        if (usersData.success && Array.isArray(usersData.usuarios)) {
            usersList.innerHTML = `
                <h3>Usuários Cadastrados</h3>
                <div class="users-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Nome</th>
                                <th>Usuário</th>
                                <th>Nível</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${usersData.usuarios.map(user => `
                                <tr>
                                    <td>${user.nome || ''}</td>
                                    <td>${user.username || ''}</td>
                                    <td>${(user.nivel_acesso === 'admin' ? 'Administrador' : 'Usuário') || ''}</td>
                                    <td>
                                        <button onclick="excluirUsuario('${user._id}')" class="btn btn-danger btn-sm">Excluir</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            usersList.innerHTML = '<p>Nenhum usuário cadastrado.</p>';
        }

        // Configurar data padrão no seletor de data
        const today = new Date().toISOString().split('T')[0];
        const dateInput = document.getElementById('reportDate');
        if (dateInput) {
            dateInput.max = today; // Impede seleção de datas futuras
            dateInput.value = today; // Define data atual como padrão
        }

        // Configurar data máxima para o seletor de data personalizada
        const todayMax = new Date().toISOString().split('T')[0];
        const dateInputMax = document.getElementById('reportDate');
        if (dateInputMax) {
            dateInputMax.max = todayMax; // Impede seleção de datas futuras
        }
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
        const usersList = document.getElementById('usersList');
        if (usersList) {
            if (error.message.includes('Sessão expirada')) {
                // Redirecionar para login
                document.getElementById('loginForm').style.display = 'block';
                document.getElementById('adminPanel').style.display = 'none';
                document.getElementById('topMenu').style.display = 'none';
            }
            usersList.innerHTML = `<p>Erro ao carregar lista de usuários: ${error.message}</p>`;
        }
    }
}

async function loadUsers() {
    try {
        const response = await fetch('/api/usuarios');
        const data = await response.json();
        
        const usersList = document.getElementById('usersList');
        usersList.innerHTML = data.usuarios.map(user => `
            <div class="list-item">
                <span>${user.nome} (${user.username})</span>
                <span>${user.nivel_acesso}</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Erro ao carregar usuários:', error);
    }
}

async function generateExcelReport() {
    try {
        window.location.href = '/api/relatorio/excel';
    } catch (error) {
        alert('Erro ao gerar relatório');
    }
}

// Funções do Painel Usuário
async function handleNovaPlaca(event) {
    event.preventDefault();
    
    const placa = document.getElementById('placa').value;
    
    try {
        const response = await fetch('/api/veiculos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ placa })
        });
        
        if (response.ok) {
            document.getElementById('placa').value = '';
            loadPlacas();
        } else {
            alert('Erro ao registrar placa');
        }
    } catch (error) {
        alert('Erro ao registrar placa');
    }
}

// Função para formatar moeda
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

// Função para marcar como pago
async function marcarComoPago(id) {
    if (!confirm('Confirmar pagamento deste veículo?')) return;
    
    try {
        const response = await fetch(`/api/veiculos/${id}/pagar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const veiculo = data.veiculo;
            const entrada = new Date(veiculo.entrada).toLocaleString();
            const saida = new Date(veiculo.saida).toLocaleString();
            
            alert(`Pagamento Registrado com Sucesso!
                
Placa: ${veiculo.placa}
Entrada: ${entrada}
Saída: ${saida}
Tempo Total: ${veiculo.tempo_permanencia}
Horas Cobradas: ${veiculo.horas_cobradas}
Valor a Pagar: ${formatarMoeda(veiculo.valor_pago)}

Primeira hora: R$ 5,00
Horas adicionais: R$ 2,00 cada`);
            
            loadPlacas(); // Recarrega a lista
        } else {
            alert('Erro ao registrar pagamento: ' + data.message);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao processar pagamento');
    }
}

// Função para adicionar nova placa
async function handleAddPlaca(event) {
    event.preventDefault();
    
    const placa = document.getElementById('newPlaca').value.trim().toUpperCase();
    if (!placa) {
        alert('Por favor, digite uma placa válida');
        return;
    }

    try {
        const response = await fetch('/api/veiculos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ placa: placa })
        });

        const data = await response.json();

        if (data.success) {
            alert('Veículo registrado com sucesso!');
            document.getElementById('newPlaca').value = ''; // Limpa o campo
            loadPlacas(); // Recarrega a lista de placas
        } else {
            alert('Erro ao registrar veículo: ' + data.message);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao registrar veículo');
    }
}

// Função para carregar placas
async function loadPlacas() {
    try {
        const response = await fetch('/api/veiculos');
        const data = await response.json();
        
        const listaPlacas = document.getElementById('listaPlacas');
        if (data.success && data.veiculos && data.veiculos.length > 0) {
            listaPlacas.innerHTML = data.veiculos.map(veiculo => {
                const entrada = new Date(veiculo.entrada);
                const agora = new Date();
                const diff = Math.floor((agora - entrada) / (1000 * 60)); // diferença em minutos
                const horas = Math.floor(diff / 60);
                const minutos = diff % 60;
                
                return `
                <div class="list-item">
                    <div class="placa-info">
                        <strong>Placa:</strong> ${veiculo.placa}
                        <br>
                        <small>Entrada: ${entrada.toLocaleString()}</small>
                        <br>
                        <small>Tempo decorrido: ${horas}h ${minutos}min</small>
                        <br>
                        <small>Status: ${veiculo.status}</small>
                    </div>
                    <div class="placa-actions">
                        ${veiculo.status === 'ativo' ? 
                            `<button onclick="marcarComoPago('${veiculo._id}')" class="btn btn-success">Pago</button>` : 
                            `<span class="badge badge-success">Pago - ${formatarMoeda(veiculo.valor_pago)}</span>`
                        }
                        <button onclick="excluirPlaca('${veiculo._id}')" class="btn btn-danger">Excluir</button>
                    </div>
                </div>
                `;
            }).join('');
        } else {
            listaPlacas.innerHTML = '<p>Nenhum veículo registrado.</p>';
        }
    } catch (error) {
        console.error('Erro ao carregar placas:', error);
        document.getElementById('listaPlacas').innerHTML = '<p>Erro ao carregar veículos.</p>';
    }
}

async function searchPlate() {
    const placa = document.getElementById('searchPlate').value.trim();
    if (!placa) {
        alert('Por favor, digite uma placa para pesquisar');
        return;
    }
    
    try {
        const response = await fetch(`/api/veiculos/busca?placa=${placa}`);
        const data = await response.json();
        
        if (data.veiculo) {
            const status = data.veiculo.status === 'ativo' ? 'Estacionado' : 'Finalizado';
            const entrada = new Date(data.veiculo.entrada).toLocaleString();
            const saida = data.veiculo.saida ? new Date(data.veiculo.saida).toLocaleString() : 'Ainda estacionado';
            
            alert(`Placa encontrada!\n
                Status: ${status}\n
                Entrada: ${entrada}\n
                Saída: ${saida}`);
        } else {
            alert('Placa não encontrada');
        }
    } catch (error) {
        console.error('Erro na busca:', error);
        alert('Erro ao buscar placa');
    }
}

async function excluirPlaca(id) {
    if (!confirm('Tem certeza que deseja excluir este registro?')) return;
    
    try {
        const response = await fetch(`/api/veiculos/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Registro excluído com sucesso!');
            loadPlacas(); // Recarrega a lista
        } else {
            alert('Erro ao excluir registro: ' + data.message);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao excluir registro');
    }
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

// Funções de Gerenciamento de Usuários
function showAddUserForm() {
    document.getElementById('addUserForm').style.display = 'block';
}

function hideAddUserForm() {
    document.getElementById('addUserForm').style.display = 'none';
}

async function handleAddUser(event) {
    event.preventDefault();
    
    const data = {
        username: document.getElementById('newUsername').value,
        senha: document.getElementById('newPassword').value,
        nome: document.getElementById('newNome').value,
        nivel_acesso: document.getElementById('newNivelAcesso').value
    };

    try {
        const response = await fetch('/api/usuarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            alert('Usuário criado com sucesso!');
            hideAddUserForm();
            // Limpar formulário
            document.getElementById('newUsername').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('newNome').value = '';
            document.getElementById('newNivelAcesso').value = 'usuario';
            // Recarregar lista de usuários
            loadUsers();
        } else {
            alert('Erro ao criar usuário');
        }
    } catch (error) {
        alert('Erro ao criar usuário');
        console.error(error);
    }
}

// Funções de tema
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateThemeIcon(theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

function updateThemeIcon(theme) {
    const themeToggle = document.getElementById('themeToggle');
    themeToggle.innerHTML = theme === 'light' ? '🌙' : '☀️';
}

// Inicializar tema
document.addEventListener('DOMContentLoaded', () => {
    checkSession();
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
});

// Função para excluir usuário
async function excluirUsuario(id) {
    if (!confirm('Tem certeza que deseja excluir este usuário?')) return;
    
    try {
        const response = await fetch(`/api/usuarios/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Usuário excluído com sucesso!');
            loadDashboard(); // Recarrega a lista
        } else {
            alert('Erro ao excluir usuário: ' + data.message);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao excluir usuário');
    }
}

// Função para verificar sessão ao carregar a página
async function checkSession() {
    try {
        const response = await fetch('/api/check_session', {
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error('Sessão inválida');
        }

        const data = await response.json();
        
        if (data.success) {
            // Mostrar menu superior
            document.getElementById('topMenu').style.display = 'block';
            document.getElementById('menuUserName').textContent = data.nome;
            document.getElementById('menuUserRole').textContent = 
                data.nivel_acesso === 'admin' ? 'Administrador' : 'Usuário';

            // Esconder login
            document.getElementById('loginForm').style.display = 'none';

            // Mostrar painel apropriado
            if (data.nivel_acesso === 'admin') {
                document.getElementById('adminPanel').style.display = 'block';
                await loadDashboard();  // Aguardar o carregamento do dashboard
            } else {
                document.getElementById('userPanel').style.display = 'block';
                await loadPlacas();
            }
        }
    } catch (error) {
        console.error('Erro ao verificar sessão:', error);
        // Mostrar login em caso de erro
        document.getElementById('loginForm').style.display = 'block';
        document.getElementById('adminPanel').style.display = 'none';
        document.getElementById('userPanel').style.display = 'none';
        document.getElementById('topMenu').style.display = 'none';
    }
}

// Função para atualizar opções do relatório
function updateReportOptions() {
    const reportType = document.getElementById('reportType').value;
    const customDateContainer = document.getElementById('customDateContainer');
    const dateInput = document.getElementById('reportDate');
    
    if (reportType === 'personalizado') {
        customDateContainer.style.display = 'block';
        // Configurar data máxima como hoje
        const today = new Date().toISOString().split('T')[0];
        dateInput.max = today;
        if (!dateInput.value) {
            dateInput.value = today;
        }
    } else {
        customDateContainer.style.display = 'none';
    }
}

// Função para gerar relatório
async function gerarRelatorio() {
    try {
        const reportType = document.getElementById('reportType').value;
        let selectedDate;

        switch (reportType) {
            case 'hoje':
                selectedDate = new Date().toISOString().split('T')[0];
                break;
            case 'ontem':
                const ontem = new Date();
                ontem.setDate(ontem.getDate() - 1);
                selectedDate = ontem.toISOString().split('T')[0];
                break;
            case 'semana':
                const semanaPassada = new Date();
                semanaPassada.setDate(semanaPassada.getDate() - 7);
                selectedDate = semanaPassada.toISOString().split('T')[0];
                break;
            case 'mes':
                const mesPassado = new Date();
                mesPassado.setMonth(mesPassado.getMonth() - 1);
                selectedDate = mesPassado.toISOString().split('T')[0];
                break;
            case 'personalizado':
                selectedDate = document.getElementById('reportDate').value;
                if (!selectedDate) {
                    alert('Por favor, selecione uma data para o relatório');
                    return;
                }
                break;
        }

        // Criar URL com a data selecionada e tipo
        const url = `/api/relatorio/excel?data=${selectedDate}&tipo=${reportType}`;
        
        // Fazer o download do arquivo
        window.location.href = url;
    } catch (error) {
        console.error('Erro ao gerar relatório:', error);
        alert('Erro ao gerar relatório');
    }
} 