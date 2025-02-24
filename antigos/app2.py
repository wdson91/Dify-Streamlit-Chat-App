import streamlit as st
import sqlite3
import bcrypt
import requests
import json
import uuid
import os

# URL da API para chamadas externas
url = "https://novoprojeto-n8n.aidvjr.easypanel.host/webhook/144c0723-cb14-41cd-90f7-2b086dc8dabf"
CHAT_HISTORY_DIR = "chat_histories"
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# Conexão com o banco de dados SQLite
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def register_user(username, email, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return False  # Email já cadastrado
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                   (username, email, hashed_password))
    conn.commit()
    conn.close()
    return True

def authenticate_user(email, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode(), user[3]):
        return user[1]  # Retorna o username
    return None

init_db()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login_page():
    st.title("🔑 Login")
    option = st.radio("Escolha uma opção", ["Entrar", "Cadastrar"])

    if option == "Entrar":
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            username = authenticate_user(email, password)
            if username:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Email ou senha incorretos.")

    elif option == "Cadastrar":
        username = st.text_input("Nome de usuário")
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        if st.button("Cadastrar"):
            if register_user(username, email, password):
                st.success("Cadastro realizado com sucesso! Faça login.")
            else:
                st.error("Email já cadastrado.")

def chat_page():
    st.sidebar.subheader(f"Bem-vindo, {st.session_state.username} 👋")
    if st.sidebar.button("🚪 Sair"):
        st.session_state.authenticated = False
        st.rerun()
    st.title("💬 Chatbot Streamlit")
    st.write("Chat funcional aqui...")

if not st.session_state.authenticated:
    login_page()
else:
    chat_page()
