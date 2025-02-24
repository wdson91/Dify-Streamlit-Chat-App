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
                        username TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    conn.commit()
    return conn

# Inicializa a sessão de login
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "show_register" not in st.session_state:
    st.session_state.show_register = False

# Função para apagar uma conversa
def delete_chat(chat_id):
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)

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
        cursor.execute("SELECT id, username, password FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password(password, user[2]):
            st.session_state.authenticated = True
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.email = email  
            st.rerun()  # Recarrega a página para garantir que a autenticação seja mantida
        else:
            st.error("Email ou senha incorretos.")
    
    if st.button("Cadastrar-se"):
        st.session_state.show_register = True
        st.rerun()

def register_page():
    st.title("📝 Cadastro")
    new_email = st.text_input("Email")
    new_username = st.text_input("Nome")
    new_password = st.text_input("Senha", type="password")
    
    if st.button("Registrar"):
        conn = connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
                           (new_email, new_username, hash_password(new_password)))
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
    if not st.session_state.authenticated:
        st.error("Você precisa estar logado para acessar o chat.")
        return

    st.sidebar.subheader(f"Bem-vindo, {st.session_state.username} 👋")
    if st.sidebar.button("🚪 Logout"):
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
        col1, col2 = st.sidebar.columns([4, 1])  # Cria duas colunas
        with col1:
            if st.button(f"Conversa {chat_id}", key=chat_id):
                chat_data = load_chat_history(chat_id)
                st.session_state.chat_id = chat_data["chat_id"]
                st.session_state.session_id = chat_data["session_id"]
                st.session_state.messages = chat_data["messages"]
        with col2:
            if st.button(f"❌", key=f"delete_{chat_id}"):  # Botão de excluir conversa
                delete_chat_id = chat_id
                if delete_chat_id:
                    confirm_delete = st.radio(f"Tem certeza que deseja excluir a conversa {delete_chat_id}?", ["Sim", "Não"])
                    if confirm_delete == "Sim":
                        delete_chat(delete_chat_id)
                        st.success(f"A conversa {delete_chat_id} foi excluída com sucesso!")
                        saved_conversations = list_saved_conversations()
                        if saved_conversations:
                            latest_chat_id = saved_conversations[0]
                            chat_data = load_chat_history(latest_chat_id)
                            st.session_state.chat_id = chat_data["chat_id"]
                            st.session_state.session_id = chat_data["session_id"]
                            st.session_state.messages = chat_data["messages"]
                        else:
                            reset_chat()
                        st.rerun()  # Recarrega a página para refletir as mudanças
                    elif confirm_delete == "Não":
                        delete_chat_id = None  # Cancela a exclusão  

    if not st.session_state.get("chat_id"):
        reset_chat()
    
    st.markdown(f"### ID da Conversa: {st.session_state.chat_id}")
    if not st.session_state.messages:
        welcome_message = f"Olá {st.session_state.username}, Sou um assistente virtual especializado em agendamentos de reuniões na empresa XYZ. Estou aqui para ajudá-lo a gerenciar seus compromissos de forma eficiente."
        st.session_state.messages.append({"role": "assistant", "content": welcome_message})
        save_chat_history(st.session_state.chat_id, st.session_state.messages, st.session_state.session_id)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Digite sua mensagem")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_chat_history(st.session_state.chat_id, st.session_state.messages, st.session_state.session_id)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("⌛ Carregando resposta...")
            
            headers = {"Content-Type": "application/json"}
            payload = {
                "message": prompt,
                "session_id": st.session_state.session_id,
                "chat_id": st.session_state.chat_id,
                "user_id": st.session_state.user_id
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()
                full_response = response_data[0].get("output", "Erro ao obter resposta.")
            except requests.exceptions.RequestException:
                full_response = "Erro ao buscar a resposta."
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            save_chat_history(st.session_state.chat_id, st.session_state.messages, st.session_state.session_id)

if st.session_state.show_register:
    register_page()
elif st.session_state.authenticated:
    chat_page()
else:
    login_page()
