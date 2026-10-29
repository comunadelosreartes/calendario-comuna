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
menu = st.sidebar.selectbox("Menú", ["Solicitar Turno", "Calendario / Turnos Tomados"])

if menu == "Solicitar Turno":
    st.subheader("📝 Nuevo Pedido de Audiencia")
    
    fecha_seleccionada = st.date_input("Fecha deseada", min_value=datetime.today())
    fecha_str = str(fecha_seleccionada)
    
    # Filtrar turnos ya ocupados para la fecha elegida
    horarios_ocupados = [t["hora"] for t in turnos if t.get("fecha") == fecha_str]
    
    todos_los_horarios = generar_horarios_disponibles()
    horarios_libres = [h for h in todos_los_horarios if h not in horarios_ocupados]
    
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
    
    with st.form("form_turno", clear_on_submit=True):
        nombre = st.text_input("Nombre y Apellido")
        dni = st.text_input("DNI")
        motivo = st.selectbox("Motivo de la reunión", ["Obras Públicas", "Acción Social", "Audiencia General", "Reclamos Varios"])
        detalle = st.text_area("Breve detalle del tema")
        
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
                st.error("Por favor, completá todos los campos obligatorios.")

elif menu == "Calendario / Turnos Tomados":
    st.subheader("📅 Agenda de Turnos Registrados")
    
    if not turnos:
        st.info("No hay turnos registrados por el momento.")
    else:
        # Ordenar todos los turnos cronológicamente por fecha y hora
        turnos_ordenados = sorted(turnos, key=lambda x: (x['fecha'], x['hora']))
        
        # Agrupar visualmente por fecha
        fechas_unicas = sorted(list(set(t['fecha'] for t in turnos_ordenados)))
        
        for fecha in fechas_unicas:
            st.markdown(f"### 🗓️ Día: {fecha}")
            turnos_del_dia = [t for t in turnos_ordenados if t['fecha'] == fecha]
            
            for t in turnos_del_dia:
                # Buscamos el índice original en la lista general para poder borrarlo o modificarlo si hace falta
                idx_real = turnos.index(t)
                
                # Diseño estilo tarjeta resumida con el horario y el nombre
                with st.expander(f"⏰ {t['hora']} hs — **{t['nombre']}** ({t['motivo']})"):
                    st.write(f"**DNI:** {t['dni']}")
                    st.write(f"**Detalle del tema:** {t['detalle']}")
                    st.write(f"**Estado:** {t['estado']}")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if t['estado'] != "Aprobado":
                            if st.button("Aprobar Turno", key=f"aprobar_{idx_real}"):
                                turnos[idx_real]["estado"] = "Aprobado"
                                guardar_turnos(turnos)
                                st.rerun()
                    with col_btn2:
                        if st.button("Cancelar / Eliminar Turno", key=f"cancelar_{idx_real}"):
                            turnos.pop(idx_real)
                            guardar_turnos(turnos)
                            st.rerun()
            st.markdown("---")
