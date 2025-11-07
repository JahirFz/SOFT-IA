import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv


#Cargar variables de entorno
load_dotenv()


#Configurar la API de Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


#Configuración de la Página
st.set_page_config(page_title="SOFT-IA 🤖", layout="centered")
st.title("🤖 SOFT IA")


#Lógica del Chat
if "model" not in st.session_state:
    st.session_state.model = genai.GenerativeModel('gemini-2.5-pro')


if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)


    with st.spinner("Pensando..."):
        response = st.session_state.model.generate_content(prompt)
        response_text = response.text


        st.session_state.messages.append({"role": "assistant", "content": response_text})
        with st.chat_message("assistant"):
            st.markdown(response_text)