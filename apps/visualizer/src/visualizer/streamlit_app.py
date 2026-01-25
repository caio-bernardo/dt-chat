from typing import Any, Sequence

import requests
import streamlit as st

################
# Setup
################

BASE_URL: str = "http://localhost:8000"


@st.fragment
def load_sessions() -> Sequence[str]:
    response = requests.get(f"{BASE_URL}/sessions")
    response.raise_for_status()
    return response.json()


@st.fragment
def load_messages(session_id: str) -> Sequence[dict[str, Any]]:
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    response.raise_for_status()
    return response.json()


@st.fragment
def checkhealth() -> bool:
    response = requests.get(f"{BASE_URL}/health")
    response.raise_for_status()
    return response.status_code == 200


if "backend_online" not in st.session_state:
    st.session_state.backend_online = checkhealth()

if "selected_session" not in st.session_state:
    st.session_state.selected_session = None

if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()


if not st.session_state.backend_online:
    st.error(
        "Falha de conexão com o servidor. Verique se ele está online e no endereço indicado."
    )
    st.stop()

st.set_page_config(
    page_title="Visualizador de Mensagens", page_icon=":email:", layout="wide"
)

###########
# Sidebar
###########

with st.sidebar:
    st.write("Mensagens")
    for i, item in enumerate(st.session_state.sessions):
        if st.button(f"{item}", key=f"session_{i}"):
            st.session_state.selected_session = item

###########
# Header
###########

col1, col2 = st.columns([0.8, 0.2])

with col1:
    st.title("Visualizador de Interações")

###########
# Body
###########
##############################
if st.session_state.selected_session is None:
    st.info("Nenhuma conversa selecionada. Por favor, escolha uma conversa na sidebar.")
else:
    # Carrega as mensagens da conversa selecionada
    conversation = load_messages(st.session_state.selected_session)
    if not conversation:
        st.warning("Não foi possível carregar esta conversa ou ela está vazia.")
    else:
        messages = conversation

        # Ajuste de estilo CSS para garantir espaçamento uniforme entre as mensagens
        st.markdown(
            """
        <style>
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 10px; /* Espaçamento vertical consistente entre as mensagens */
        }

        .human-bubble {            background-color: #003366;
            color: white;
            padding: 10px;
            border-radius: 10px;
            max-width: 60%;
            word-wrap: break-word;
            margin-left: auto; /* Alinha à direita */
            margin-right: 0;
            font-size: 20px
        }

        .ai-bubble {
            background-color: #3a3a3a;
            color: white;
            padding: 10px;
            border-radius: 10px;
            max-width: 60%;
            word-wrap: break-word;
            margin-right: auto; /* Alinha à esquerda */
            margin-left: 0;
            font-size: 20px
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Container para as mensagens
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in messages:
            bubble_class = "human-bubble" if msg["type"] == "human" else "ai-bubble"
            st.markdown(
                f'<div class="{bubble_class}">{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
