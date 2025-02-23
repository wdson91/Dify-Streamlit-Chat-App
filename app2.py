import requests
import streamlit as st
import json

dify_api_key = "app-4MGk7btuUXKkE04wvxEJuMop"
url = "https://novoprojeto-dify.aidvjr.easypanel.host/v1/chat-messages"

st.title("Dify Streamlit App")

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = "3cbe8d5a-6254-4192-b09a-3733f13ac1aa"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe mensagens anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Enter your question")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("⌛ Carregando resposta...")

        headers = {
            "Authorization": f"Bearer {dify_api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }

        payload = {
             "inputs": {
          # Variável a ser armazenada
        
    },
            "query": prompt,
            "response_mode": "streaming",
            "conversation_id": "3cbe8d5a-6254-4192-b09a-3733f13ac1aa",
            "user": "aianytime",
            "files": []
        }

        full_response = ""

        try:
            with requests.post(url, headers=headers, json=payload, stream=True) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line and line.startswith(b"data: "):
                        try:
                            decoded_line = line.decode("utf-8").replace("data: ", "")
                            event_data = json.loads(decoded_line)
                            if event_data.get("event") in ["message", "agent_thought"]:
                                
                                full_response += event_data.get("answer", event_data.get("thought", ""))
                                print(full_response)
                                message_placeholder.markdown(full_response)
                            elif event_data.get("event") == "message_end":
                                st.session_state.conversation_id = event_data.get("conversation_id", st.session_state.conversation_id)
                                break
                        except json.JSONDecodeError as e:
                            print("Erro ao decodificar JSON:", e)
        except requests.exceptions.RequestException as e:
            st.error(f"Ocorreu um erro na requisição: {e}")
            full_response = "Erro ao buscar a resposta."

        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
