from datetime import datetime, time, timedelta
import json
import os
import streamlit as st

DB_FILE = "turnos.json"

def cargar_turnos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_turnos(turnos):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(turnos, f, ensure_ascii=False, indent=4)

# Función para generar los horarios de 8:00 a 13:00 cada 30 minutos
def generar_horarios_disponibles():
    horarios = []
    inicio = time(8, 0)
    fin = time(13, 0)
    actual = datetime.combine(datetime.today(), inicio)
    limite = datetime.combine(datetime.today(), fin)
    
    while actual <= limite:
        horarios.append(actual.strftime("%H:%M"))
        actual += timedelta(minutes=30)
    return horarios

st.title("🏛️ Gestión de Turnos - Presidencia Comunal")
st.write("Sistema de turnos y audiencias con la presidenta.")

turnos = cargar_turnos()
menu = st.sidebar.selectbox("Menú", ["Solicitar Turno", "Ver Turnos (Admin)"])

if menu == "Solicitar Turno":
    st.subheader("📝 Nuevo Pedido de Audiencia")
    
    # 1. Primero elegimos la fecha para ver qué horarios quedan libres en ese día
    fecha_seleccionada = st.date_input("Fecha deseada", min_value=datetime.today())
    fecha_str = str(fecha_seleccionada)
    
    # Filtrar turnos ya ocupados para la fecha elegida
    horarios_ocupados = [t["hora"] for t in turnos if t.get("fecha") == fecha_str]
    
    # Generar todos los horarios posibles y filtrar los libres
    todos_los_horarios = generar_horarios_disponibles()
    horarios_libres = [h for h in todos_los_horarios if h not in horarios_ocupados]
    
    # Mostrar estado de disponibilidad al operador/vecino
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🟢 Horarios Disponibles:**")
        if horarios_libres:
            st.write(", ".join(horarios_libres))
        else:
            st.warning("No hay turnos libres para esta fecha.")
            
    with col2:
        st.markdown("**🔴 Horarios Ocupados:**")
        if horarios_ocupados:
            st.write(", ".join(horarios_ocupados))
        else:
            st.info("Ningún turno ocupado aún.")
    st.markdown("---")
    
    # Formulario de carga
    with st.form("form_turno", clear_on_submit=True):
        nombre = st.text_input("Nombre y Apellido")
        dni = st.text_input("DNI")
        motivo = st.selectbox("Motivo de la reunión", ["Obras Públicas", "Acción Social", "Audiencia General", "Reclamos Varios"])
        detalle = st.text_area("Breve detalle del tema")
        
        # Selector de hora basado únicamente en los turnos libres
        if horarios_libres:
            hora_elegida = st.selectbox("Seleccionar Hora (Bloques de 30 min)", horarios_libres)
        else:
            hora_elegida = None
            st.error("Seleccione otra fecha, no quedan horarios disponibles.")
        
        enviado = st.form_submit_button("Confirmar Turno")
        
        if enviado:
            if nombre and dni and hora_elegida:
                nuevo_turno = {
                    "nombre": nombre,
                    "dni": dni,
                    "motivo": motivo,
                    "detalle": detalle,
                    "fecha": fecha_str,
                    "hora": hora_elegida,
                    "estado": "Pendiente"
                }
                turnos.append(nuevo_turno)
                guardar_turnos(turnos)
                st.success(f"¡Turno confirmado para el {fecha_str} a las {hora_elegida} hs!")
                st.rerun()
            else:
                st.error("Por favor, completá todos los campos obligatorios y asegurate de elegir un horario válido.")

elif menu == "Ver Turnos (Admin)":
    st.subheader("🔒 Panel de Control - Turnos Registrados")
    
    password = st.text_input("Contraseña de Administrador", type="password")
    
    if password == "comuna2026": 
        if not turnos:
            st.info("No hay turnos registrados por el momento.")
        else:
            for i, t in enumerate(turnos):
                with st.expander(f"{t['fecha']} {t['hora']} hs - {t['nombre']} ({t['motivo']})"):
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
