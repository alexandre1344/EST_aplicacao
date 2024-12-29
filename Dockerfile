# Usar uma imagem base Python oficial
FROM python:3.9-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar os arquivos de requisitos primeiro
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto do código
COPY . .

# Porta padrão do App Runner
EXPOSE 8080

# Variáveis de ambiente serão definidas no App Runner
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Comando para executar a aplicação
CMD ["python", "app.py"] 