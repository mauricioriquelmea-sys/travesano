# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os
import base64
from fpdf import FPDF

# =================================================================
# 1. CONFIGURACIÓN Y ESTILO
# =================================================================
st.set_page_config(page_title="AccuraWall | Mauricio Riquelme", layout="wide")

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
    .calc-inline { color: #003366; font-weight: bold; font-size: 0.9rem; margin-top: -10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Prediseño de Travesaños (Horizontales)")
st.divider()

# =================================================================
# 2. SIDEBAR: PARÁMETROS Y CÁLCULO DE CALZOS
# =================================================================
st.sidebar.header("⚙️ Parámetros de Diseño")

with st.sidebar.expander("📐 Geometría y Cargas", expanded=True):
    L = st.number_input("Longitud Travesaño (L) [mm]", value=1500.0)
    U = st.number_input("Altura Vidrio Superior (U) [mm]", value=2500.0)
    q_viento = st.number_input("Carga Viento (q) [kgf/m²]", value=100.0)
    e_vidrio = st.number_input("Espesor Vidrio (e) [mm]", value=12.0)

with st.sidebar.expander("🧪 Material y Calzos", expanded=True):
    material_perfil = st.selectbox("Material del Perfil", 
                                  ["Aluminio 6063 - T6", "Aluminio 6063 - T5", "Acero A42-27ES"])
    
    st.markdown("---")
    mat_block = st.selectbox("Material del Calzo", ["Neopreno/EPDM/Silicona", "PVC"])
    
    # Cálculo métrico inmediato de calzos (27 mm/m2 o 14 mm/m2)
    area_m2 = (L * U) / 1_000_000
    factor_sb = 27 if mat_block == "Neopreno/EPDM/Silicona" else 14
    sb_len_sug = max(factor_sb * area_m2, 100.0 if L > 1219.2 else 50.0)
    
    st.markdown(f'<p class="calc-inline">📏 Largo sugerido: {sb_len_sug:.1f} mm</p>', unsafe_allow_html=True)
    
    pos_block = st.radio("Posición de Apoyo", ["L/4 (Preferida)", "L/8 (Alternativa)"])
    
    if st.button("Ver Guía de Calzos"):
        if os.path.exists("setting.jpg"):
            st.image("setting.jpg", caption="Esquema de Apoyos")

# =================================================================
# 3. MOTOR DE CÁLCULO
# =================================================================
def ejecutar_calculos():
    # Propiedades del Material
    if "Acero" in material_perfil:
        E, Fcy = 21000000000, 27532337.75
    elif "T6" in material_perfil:
        E, Fcy = 7101002754, 17576739.5
    else: # T5
        E, Fcy = 7101002754, 11249113.3

    L_m, U_m, e_m = L/1000, U/1000, e_vidrio/1000
    df_h_adm = (L/175) if L < 4115 else ((L/240) + 6.35)
    df_v_adm = min(L/360, 3.18)

    # Ix (Viento - Trapezoidal)
    ratio = U_m / (2 * L_m)
    f_ix = (1 - (4/3)*(ratio**2)) if ratio < 1 else 1.0
    ix_req = ((5/384) * q_viento * U_m * L_m**4 / (E * (df_h_adm/1000))) * f_ix
    
    # Iy (Peso - Uniforme)
    p_lin = 2500 * e_m * U_m
    iy_req = (5/384) * p_lin * L_m**4 / (E * (df_v_adm/1000))

    Fb = 0.6 * Fcy
    sx_req = ((1/8 * q_viento * U_m * L_m**2) / Fb) * 100**3
    sy_req = ((1/8 * p_lin * L_m**2) / Fb) * 100**3

    sb_pos = L * (0.25 if "L/4" in pos_block else 0.125)

    return ix_req*100**4, iy_req*100**4, sx_req, sy_req, sb_len_sug, sb_pos, area_m2

ix, iy, sx, sy, sb_l, sb_p, a_m2 = ejecutar_calculos()

# =================================================================
# 4. RESULTADOS VISUALES
# =================================================================
st.subheader("📊 Requerimientos Mínimos de Sección")
c1, c2 = st.columns(2)
with c1: st.metric("Inercia Ix (Viento)", f"{ix:.2f} cm⁴")
with c2: st.metric("Inercia Iy (Peso Vidrio)", f"{iy:.2f} cm⁴")

c3, c4 = st.columns(2)
with c3: st.metric("Módulo Sx (Resistencia)", f"{sx:.2f} cm³")
with c4: st.metric("Módulo Sy (Resistencia)", f"{sy:.2f} cm³")

st.divider()

col_sb1, col_sb2 = st.columns(2)
with col_sb1:
    st.markdown(f"""
    <div class="guide-box">
        <h4 style="margin-top:0; color: #ff9900;">Detalle de Apoyos (Vidrio):</h4>
        <ul>
            <li><strong>Largo del calzo:</strong> {sb_l:.2f} mm</li>
            <li><strong>Dureza:</strong> 85 ± 5 Sh A°</li>
            <li><strong>Ubicación:</strong> {sb_p:.1f} mm desde extremos</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col_sb2:
    if os.path.exists("trav.jpg"):
        sub1, sub2 = st.columns([4, 6])
        with sub1: st.image("trav.jpg", use_column_width=True)

# =================================================================
# 5. GENERADOR DE PDF PROFESIONAL (ESTILO PROYECTOS ESTRUCTURALES)
# =================================================================
def generar_pdf_travesano():
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("Logo.png"):
        pdf.image("Logo.png", x=10, y=8, w=33)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Memoria de Calculo: Travesaños", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 7, "Proyectos Estructurales | Structural Lab", ln=True, align='C')
    pdf.ln(15)

    # 1. Datos y 2. Resultados (Compactos para el PDF)
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, " 1. INFORMACION Y RESULTADOS", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f" L: {L} mm | U: {U} mm | Viento q: {q_viento} kgf/m2", ln=True)
    pdf.cell(0, 8, f" Ix Req: {ix:.2f} cm4 | Sx Req: {sx:.2f} cm3 | Iy Req: {iy:.2f} cm4", ln=True)
    
    pdf.set_y(-25); pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Memoria generada por AccuraWall Port - Mauricio Riquelme", align='C')
    return pdf.output()

# --- BOTÓN DE DESCARGA AZUL (SIN SUBRAYADO Y EN UNA LÍNEA) ---
st.sidebar.markdown("---")
try:
    # Llamamos a la función correcta definida arriba
    pdf_bytes = generar_pdf_travesano()
    b64 = base64.b64encode(pdf_bytes).decode()
    file_name = f"Memoria_Travesano_L{int(L)}.pdf"
    
    # CSS para que el botón sea idéntico a tu portal, sin subrayado
    btn_html = f'''
        <style>
        .main-btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #003366;
            color: white !important;
            padding: 12px 10px;
            text-decoration: none !important;
            border-radius: 8px;
            font-weight: bold;
            width: 100%;
            border: none;
            font-size: 14px;
            transition: 0.3s;
        }}
        .main-btn:hover {{
            background-color: #004488;
            text-decoration: none !important;
        }}
        </style>
        <a class="main-btn" href="data:application/pdf;base64,{b64}" download="{file_name}">
            📥 DESCARGAR MEMORIA PDF
        </a>
    '''
    st.sidebar.markdown(btn_html, unsafe_allow_html=True)

except Exception as e:
    # Mensaje de error corregido sin comillas abiertas
    st.sidebar.error(f"Error técnico: {e}")


# =================================================================
# 6. GRÁFICOS DE SENSIBILIDAD
# =================================================================
st.subheader("📈 Análisis de Sensibilidad")
L_axis = np.linspace(2000, 6000, 50)
Ix_plt, Iy_plt = [], []
E_plt = 21000000000 if "Acero" in material_perfil else 7101002754

for lx in L_axis:
    lx_m = lx / 1000
    df_h = (lx / 175) if lx < 4115 else ((lx / 240) + 6.35)
    df_v = min(lx / 360, 3.18)
    r_h = (U/1000) / (2 * lx_m)
    f_h = (1 - (4/3)*r_h**2) if r_h < 1 else 1.0
    Ix_plt.append(((5/384)*q_viento*(U/1000)*lx_m**4 / (E_plt*(df_h/1000))) * f_h * 100**4)
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