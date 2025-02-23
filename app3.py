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

st.title("Chatbot Streamlit")

# Função para listar todas as conversas salvas
def list_saved_conversations():
    return [f.replace(".json", "") for f in os.listdir(CHAT_HISTORY_DIR) if f.endswith(".json")]

# Função para carregar o histórico de conversa com base no ID do chat
def load_chat_history(chat_id):
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"chat_id": chat_id, "messages": [], "session_id": str(uuid.uuid4())}

# Função para salvar a conversa no arquivo
def save_chat_history(chat_id, messages, session_id):
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
    data = {"chat_id": chat_id, "messages": messages, "session_id": session_id}
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Função para resetar a conversa e iniciar uma nova
def reset_chat():
    new_chat_id = str(uuid.uuid4())  # Novo ID para a nova conversa
    st.session_state.chat_id = new_chat_id
    st.session_state.session_id = str(uuid.uuid4())  # Novo session_id exclusivo
    st.session_state.messages = []  # Limpa as mensagens anteriores
    save_chat_history(new_chat_id, [], st.session_state.session_id)  # Cria um novo arquivo para a conversa

# Verifica se o chat_id está presente, caso contrário, inicia uma nova conversa
if "chat_id" not in st.session_state:
    st.session_state.chat_id = None  # Nenhuma conversa ativa inicialmente

# Lista todas as conversas salvas no sidebar
st.sidebar.subheader("📜 Históricos de Conversa")
saved_conversations = list_saved_conversations()

# Botão para iniciar uma nova conversa
if st.sidebar.button("➕ Nova Conversa"):
    reset_chat()

# Se o usuário selecionar uma conversa, carrega os dados dessa conversa
selected_chat = st.sidebar.selectbox("Selecione uma conversa:", saved_conversations, index=None, placeholder="Escolha uma conversa...")

if selected_chat and selected_chat != st.session_state.get("chat_id"):
    chat_data = load_chat_history(selected_chat)
    st.session_state.chat_id = chat_data["chat_id"]
    st.session_state.session_id = chat_data["session_id"]
    st.session_state.messages = chat_data["messages"]

# Se não houver conversa ativa, cria uma nova conversa
if not st.session_state.get("chat_id"):
    reset_chat()

# Exibe uma mensagem de boas-vindas se não houver histórico de mensagens
if not st.session_state.messages:
    welcome_message = "Sou um assistente virtual especializado em agendamentos de reuniões na empresa XYZ. Estou aqui para ajudá-lo a gerenciar seus compromissos de forma eficiente, agendando, reagendando, listando ou cancelando reuniões conforme a sua necessidade. Se tiver alguma dúvida ou precisar de assistência, é só me avisar!"
    st.session_state.messages.append({"role": "assistant", "content": welcome_message})
    save_chat_history(st.session_state.chat_id, st.session_state.messages, st.session_state.session_id)

# Exibe as mensagens anteriores corretamente
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Captura a entrada do usuário para uma nova mensagem
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
            "session_id": st.session_state.session_id
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            full_response = response_data[0].get("output", "Erro ao obter resposta.")
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão com o servidor. Por favor, tente novamente mais tarde.")
            full_response = "Erro ao buscar a resposta."
        
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_chat_history(st.session_state.chat_id, st.session_state.messages, st.session_state.session_id)  # Salva a conversa
