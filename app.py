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
        telefono = st.text_input("Número Telefónico (Ej: 3546...)")
        motivo = st.selectbox("Motivo de la reunión", ["Obras Públicas", "Acción Social", "Audiencia General", "Reclamos Varios"])
        detalle = st.text_area("Breve detalle del tema")
        
        if horarios_libres:
            hora_elegida = st.selectbox("Seleccionar Hora (Bloques de 30 min)", horarios_libres)
        else:
            hora_elegida = None
            st.error("Seleccione otra fecha, no quedan horarios disponibles.")
        
        enviado = st.form_submit_button("Confirmar Turno")
        
        if enviado:
            if nombre and dni and telefono and hora_elegida:
                nuevo_turno = {
                    "nombre": nombre,
                    "dni": dni,
                    "telefono": telefono,
                    "motivo": motivo,
                    "detalle": detalle,
                    "fecha": fecha_str,
                    "hora": hora_elegida,
                    "asistencia": "Pendiente" # <--- Estado inicial de asistencia
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
        turnos_ordenados = sorted(turnos, key=lambda x: (x['fecha'], x['hora']))
        fechas_unicas = sorted(list(set(t['fecha'] for t in turnos_ordenados)))
        
        for fecha in fechas_unicas:
            st.markdown(f"### 🗓️ Día: {fecha}")
            turnos_del_dia = [t for t in turnos_ordenados if t['fecha'] == fecha]
            
            for t in turnos_del_dia:
                idx_real = turnos.index(t)
                
                # Definir un emoji indicador según la asistencia
                estado_asis = t.get('asistencia', 'Pendiente')
                icono_estado = "⏳"
                if estado_asis == "Presente":
                    icono_estado = "✅"
                elif estado_asis == "Ausente":
                    icono_estado = "❌"
                
                with st.expander(f"{icono_estado} {t['hora']} hs — **{t['nombre']}** ({t['motivo']}) [{estado_asis}]"):
                    st.write(f"**DNI:** {t['dni']}")
                    st.write(f"**Teléfono:** {t.get('telefono', 'No especificado')}")
                    st.write(f"**Detalle del tema:** {t['detalle']}")
                    st.write(f"**Asistencia:** {estado_asis}")
                    
                    # 1. Botones para marcar asistencia
                    st.markdown("---")
                    st.markdown("##### 📌 Control de Asistencia")
                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        if st.button("🟢 Marcar Presente", key=f"pres_{idx_real}"):
                            turnos[idx_real]["asistencia"] = "Presente"
                            guardar_turnos(turnos)
                            st.rerun()
                    with col_a2:
                        if st.button("🔴 Marcar Ausente", key=f"aus_{idx_real}"):
                            turnos[idx_real]["asistencia"] = "Ausente"
                            guardar_turnos(turnos)
                            st.rerun()
                            
                    # 2. Sección para Reprogramar el turno sin borrarlo
                    st.markdown("---")
                    with st.expander("🔄 Reprogramar este turno"):
                        nueva_fecha_input = st.date_input("Nueva Fecha", min_value=datetime.today(), key=f"n_fec_{idx_real}")
                        nueva_fecha_str = str(nueva_fecha_input)
                        
                        # Buscar horarios ocupados en la nueva fecha (excluyendo este mismo turno si fuera el mismo día)
                        ocupados_reprog = [
                            item["hora"] for i_item, item in enumerate(turnos) 
                            if item.get("fecha") == nueva_fecha_str and i_item != idx_real
                        ]
                        libres_reprog = [h for h in generar_horarios_disponibles() if h not in ocupados_reprog]
                        
                        if libres_reprog:
                            nueva_hora_sel = st.selectbox("Nuevo Horario disponible", libres_reprog, key=f"n_hora_{idx_real}")
                            if st.button("Confirmar Reprogramación", key=f"btn_conf_reprog_{idx_real}"):
                                turnos[idx_real]["fecha"] = nueva_fecha_str
                                turnos[idx_real]["hora"] = nueva_hora_sel
                                turnos[idx_real]["asistencia"] = "Pendiente" # Vuelve a pendiente al reprogramar
                                guardar_turnos(turnos)
                                st.success("¡Turno reprogramado con éxito!")
                                st.rerun()
                        else:
                            st.warning("No hay horarios libres en esa fecha.")

                    # 3. Botón para cancelar / eliminar el turno
                    st.markdown("---")
                    if st.button("🗑️ Cancelar / Eliminar Turno", key=f"cancelar_{idx_real}"):
                        turnos.pop(idx_real)
                        guardar_turnos(turnos)
                        st.rerun()
                        
            st.markdown("---")
