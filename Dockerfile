# Usar uma imagem base Python oficial
FROM python:3.11

# Definir diretório de trabalho
WORKDIR /app

# Copiar os arquivos de requisitos primeiro
COPY requirements.txt .

# Instalar dependências
RUN pip3 install -r requirements.txt

# Copiar o resto do código
COPY . .

# Porta padrão do App Runner
EXPOSE 8080

# Variáveis de ambiente serão definidas no App Runner
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:${PATH}"

# Usar caminho completo do Python
ENTRYPOINT ["/usr/local/bin/python3"]
CMD ["app.py"]