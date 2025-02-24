import requests
import streamlit as st
import json
import uuid
import os

# URL da API para chamadas externas
url = "https://novoprojeto-n8n.aidvjr.easypanel.host/webhook/144c0723-cb14-41cd-90f7-2b086dc8dabf"
CHAT_HISTORY_DIR = "chat_histories"  # Diretório onde as conversas serão armazenadas

# Garante que a pasta de histórico de conversas exista
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# Simulação de credenciais (pode substituir por banco de dados ou API)
USERS = {
    "admin": "1234",
    "usuario": "senha123"
}

# Inicializa a sessão de login
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Página de Login
def login_page():
    st.title("🔑 Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if username in USERS and USERS[username] == password:
            st.session_state.authenticated = True
            st.session_state.username = username  # Salva o nome do usuário na sessão
            st.rerun()  # Recarrega a página para exibir o chat
        else:
            st.error("Usuário ou senha incorretos.")

# Página de Chat
def chat_page():
    st.sidebar.subheader(f"Bem-vindo, {st.session_state.username} 👋") 
    if st.sidebar.button("🚪 Sair"):
        st.session_state.authenticated = False
        st.rerun()

    st.title("💬 Chatbot Streamlit")

    # Função para listar todas as conversas salvas e ordená-las das mais recentes para as mais antigas
    def list_saved_conversations():
        conversations = [f.replace(".json", "") for f in os.listdir(CHAT_HISTORY_DIR) if f.endswith(".json")]
        return sorted(conversations, key=lambda x: os.path.getmtime(os.path.join(CHAT_HISTORY_DIR, f"{x}.json")), reverse=True)

    # Função para carregar o histórico de conversa
    def load_chat_history(chat_id):
        file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        return {"chat_id": chat_id, "messages": [], "session_id": str(uuid.uuid4())}

    # Função para salvar a conversa
    def save_chat_history(chat_id, messages, session_id):
        file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
        data = {"chat_id": chat_id, "messages": messages, "session_id": session_id}
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    # Função para resetar a conversa e iniciar uma nova
    def reset_chat():
        new_chat_id = str(uuid.uuid4())  
        st.session_state.chat_id = new_chat_id
        st.session_state.session_id = str(uuid.uuid4())  
        st.session_state.messages = []  
        save_chat_history(new_chat_id, [], st.session_state.session_id)

    # Lista todas as conversas no sidebar
    st.sidebar.subheader("📜 Históricos de Conversa")
    saved_conversations = list_saved_conversations()

    if st.sidebar.button("➕ Nova Conversa"):
        reset_chat()

    for chat_id in saved_conversations:
        if st.sidebar.button(f"Conversa {chat_id}", key=chat_id):
            chat_data = load_chat_history(chat_id)
            st.session_state.chat_id = chat_data["chat_id"]
            st.session_state.session_id = chat_data["session_id"]
            st.session_state.messages = chat_data["messages"]

    if not st.session_state.get("chat_id"):
        if saved_conversations:
            latest_chat_id = saved_conversations[0]
            chat_data = load_chat_history(latest_chat_id)
            st.session_state.chat_id = chat_data["chat_id"]
            st.session_state.session_id = chat_data["session_id"]
            st.session_state.messages = chat_data["messages"]
        else:
            reset_chat()

    st.markdown(f"### ID da Conversa: {st.session_state.chat_id}")

    if not st.session_state.messages:
        welcome_message = "Sou um assistente virtual especializado em agendamentos de reuniões na empresa XYZ."
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
                "user_id": f"user_{st.session_state.username}"
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

# 🚀 **Controla qual página mostrar**
if not st.session_state.authenticated:
    login_page()
else:
    chat_page()
