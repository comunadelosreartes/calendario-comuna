from datetime import datetime, time, timedelta
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN E INTEGRACIÓN CON GOOGLE SHEETS ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def conectar_gsheets():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    # ⚠️ ASEGURATE que este nombre coincida exactamente con el de tu Google Sheets
    sh = gc.open("Base_Turnos_Comuna")
    return sh.sheet1

# Manejo seguro de la conexión
try:
    sheet = conectar_gsheets()
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
    st.info("Revisá que el nombre de la planilla en el código sea exactamente igual al de Google Drive y que esté compartida con el correo de la Service Account.")
    st.stop() # Frena la ejecución para que no tire NameError después

def cargar_turnos():
    try:
        return sheet.get_all_records()
    except Exception:
        return []

def guardar_turnos_completo(turnos):
    sheet.clear()
    cabeceras = ["fecha", "hora", "nombre", "dni", "telefono", "motivo", "detalle", "asistencia"]
    filas = [cabeceras]
    for t in turnos:
        filas.append([
            str(t.get("fecha", "")),
            str(t.get("hora", "")),
            str(t.get("nombre", "")),
            str(t.get("dni", "")),
            str(t.get("telefono", "")),
            str(t.get("motivo", "")),
            str(t.get("detalle", "")),
            str(t.get("asistencia", "Pendiente"))
        ])
    sheet.update(filas)

def agregar_un_turno(nuevo_turno):
    fila = [
        str(nuevo_turno.get("fecha", "")),
        str(nuevo_turno.get("hora", "")),
        str(nuevo_turno.get("nombre", "")),
        str(nuevo_turno.get("dni", "")),
        str(nuevo_turno.get("telefono", "")),
        str(nuevo_turno.get("motivo", "")),
        str(nuevo_turno.get("detalle", "")),
        str(nuevo_turno.get("asistencia", "Pendiente"))
    ]
    sheet.append_row(fila)

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

# --- INTERFAZ GRAFICA ---
st.title("🏛️ Gestión de Turnos - Presidencia Comunal")
st.write("Sistema de turnos y audiencias con la presidenta.")

turnos = cargar_turnos()
menu = st.sidebar.selectbox("Menú", ["Solicitar Turno", "Calendario / Turnos Tomados"])

if menu == "Solicitar Turno":
    st.subheader("📝 Nuevo Pedido de Audiencia")
    
    fecha_seleccionada = st.date_input("Fecha deseada", min_value=datetime.today())
    fecha_str = str(fecha_seleccionada)
    
    horarios_ocupados = [str(t["hora"]) for t in turnos if str(t.get("fecha")) == fecha_str]
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
                    "asistencia": "Pendiente"
                }
                agregar_un_turno(nuevo_turno)
                st.success(f"¡Turno confirmado para el {fecha_str} a las {hora_elegida} hs!")
                st.rerun()
            else:
                st.error("Por favor, completá todos los campos obligatorios.")

elif menu == "Calendario / Turnos Tomados":
    st.subheader("📅 Agenda de Turnos Registrados")
    
    if not turnos:
        st.info("No hay turnos registrados por el momento.")
    else:
        turnos_ordenados = sorted(turnos, key=lambda x: (str(x['fecha']), str(x['hora'])))
        fechas_unicas = sorted(list(set(str(t['fecha']) for t in turnos_ordenados)))
        
        for fecha in fechas_unicas:
            st.markdown(f"### 🗓️ Día: {fecha}")
            turnos_del_dia = [t for t in turnos_ordenados if str(t['fecha']) == fecha]
            
            for t in turnos_del_dia:
                idx_real = turnos.index(t)
                
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
                    
                    st.markdown("---")
                    st.markdown("##### 📌 Control de Asistencia")
                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        if st.button("🟢 Marcar Presente", key=f"pres_{idx_real}"):
                            turnos[idx_real]["asistencia"] = "Presente"
                            guardar_turnos_completo(turnos)
                            st.rerun()
                    with col_a2:
                        if st.button("🔴 Marcar Ausente", key=f"aus_{idx_real}"):
                            turnos[idx_real]["asistencia"] = "Ausente"
                            guardar_turnos_completo(turnos)
                            st.rerun()
                            
                    st.markdown("---")
                    with st.expander("🔄 Reprogramar este turno"):
                        nueva_fecha_input = st.date_input("Nueva Fecha", min_value=datetime.today(), key=f"n_fec_{idx_real}")
                        nueva_fecha_str = str(nueva_fecha_input)
                        
                        ocupados_reprog = [
                            str(item["hora"]) for i_item, item in enumerate(turnos) 
                            if str(item.get("fecha")) == nueva_fecha_str and i_item != idx_real
                        ]
                        libres_reprog = [h for h in generar_horarios_disponibles() if h not in ocupados_reprog]
                        
                        if libres_reprog:
                            nueva_hora_sel = st.selectbox("Nuevo Horario disponible", libres_reprog, key=f"n_hora_{idx_real}")
                            if st.button("Confirmar Reprogramación", key=f"btn_conf_reprog_{idx_real}"):
                                turnos[idx_real]["fecha"] = nueva_fecha_str
                                turnos[idx_real]["hora"] = nueva_hora_sel
                                turnos[idx_real]["asistencia"] = "Pendiente"
                                guardar_turnos_completo(turnos)
                                st.success("¡Turno reprogramado con éxito!")
                                st.rerun()
                        else:
                            st.warning("No hay horarios libres en esa fecha.")

                    st.markdown("---")
                    if st.button("🗑️ Cancelar / Eliminar Turno", key=f"cancelar_{idx_real}"):
                        turnos.pop(idx_real)
                        guardar_turnos_completo(turnos)
                        st.rerun()
                        
            st.markdown("---")
