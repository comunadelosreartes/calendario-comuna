from datetime import datetime, time, timedelta
import streamlit as st
import requests

# 🌐 PEGA AQUÍ LA URL DE TU GOOGLE APPS SCRIPT
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyVRhXYs4SA3LJRwQKuLaPG3OOxmJk1VMxlZUToTNOEF8Ml0DxYg5niZQW8RQ4kvDm5zg/exec"

def formatear_fecha_amigable(fecha_str):
    """Convierte '2026-10-29T03:00:00.000Z' o '2026-10-29' en 'Miércoles, 29 de octubre de 2026'"""
    if not fecha_str:
        return ""
    try:
        f_limpia = str(fecha_str).split("T")[0]
        dt = datetime.strptime(f_limpia, "%Y-%m-%d")
        
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        
        nombre_dia = dias[dt.weekday()]
        nombre_mes = meses[dt.month - 1]
        
        return f"{nombre_dia}, {dt.day} de {nombre_mes} de {dt.year}"
    except Exception:
        return str(fecha_str)

def formatear_hora_amigable(hora_str):
    """Limpia la hora por si viene con formato largo de Google Sheets"""
    if not hora_str:
        return ""
    try:
        s = str(hora_str)
        if "T" in s:
            parte_hora = s.split("T")[1].split("Z")[0]
            h, m, *_ = parte_hora.split(":")
            return f"{h}:{m}"
        return s[:5]
    except Exception:
        return str(hora_str)

def cargar_turnos():
    try:
        response = requests.get(WEB_APP_URL)
        if response.ok:
            return response.json()
        return []
    except Exception:
        return []

def guardar_turnos_completo(turnos):
    try:
        payload = {
            "action": "update_all",
            "turnos": turnos
        }
        requests.post(WEB_APP_URL, json=payload)
    except Exception as e:
        st.error(f"Error al actualizar la base de datos: {e}")

def agregar_un_turno(nuevo_turno):
    try:
        requests.post(WEB_APP_URL, json=nuevo_turno)
    except Exception as e:
        st.error(f"Error al guardar el turno: {e}")

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
menu = st.sidebar.selectbox("Menú", ["Solicitar Turno", "Calendario / Turnos Tomados", "🖨️ Imprimir Agenda del Día"])

if menu == "Solicitar Turno":
    st.subheader("📝 Nuevo Pedido de Audiencia")
    
    fecha_seleccionada = st.date_input("Fecha deseada", min_value=datetime.today())
    fecha_str = str(fecha_seleccionada)
    
    horarios_ocupados = [formatear_hora_amigable(t["hora"]) for t in turnos if str(t.get("fecha", "")).split("T")[0] == fecha_str]
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
        turnos_ordenados = sorted(turnos, key=lambda x: (str(x.get('fecha', '')).split('T')[0], str(x.get('hora', ''))))
        fechas_unicas = sorted(list(set(str(t.get('fecha', '')).split('T')[0] for t in turnos_ordenados)))
        
        for fecha_iso in fechas_unicas:
            fecha_amigable = formatear_fecha_amigable(fecha_iso)
            st.markdown(f"### 🗓️ {fecha_amigable}")
            turnos_del_dia = [t for t in turnos_ordenados if str(t.get('fecha', '')).split('T')[0] == fecha_iso]
            
            for t in turnos_del_dia:
                idx_real = turnos.index(t)
                hora_limpia = formatear_hora_amigable(t.get('hora', ''))
                
                estado_asis = t.get('asistencia', 'Pendiente')
                icono_estado = "⏳"
                if estado_asis == "Presente":
                    icono_estado = "✅"
                elif estado_asis == "Ausente":
                    icono_estado = "❌"
                
                with st.expander(f"{icono_estado} {hora_limpia} hs — **{t.get('nombre', '')}** ({t.get('motivo', '')}) [{estado_asis}]"):
                    st.write(f"**DNI:** {t.get('dni', '')}")
                    st.write(f"**Teléfono:** {t.get('telefono', 'No especificado')}")
                    st.write(f"**Detalle del tema:** {t.get('detalle', '')}")
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
                            formatear_hora_amigable(item.get("hora", "")) for i_item, item in enumerate(turnos) 
                            if str(item.get("fecha", "")).split("T")[0] == nueva_fecha_str and i_item != idx_real
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

elif menu == "🖨️ Imprimir Agenda del Día":
    st.markdown("""
        <style>
        @media print {
            [data-testid="stSidebar"], header, footer, button {
                display: none !important;
            }
            [data-testid="stMain"] {
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            body {
                background-color: white;
            }
        }
        .hoja-impresion {
            background: white;
            padding: 30px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            color: #333;
            font-family: sans-serif;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("🖨️ Impresión de Agenda de Audiencias")
    st.write("Elegí la fecha para generar el parte diario listo para imprimir.")
    
    fecha_imprimir = st.date_input("Seleccionar Fecha", min_value=datetime.today(), key="input_fecha_imprimir")
    fecha_imp_str = str(fecha_imprimir)
    fecha_imp_amigable = formatear_fecha_amigable(fecha_imp_str)
    
    st.markdown("---")
    
    if not turnos:
        html_final = f"""
        <div class="hoja-impresion">
            <h2 style="text-align: center; margin-bottom: 0; color: #111;">COMUNA DE LOS REARTES</h2>
            <p style="text-align: center; font-size: 14px; color: #666; margin-top: 5px;">Presidencia Comunal — Agenda de Audiencias</p>
            <hr style="border: 1px solid #333; margin: 20px 0;">
            <p style="font-size: 16px;"><strong>Fecha:</strong> {fecha_imp_amigable}</p>
            <p style="color: #888;">No hay turnos registrados en el sistema.</p>
        </div>
        """
    else:
        turnos_dia = [t for t in turnos if str(t.get('fecha', '')).split('T')[0] == fecha_imp_str]
        turnos_dia_ordenados = sorted(turnos_dia, key=lambda x: str(x.get('hora', '')))
        
        filas_html = ""
        if not turnos_dia_ordenados:
            filas_html = "<tr><td colspan='4' style='text-align: center; padding: 20px; color: #666;'>No hay audiencias programadas para esta fecha.</td></tr>"
        else:
            for t in turnos_dia_ordenados:
                hora_limpia = formatear_hora_amigable(t.get('hora', ''))
                nombre = t.get('nombre', '')
                dni = t.get('dni', '')
                tel = t.get('telefono', 'Sin tel')
                motivo = t.get('motivo', '')
                detalle = t.get('detalle', 'Sin detalles')
                
                filas_html += f"""
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="border: 1px solid #ddd; padding: 10px; text-align: center; font-weight: bold; font-size: 15px;">{hora_limpia} hs</td>
                    <td style="border: 1px solid #ddd; padding: 10px;">
                        <strong>{nombre}</strong><br>
                        <span style="font-size: 12px; color: #555;">DNI: {dni} | Tel: {tel}</span>
                    </td>
                    <td style="border: 1px solid #ddd; padding: 10px;">
                        <strong>{motivo}</strong><br>
                        <span style="font-size: 12px; color: #555;">{detalle}</span>
                    </td>
                    <td style="border: 1px solid #ddd; padding: 10px; text-align: center; font-size: 12px;">
                        [ &nbsp; ] Presente<br>[ &nbsp; ] Ausente
                    </td>
                </tr>
                """

        html_final = f"""
        <div class="hoja-impresion">
            <h2 style="text-align: center; margin-bottom: 0; color: #111;">COMUNA DE LOS REARTES</h2>
            <p style="text-align: center; font-size: 14px; color: #666; margin-top: 5px;">Presidencia Comunal — Agenda de Audiencias</p>
            <hr style="border: 1px solid #333; margin: 20px 0;">
            <p style="font-size: 16px;"><strong>Fecha:</strong> {fecha_imp_amigable}</p>
            <p style="font-size: 16px;"><strong>Total de audiencias programadas:</strong> {len(turnos_dia_ordenados)}</p>
            <br>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 10px;">
                <thead>
                    <tr style="background-color: #f2f2f2; border-bottom: 2px solid #333;">
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: center; width: 15%;">Hora</th>
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: left; width: 30%;">Vecino / DNI / Teléfono</th>
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: left; width: 35%;">Motivo / Detalle</th>
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: center; width: 20%;">Asistencia</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                </tbody>
            </table>
        </div>
        """

    # Forzar renderizado HTML puro sin que Markdown lo interprete mal
    st.components.v1.html(html_final, height=600, scrolling=True)
            
    st.markdown("---")
    st.info("💡 **Para imprimir:** Presioná **Ctrl + P** en tu teclado. El sistema ocultará automáticamente los menús y dejará solo la planilla prolija lista para la impresora o PDF.")
