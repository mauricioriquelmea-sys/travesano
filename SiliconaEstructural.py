# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
import os
import base64
from fpdf import FPDF

# =================================================================
# 1. CONFIGURACIÓN Y ESTILO (UI/UX)
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
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Prediseño de Mullions")
st.markdown("#### **Control de Deflexión y Distribución de Carga Tributaria**")
st.divider()

# =================================================================
# 2. SIDEBAR: PARÁMETROS TÉCNICOS
# =================================================================
st.sidebar.header("⚙️ Parámetros de Diseño")

with st.sidebar.expander("📐 Geometría y Carga", expanded=True):
    L = st.number_input("Alto del Mullion (L) [mm]", value=3500.0, step=10.0)
    B = st.number_input("Ancho Tributario (B) [mm]", value=1500.0, step=10.0)
    q = st.number_input("Carga de Viento (q) [kgf/m²]", value=100.0, step=5.0)
    e_vidrio = st.number_input("Espesor Vidrio (e) [mm]", value=6.0)

# Criterio automático NCh
if L < 4115:
    criterio_sugerido = "L/175"
    valor_df_sugerido = L / 175
else:
    criterio_sugerido = "L/240 + 6.35 mm"
    valor_df_sugerido = (L / 240) + 6.35

with st.sidebar.expander("📏 Criterio de Deformación", expanded=True):
    st.markdown(f"**Sugerido por Norma:** `{criterio_sugerido}`")
    df_admisible = st.number_input("Deflexión Admisible [mm]", value=float(valor_df_sugerido))

with st.sidebar.expander("🧪 Material y Distribución", expanded=True):
    material = st.selectbox("Material", ["Aluminio 6063 - T6", "Aluminio 6063 - T5", "Acero A42-27ES"])
    distribucion = st.radio("Distribución de Carga", ["Rectangular", "Trapezoidal"])

# =================================================================
# 3. MOTOR DE CÁLCULO
# =================================================================
def calcular_requerimientos():
    if material == "Aluminio 6063 - T6":
        E, Fcy = 7101002754, 17576739.5
    elif material == "Aluminio 6063 - T5":
        E, Fcy = 7101002754, 11249113.3
    else: # Acero
        E, Fcy = 21000000000, 27532337.75

    L_m, B_m = L / 1000, B / 1000
    Df_m = df_admisible / 1000

    if distribucion == "Rectangular":
        I_req = (5 / 384) * q * B_m * L_m**4 / (E * Df_m)
        M = (1/8) * (q * B_m) * (L_m)**2
        img_dist = "rect.jpg"
    else:
        # Ajuste Trapezoidal real para Mullions
        ratio = B_m / (2 * L_m)
        factor_i = (1 - (4/3) * (ratio**2))
        factor_m = (1 - (2/3) * (ratio**2))
        I_req = ((5 / 384) * q * B_m * L_m**4 / (E * Df_m)) * factor_i
        M = ((1/8) * (q * B_m) * (L_m)**2) * factor_m
        img_dist = "trap.jpg"

    Fb = 0.6 * Fcy
    S_req = M / Fb
    return I_req * 100**4, S_req * 100**3, img_dist

inercia, modulo, imagen_a_cargar = calcular_requerimientos()

# =================================================================
# 4. DESPLIEGUE DE RESULTADOS
# =================================================================
st.subheader("📊 Requerimientos Mínimos de Sección")
c1, c2, c3 = st.columns(3)
with c1: st.metric("Inercia (Ix)", f"{inercia:.2f} cm⁴")
with c2: st.metric("Módulo (Sx)", f"{modulo:.2f} cm³")
with c3: st.metric("Criterio Δ", criterio_sugerido)

st.divider()

col_fig, col_txt = st.columns([1, 1])
with col_fig:
    st.markdown(f"**Modelo de Carga: {distribucion}**")
    if os.path.exists(imagen_a_cargar):
        # Sub-columnas para reducción al 40%
        sub1, sub2 = st.columns([4, 6])
        with sub1:
            st.image(imagen_a_cargar, caption=None, use_column_width=True)
    else:
        st.warning(f"💡 Archivo '{imagen_a_cargar}' no encontrado.")

with col_txt:
    st.markdown(f"""
    <div class="result-box" style="margin-top:0;">
        <h3 style="margin-top:0;">✅ Especificación Final:</h3>
        <ul>
            <li><strong>Largo L:</strong> {L} mm</li>
            <li><strong>Ancho B:</strong> {B} mm</li>
            <li><strong>Deflexión límite:</strong> {df_admisible:.2f} mm</li>
            <li><strong>Inercia Req:</strong> {inercia:.2f} cm⁴</li>
        </ul>
        <hr>
        <p><small>Nota: La inercia calculada con distribución {distribucion.lower()} es la base del diseño.</small></p>
    </div>
    """, unsafe_allow_html=True)

# =================================================================
# 5. GENERADOR DE PDF PROFESIONAL
# =================================================================
def generar_pdf_mullion():
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("Logo.png"):
        pdf.image("Logo.png", x=10, y=8, w=33)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Memoria de Calculo: Mullions", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 7, "Proyectos Estructurales | Structural Lab", ln=True, align='C')
    pdf.ln(15)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, " 1. INFORMACION DEL DISENO", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f" Alto del Mullion (L): {L} mm | Ancho Tributario (B): {B} mm", ln=True)
    pdf.cell(0, 8, f" Carga Viento q: {q} kgf/m2 | Distribucion: {distribucion}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, " 2. RESULTADOS ESTRUCTURALES", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 8, f" Inercia Ix Req: {inercia:.2f} cm4", border=0)
    pdf.cell(95, 8, f" Modulo Sx Req: {modulo:.2f} cm3", ln=True)
    pdf.cell(0, 8, f" Criterio de Deflexion: {criterio_sugerido} ({df_admisible:.2f} mm)", ln=True)
    pdf.cell(0, 8, f" Material Especificado: {material}", ln=True)
    
    pdf.set_y(-25)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Memoria generada por AccuraWall Port - Mauricio Riquelme", align='C')
    
    return pdf.output()

st.sidebar.markdown("---")
if st.sidebar.button("📄 Preparar Reporte PDF"):
    try:
        pdf_bytes = generar_pdf_mullion()
        b64 = base64.b64encode(pdf_bytes).decode()
        btn_html = f'''
            <div style="text-align: center; margin-top: 10px;">
                <a href="data:application/pdf;base64,{b64}" download="Memoria_Mullion_L{int(L)}mm.pdf" 
                   style="background-color: #ff9900; color: white; padding: 12px 20px; text-decoration: none; 
                   border-radius: 5px; font-weight: bold; display: block;">
                   📥 DESCARGAR REPORTE
                </a>
            </div>
        '''
        st.sidebar.markdown(btn_html, unsafe_allow_html=True)
        st.sidebar.info("El archivo está listo. Presiona el botón naranja arriba.")
    except Exception as e:
        st.sidebar.error(f"Error técnico: {e}")

# =================================================================
# 6. GRÁFICO DE SENSIBILIDAD
# =================================================================
st.subheader(f"📈 Sensibilidad Ix vs Longitud ({distribucion})")

L_axis = np.linspace(2000, 6000, 50)
I_axis = []
for lx in L_axis:
    dfx = (lx / 175) if lx < 4115 else ((lx / 240) + 6.35)
    Ex = 7101002754 if material.startswith("Aluminio") else 21000000000
    if distribucion == "Rectangular":
        ix = (5 / 384) * q * (B/1000) * (lx/1000)**4 / (Ex * (dfx/1000))
    else:
        r = (B/1000) / (2 * (lx/1000))
        ix = ((5 / 384) * q * (B/1000) * (lx/1000)**4 / (Ex * (dfx/1000))) * (1 - (4/3)*r**2)
    I_axis.append(ix * 100**4)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(L_axis, I_axis, color='#003366', label=f'Ix ({distribucion})')
ax.axvline(4115, color='red', ls='--', alpha=0.5, label='Umbral 4115mm')
ax.scatter([L], [inercia], color='red', zorder=5)
ax.set_xlabel("L (mm)")
ax.set_ylabel("Ix (cm4)")
ax.legend(); ax.grid(True, alpha=0.3)
st.pyplot(fig)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>AccuraWall Port | Mauricio Riquelme</div>", unsafe_allow_html=True)