from datetime import datetime
import json
import os
import streamlit as st

# Archivo donde guardaremos los turnos
DB_FILE = "turnos.json"

def cargar_turnos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_turnos(turnos):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(turnos, f, ensure_ascii=False, indent=4)

st.title("🏛️ Gestión de Turnos - Presidencia Comunal")
st.write("Seleccioná un día y horario disponible para solicitar una audiencia con la presidenta.")

# Cargar turnos existentes
turnos = cargar_turnos()

# Menú lateral para elegir vista
menu = st.sidebar.selectbox("Menú", ["Solicitar Turno", "Ver Turnos (Admin)"])

if menu == "Solicitar Turno":
    st.subheader("📝 Nuevo Pedido de Audiencia")
    
    # Creamos un formulario (esto permite limpiar los campos automáticamente al enviar)
    with st.form("form_turno", clear_on_submit=True):
        nombre = st.text_input("Nombre y Apellido")
        dni = st.text_input("DNI")
        motivo = st.selectbox("Motivo de la reunión", ["Obras Públicas", "Acción Social", "Audiencia General", "Reclamos Varios"])
        detalle = st.text_area("Breve detalle del tema")
        
        fecha = st.date_input("Fecha deseada", min_value=datetime.today())
        hora = st.time_input("Hora sugerida")
        
        # El botón de envío dentro del form se llama form_submit_button
        enviado = st.form_submit_button("Confirmar Turno")
        
        if enviado:
            if nombre and dni:
                nuevo_turno = {
                    "nombre": nombre,
                    "dni": dni,
                    "motivo": motivo,
                    "detalle": detalle,
                    "fecha": str(fecha),
                    "hora": str(hora),
                    "estado": "Pendiente"
                }
                turnos.append(nuevo_turno)
                guardar_turnos(turnos)
                st.success("¡Turno solicitado con éxito! Nos pondremos en contacto para confirmarlo.")
            else:
                st.error("Por favor, completá al menos tu Nombre y DNI.")

elif menu == "Ver Turnos (Admin)":
    st.subheader("🔒 Panel de Control - Turnos Registrados")
    
    password = st.text_input("Contraseña de Administrador", type="password")
    
    if password == "comuna2026": 
        if not turnos:
            st.info("No hay turnos registrados por el momento.")
        else:
            for i, t in enumerate(turnos):
                with st.expander(f"{t['fecha']} {t['hora']} - {t['nombre']} ({t['motivo']})"):
                    st.write(f"**DNI:** {t['dni']}")
                    st.write(f"**Detalle:** {t['detalle']}")
                    st.write(f"**Estado:** {t['estado']}")
                    
                    if st.button(f"Aprobar turno {i}", key=f"aprobar_{i}"):
                        turnos[i]["estado"] = "Aprobado"
                        guardar_turnos(turnos)
                        st.rerun()
                    
                    if st.button(f"Cancelar turno {i}", key=f"cancelar_{i}"):
                        turnos.pop(i)
                        guardar_turnos(turnos)
                        st.rerun()
    elif password:
        st.error("Contraseña incorrecta")
