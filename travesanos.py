# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os

# =================================================================
# 1. CONFIGURACIÓN, ESTILO Y TÍTULO
# =================================================================
st.set_page_config(page_title="AccuraWall | Prediseño de Travesaños", layout="wide")

st.markdown("""
    <style>
    .main > div { padding-left: 2.5rem; padding-right: 2.5rem; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; }
    .result-box { 
        background-color: #f0f7ff; padding: 25px; 
        border-left: 10px solid #003366; border-radius: 8px; margin: 20px 0;
    }
    .guide-box {
        background-color: #fffaf0; padding: 15px;
        border: 1px solid #ff9900; border-radius: 8px; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Prediseño de Travesaños (Horizontales)")
st.markdown("#### **Control de Deflexión Combinada y Especificación de Apoyos de Vidrio**")
st.divider()

# =================================================================
# 2. SIDEBAR: PARÁMETROS TÉCNICOS
# =================================================================
st.sidebar.header("⚙️ Parámetros de Diseño")

with st.sidebar.expander("📐 Geometría y Cargas", expanded=True):
    L = st.number_input("Longitud Travesaño (L) [mm]", value=1500.0)
    U = st.number_input("Altura Vidrio Superior (U) [mm]", value=2500.0)
    q_viento = st.number_input("Carga Viento (q) [kgf/m²]", value=100.0)
    e_vidrio = st.number_input("Espesor Vidrio (e) [mm]", value=12.0)

with st.sidebar.expander("🧪 Material y Calzos", expanded=True):
    # Definimos 'material' aquí para que el motor de cálculo lo reconozca
    material_perfil = st.selectbox("Material del Perfil", 
                                  ["Aluminio 6063 - T6", "Aluminio 6063 - T5", "Acero A42-27ES"])
    
    st.markdown("---")
    # SECCIÓN DE CALZOS CON CÁLCULO EN TIEMPO REAL
    mat_block = st.selectbox("Material del Calzo", ["Neopreno/EPDM/Silicona", "PVC"])
    
    # Cálculo rápido para mostrar bajo el selector
    area_m2_tmp = (L * U) / 1000000
    factor_tmp = 27 if mat_block == "Neopreno/EPDM/Silicona" else 14
    largo_tmp = max(factor_tmp * area_m2_tmp, 100.0 if L > 1219.2 else 50.0)
    
    st.markdown(f'<p class="calc-inline">📏 Largo sugerido: {largo_tmp:.1f} mm</p>', unsafe_allow_html=True)
    
    pos_block = st.radio("Posición de Apoyo", ["L/4 (Preferida)", "L/8 (Alternativa)"])
    
    if st.button("Ver Guía de Calzos"):
        if os.path.exists("setting.jpg"):
            st.image("setting.jpg", caption="Ubicación de tacos de asentamiento")

# =================================================================
# 3. MOTOR DE CÁLCULO (ORDENADO)
# =================================================================
def calcular_todo_metrico():
    # Propiedades del Material
    if "Acero" in material_perfil:
        E, Fcy = 21000000000, 27532337.75
    elif "T6" in material_perfil:
        E, Fcy = 7101002754, 17576739.5
    else: # T5
        E, Fcy = 7101002754, 11249113.3

    L_m, U_m, e_m = L / 1000, U / 1000, e_vidrio / 1000
    
    # 1. Límites de Deflexión
    d_h_lim = (L / 175) if L < 4115 else ((L / 240) + 6.35)
    d_v_lim = min(L / 360, 3.18)

    # 2. Inercias y Módulos
    # Viento (Ix) - Carga Trapezoidal
    ratio_h = U_m / (2 * L_m)
    factor_h = (1 - (4/3) * (ratio_h**2)) if ratio_h < 1 else 1.0
    ix_val = ((5 / 384) * q_viento * U_m * L_m**4 / (E * (d_h_lim/1000))) * factor_h
    
    # Peso (Iy) - Carga Uniforme
    peso_lin = 2500 * e_m * U_m 
    iy_val = (5 / 384) * peso_lin * L_m**4 / (E * (d_v_lim/1000))

    Fb = 0.6 * Fcy
    sx_val = ((1/8 * q_viento * U_m * L_m**2) / Fb) * 100**3
    sy_val = ((1/8 * peso_lin * L_m**2) / Fb) * 100**3

    # 3. Calzos (Métrico y Dureza)
    area_m2 = L_m * U_m
    if mat_block == "Neopreno/EPDM/Silicona":
        sb_len = 27 * area_m2
    else: # PVC
        sb_len = 14 * area_m2
    
    # Mínimos de seguridad
    sb_len = max(sb_len, 100.0 if L > 1219.2 else 50.0)
    sb_pos = L * (0.25 if "L/4" in pos_block else 0.125)

    return (ix_val * 100**4, iy_val * 100**4, sx_val, sy_val, 
            sb_len, sb_pos, area_m2, d_h_lim, d_v_lim)

# Ejecución de cálculos
ix, iy, sx, sy, sb_len, sb_pos, area, d_h, d_v = calcular_todo_metrico()

# =================================================================
# 4. DESPLIEGUE DE RESULTADOS
# =================================================================
st.subheader("📊 Requerimientos Mínimos de Sección")

# Fila 1: Inercias
c1, c2 = st.columns(2)
with c1: st.metric("Inercia Ix (Viento)", f"{ix:.2f} cm⁴", help=f"Límite Δh: {d_h:.2f} mm")
with c2: st.metric("Inercia Iy (Peso Vidrio)", f"{iy:.2f} cm⁴", help=f"Límite Δv: {d_v:.2f} mm")

# Fila 2: Módulos
c3, c4 = st.columns(2)
with c3: st.metric("Módulo Sx (Resistencia)", f"{sx:.2f} cm³")
with c4: st.metric("Módulo Sy (Resistencia)", f"{sy:.2f} cm³")

st.divider()

# Sección de Calzos (Setting Blocks)
st.subheader("🛠️ Especificación de Setting Blocks (Calzos)")
col_sb1, col_sb2 = st.columns(2)

with col_sb1:
    st.markdown(f"""
    <div class="guide-box">
        <h4 style="margin-top:0; color: #ff9900;">Resultados del Cálculo:</h4>
        <ul>
            <li><strong>Área del Vidrio:</strong> {area:.2f} m²</li>
            <li><strong>Material:</strong> {mat_block} (85 ± 5 Sh A°)</li>
            <li><strong>Largo mín. calzo:</strong> {sb_len:.2f} mm</li>
            <li><strong>Ubicar a:</strong> {sb_pos:.1f} mm desde extremos</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col_sb2:
    if os.path.exists("trav.jpg"):
        # Creamos dos sub-columnas con proporción 4:6 (40% y 60%)
        # La imagen se ubica en la primera para que ocupe el 40% del ancho de col_sb2
        sub_col1, sub_col2 = st.columns([4, 6]) 
        with sub_col1:
            # Eliminamos el texto del caption pasando None
            st.image("trav.jpg", caption=None, use_column_width=True)
    else:
        st.info("Sube 'trav.jpg' para ver el diagrama.")

# =================================================================
# 5. GRÁFICOS DE SENSIBILIDAD
# =================================================================
st.subheader("📈 Análisis de Sensibilidad")
L_axis = np.linspace(2000, 6000, 50)
Ix_plt, Iy_plt = [], []

# E para gráfico
E_plt = 21000000000 if "Acero" in material_perfil else 7101002754

for lx in L_axis:
    lx_m = lx / 1000
    df_h = (lx / 175) if lx < 4115 else ((lx / 240) + 6.35)
    df_v = min(lx / 360, 3.18)
    
    # Sensibilidad Ix
    r_h = (U/1000) / (2 * lx_m)
    f_h = (1 - (4/3)*r_h**2) if r_h < 1 else 1.0
    Ix_plt.append(((5/384)*q_viento*(U/1000)*lx_m**4 / (E_plt*(df_h/1000))) * f_h * 100**4)
    
    # Sensibilidad Iy
    p_v = 2500 * (e_vidrio/1000) * (U/1000)
    Iy_plt.append(((5/384)*p_v*lx_m**4 / (E_plt*(df_v/1000))) * 100**4)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
ax1.plot(L_axis, Ix_plt, color='#003366', label='Ix Req.')
ax1.scatter([L], [ix], color='red')
ax1.set_title("Ix vs Longitud (Viento)")
ax1.grid(True, alpha=0.3)

ax2.plot(L_axis, Iy_plt, color='#ff9900', label='Iy Req.')
ax2.scatter([L], [iy], color='red')
ax2.set_title("Iy vs Longitud (Peso)")
ax2.grid(True, alpha=0.3)

st.pyplot(fig)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>AccuraWall Port | Mauricio Riquelme</div>", unsafe_allow_html=True)



from fpdf import FPDF
import base64

def generar_pdf():
    # Usamos FPDF2
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado técnico con Logo (si existe en el servidor)
    if os.path.exists("Logo.png"):
        pdf.image("Logo.png", x=10, y=8, w=33)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Memoria de Cálculo: Travesaños", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 7, "Proyectos Estructurales | Structural Lab", ln=True, align='C')
    pdf.ln(15)

    # Datos del Proyecto (Geometría y Cargas)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, " 1. INFORMACIÓN DEL PROYECTO", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f" Longitud L: {L} mm | Altura U: {U} mm", ln=True)
    pdf.cell(0, 8, f" Carga Viento q: {q_viento} kgf/m2 | Espesor Vidrio e: {e_vidrio} mm", ln=True)
    pdf.ln(5)

    # Resultados Estructurales (Ix, Iy, Sx, Sy)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, " 2. RESULTADOS DE ANÁLISIS", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 8, f" Inercia Ix: {ix:.2f} cm4", border=0)
    pdf.cell(95, 8, f" Módulo Sx: {sx:.2f} cm3", ln=True)
    pdf.cell(95, 8, f" Inercia Iy: {iy:.2f} cm4", border=0)
    pdf.cell(95, 8, f" Módulo Sy: {sy:.2f} cm3", ln=True)
    pdf.ln(5)

    # Calzos (Métrico 27 mm/m2 o 14 mm/m2)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, " 3. ESPECIFICACIÓN DE CALZOS (SETTING BLOCKS)", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f" Material: {mat_block} | Dureza: 85 +/- 5 Sh A", ln=True)
    pdf.cell(0, 8, f" Largo Sugerido: {sb_len:.2f} mm | Posición: {sb_pos:.1f} mm desde extremos", ln=True)
    
    return pdf.output()

# --- INTERFAZ DEL BOTÓN ---
st.sidebar.markdown("---")
if st.sidebar.button("📄 Preparar Reporte PDF"):
    try:
        pdf_bytes = generar_pdf()
        # Codificación para el navegador
        b64 = base64.b64encode(pdf_bytes).decode()
        
        # Estilo del botón de descarga real
        download_button_str = f'''
            <div style="text-align: center; margin-top: 10px;">
                <a href="data:application/pdf;base64,{b64}" download="Memoria_Travesano_L{int(L)}.pdf" 
                   style="background-color: #ff9900; color: white; padding: 12px 20px; text-decoration: none; 
                   border-radius: 5px; font-weight: bold; display: block;">
                   📥 DESCARGAR AHORA
                </a>
            </div>
        '''
        st.sidebar.markdown(download_button_str, unsafe_allow_html=True)
        st.sidebar.info("El archivo está listo. Presiona el botón naranja