import requests
import streamlit as st
import json
import uuid
import os
import sqlite3
import bcrypt

# URL da API para chamadas externas
url = "https://novoprojeto-n8n.aidvjr.easypanel.host/webhook/144c0723-cb14-41cd-90f7-2b086dc8dabf"
CHAT_HISTORY_DIR = "chat_histories"  # Diretório onde as conversas serão armazenadas
DB_PATH = "users.db"  # Banco de dados SQLite

# Garante que a pasta de histórico de conversas exista
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# Função para conectar ao banco de dados
def connect_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    conn.commit()
    return conn

# Inicializa a sessão de login
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode() if isinstance(hashed, str) else hashed)


def login_page():
    st.title("🔑 Login")
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password(password, user[1]):
            st.session_state.authenticated = True
            st.session_state.user_id = user[0]
            st.session_state.email = email  
            st.rerun()
        else:
            st.error("Email ou senha incorretos.")
    
    if st.button("Cadastrar-se"):
        st.session_state.show_register = True
        st.rerun()

def register_page():
    st.title("📝 Cadastro")
    new_email = st.text_input("Email")
    new_password = st.text_input("Senha", type="password")
    
    if st.button("Registrar"):
        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                           (new_email, hash_password(new_password)))
            conn.commit()
            st.success("Usuário cadastrado com sucesso! Agora faça login.")
            st.session_state.show_register = False
        except sqlite3.IntegrityError:
            st.error("Email já cadastrado.")
        finally:
            conn.close()
    
    if st.button("Voltar para Login"):
        st.session_state.show_register = False
        st.rerun()

def chat_page():
    st.sidebar.subheader(f"Bem-vindo, {st.session_state.email} 👋")
    if st.sidebar.button("🚪 Sair"):
        st.session_state.authenticated = False
        st.rerun()

    st.title("💬 Chatbot Streamlit")

    def list_saved_conversations():
        conversations = [f.replace(".json", "") for f in os.listdir(CHAT_HISTORY_DIR) if f.endswith(".json")]
        return sorted(conversations, key=lambda x: os.path.getmtime(os.path.join(CHAT_HISTORY_DIR, f"{x}.json")), reverse=True)

    def load_chat_history(chat_id):
        file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        return {"chat_id": chat_id, "messages": [], "session_id": str(uuid.uuid4()), "user_id": st.session_state.user_id}

    def save_chat_history(chat_id, messages, session_id):
        file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
        data = {"chat_id": chat_id, "messages": messages, "session_id": session_id, "user_id": st.session_state.user_id}
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def reset_chat():
        new_chat_id = str(uuid.uuid4())  
        st.session_state.chat_id = new_chat_id
        st.session_state.session_id = str(uuid.uuid4())  
        st.session_state.messages = []  
        save_chat_history(new_chat_id, [], st.session_state.session_id)

    st.sidebar.subheader("📜 Históricos de Conversa")
    saved_conversations = [c for c in list_saved_conversations() if load_chat_history(c).get("user_id") == st.session_state.user_id]

    if st.sidebar.button("➕ Nova Conversa"):
        reset_chat()

    for chat_id in saved_conversations:
        if st.sidebar.button(f"Conversa {chat_id}", key=chat_id):
            chat_data = load_chat_history(chat_id)
            st.session_state.chat_id = chat_data["chat_id"]
            st.session_state.session_id = chat_data["session_id"]
            st.session_state.messages = chat_data["messages"]

    if not st.session_state.get("chat_id"):
        reset_chat()

    st.markdown(f"### ID da Conversa: {st.session_state.chat_id}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Digite sua mensagem")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_chat_history(st.session_state.chat_id, st.session_state.messages, st.session_state.session_id)

if "show_register" in st.session_state and st.session_state.show_register:
    register_page()
else:
    if not st.session_state.authenticated:
        login_page()
    else:
        chat_page()
