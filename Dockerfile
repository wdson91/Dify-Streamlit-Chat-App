# Use a imagem oficial do Python
FROM python:3.9-slim

# Defina o diretório de trabalho dentro do container
WORKDIR /app

# Copie os arquivos do projeto para o diretório de trabalho
COPY . /app

# Instale as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta que o Streamlit vai usar
EXPOSE 8501

# Comando para rodar o Streamlit
CMD ["streamlit", "run", "app4.py"]
