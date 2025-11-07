import streamlit as st
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
import hashlib



st.set_page_config(page_title="SOFT-IA 🤖", layout="wide")  

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

#Lugar donde se van a guardar los usuarios
CARPETA_USUARIOS = "usuarios"
os.makedirs(CARPETA_USUARIOS, exist_ok=True)

#Ayuda a cifrar las contraseñas
def cifrar_contrasena(contrasena):
    return hashlib.sha256(contrasena.encode()).hexdigest()

#Devolucion del JSON de un usuario
def archivo_usuario(nombre_usuario):
    return os.path.join(CARPETA_USUARIOS, f"{nombre_usuario}.json")

#Comprobación de que el usuario existe
def usuario_existe(nombre_usuario):
    return os.path.exists(archivo_usuario(nombre_usuario))

#Creacion de un nuevo usuario
def crear_usuario(nombre_usuario, contrasena):
    if usuario_existe(nombre_usuario):
        return False
    with open(archivo_usuario(nombre_usuario), "w") as f:
        json.dump({"contrasena": cifrar_contrasena(contrasena), "mensajes": []}, f, indent=2)
    return True

#Verifica que la contraseña sea correcta
def verificar_usuario(nombre_usuario, contrasena):
    if not usuario_existe(nombre_usuario):
        return False
    with open(archivo_usuario(nombre_usuario), "r") as f:
        datos = json.load(f)
    return datos["contrasena"] == cifrar_contrasena(contrasena)


def cargar_mensajes(nombre_usuario):
    with open(archivo_usuario(nombre_usuario), "r") as f:
        datos = json.load(f)
    return datos.get("mensajes", [])


def guardar_mensajes(nombre_usuario, mensajes):
    with open(archivo_usuario(nombre_usuario), "r") as f:
        datos = json.load(f)
    datos["mensajes"] = mensajes
    with open(archivo_usuario(nombre_usuario), "w") as f:
        json.dump(datos, f, indent=2)

# Estado de sesión
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Selección de modo de uso
if not st.session_state.logueado:
    st.title("💬 SOFT-IA")
    modo = st.radio("Modo de uso", ["Invitado", "Registrarse/Iniciar sesión"])

    # Modo invitado
    if modo == "Invitado":
        if st.button("Usar como invitado"):
            st.session_state.logueado = True
            st.session_state.usuario = None 
            st.session_state.mensajes = []
            st.success("Estás usando el chat como invitado (los mensajes no se guardarán)")
            st.rerun()

    # Modo registro / login
    else:
        # Formulario de registro
        with st.form("formulario_registro"):
            st.subheader("Crear cuenta")
            nuevo_usuario = st.text_input("Usuario", key="reg_user")
            nueva_contrasena = st.text_input("Contraseña", type="password", key="reg_pass")
            repetir_contrasena = st.text_input("Repetir Contraseña", type="password", key="reg_pass2")
            boton_registro = st.form_submit_button("Crear cuenta")

            if boton_registro:
                if not nuevo_usuario or not nueva_contrasena:
                    st.warning("Completa todos los campos")
                elif nueva_contrasena != repetir_contrasena:
                    st.error("Las contraseñas no coinciden")
                elif usuario_existe(nuevo_usuario):
                    st.error("El usuario ya existe")
                else:
                    crear_usuario(nuevo_usuario, nueva_contrasena)
                    st.session_state.logueado = True
                    st.session_state.usuario = nuevo_usuario
                    st.session_state.mensajes = cargar_mensajes(nuevo_usuario)
                    st.success("Usuario creado correctamente! Ya puedes usar el chat.")
                    st.rerun()

        # Formulario de login
        with st.form("formulario_login"):
            st.subheader("Iniciar sesión")
            nombre_usuario = st.text_input("Usuario", key="login_user")
            contrasena_usuario = st.text_input("Contraseña", type="password", key="login_pass")
            boton_login = st.form_submit_button("Iniciar sesión")

            if boton_login:
                if verificar_usuario(nombre_usuario, contrasena_usuario):
                    st.session_state.logueado = True
                    st.session_state.usuario = nombre_usuario
                    st.session_state.mensajes = cargar_mensajes(nombre_usuario)
                    st.success(f"Bienvenido {nombre_usuario} 👋")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

# -----------------------------
# Chat principal
# -----------------------------
if st.session_state.logueado:
    st.sidebar.write(f"👤 Usuario: {st.session_state.usuario or 'Invitado'}")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.logueado = False
        st.session_state.usuario = None
        st.session_state.mensajes = []
        st.rerun()

    st.title("🤖 SOFT IA")

    # Inicializar modelo Gemini
    if "modelo" not in st.session_state:
        st.session_state.modelo = genai.GenerativeModel('gemini-2.5-pro')

    # Buscador de mensajes
    busqueda = st.sidebar.text_input("🔍 Buscar en tu conversación")
    mensajes_a_mostrar = (
        [m for m in st.session_state.mensajes if busqueda.lower() in m["content"].lower()]
        if busqueda else st.session_state.mensajes
    )

    # Mostrar mensajes filtrados
    for mensaje in mensajes_a_mostrar:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    # Input de chat
    if mensaje_usuario := st.chat_input("¿En qué puedo ayudarte hoy?"):
        st.session_state.mensajes.append({"role": "user", "content": mensaje_usuario})
        with st.chat_message("user"):
            st.markdown(mensaje_usuario)

        with st.spinner("Pensando..."):
            respuesta = st.session_state.modelo.generate_content(mensaje_usuario)
            texto_respuesta = respuesta.text

        st.session_state.mensajes.append({"role": "assistant", "content": texto_respuesta})
        with st.chat_message("assistant"):
            st.markdown(texto_respuesta)

        # Guardar solo si es usuario registrado
        if st.session_state.usuario:
            guardar_mensajes(st.session_state.usuario, st.session_state.mensajes)
