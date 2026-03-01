# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
import os

# =================================================================
# 1. CONFIGURACIÓN Y ESTILO
# =================================================================
st.set_page_config(page_title="AccuraWall | Mauricio Riquelme", layout="wide")

st.markdown("""
    <style>
    .main > div { padding-left: 2.5rem; padding-right: 2.5rem; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; }
    .result-box { 
        background-color: #f0f7ff; 
        padding: 25px; 
        border-left: 10px solid #003366; 
        border-radius: 8px; 
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ AccuraWall: Prediseño de Perfiles")
st.markdown("#### **Mullions y Travesaños - Análisis de Flexión y Deflexión**")
st.divider()

# =================================================================
# 2. SIDEBAR: PARÁMETROS TÉCNICOS
# =================================================================
st.sidebar.header("⚙️ Parámetros de Diseño")

with st.sidebar.expander("📐 Geometría y Carga", expanded=True):
    L = st.number_input("Longitud del Elemento (L) [mm]", value=3500.0, step=10.0)
    B = st.number_input("Ancho Tributario (B) [mm]", value=1500.0, step=10.0)
    q = st.number_input("Carga de Viento (q) [kgf/m²]", value=100.0, step=5.0)
    e_vidrio = st.number_input("Espesor Cristal (e) [mm]", value=6.0)

# Lógica del criterio de deformación automática
if L < 4115:
    criterio_sugerido = "L/175"
    valor_df_sugerido = L / 175
else:
    criterio_sugerido = "L/240 + 6.35 mm"
    valor_df_sugerido = (L / 240) + 6.35

with st.sidebar.expander("📏 Criterio de Deformación", expanded=True):
    st.markdown(f"**Sugerido por Norma:** `{criterio_sugerido}`")
    df_admisible = st.number_input("Deflexión Admisible [mm] (Editable)", 
                                    value=float(valor_df_sugerido))

with st.sidebar.expander("🧪 Material y Configuración", expanded=True):
    material = st.selectbox("Material", 
                           ["Aluminio 6063 - T6", "Aluminio 6063 - T5", "Acero A42-27ES"])
    
    # OPCIÓN DE TRAVESAÑOS AÑADIDA
    distribucion = st.radio("Tipo de Elemento / Distribución", 
                               ["Rectangular (Mullion)", "Trapezoidal (Mullion)", "Travesaño (Transom)"])

# =================================================================
# 3. MOTOR DE CÁLCULO
# =================================================================
def calcular_requerimientos():
    # Propiedades según VB
    if material == "Aluminio 6063 - T6":
        E, Fcy = 7101002754, 17576739.5
    elif material == "Aluminio 6063 - T5":
        E, Fcy = 7101002754, 11249113.3
    else: # Acero
        E, Fcy = 21000000000, 27532337.75

    L_m, B_m = L / 1000, B / 1000
    Df_m = df_admisible / 1000

    # Momento Flector (M)
    M = (1/8) * (q * B_m) * (L_m)**2

    # Lógica de Inercia y selección de imagen
    if distribucion == "Rectangular (Mullion)":
        I_req = (5 / 384) * q * B_m * L_m**4 / (E * Df_m)
        img_dist = "rect.jpg"
    elif distribucion == "Trapezoidal (Mullion)":
        ratio = B_m / (2 * L_m)
        factor = (1 - (4/3) * (ratio**2))
        I_req = ((5 / 384) * q * B_m * L_m**4 / (E * Df_m)) * factor
        img_dist = "tra.jpg"
    else: # Travesaño
        # Para travesaños se asume carga rectangular pero con apoyo en el plano horizontal (Ix)
        # Se carga trav.jpg según solicitado
        I_req = (5 / 384) * q * B_m * L_m**4 / (E * Df_m)
        img_dist = "trav.jpg"

    # Módulo Resistente (Sx)
    Fb = 0.6 * Fcy
    S_req = M / Fb

    return I_req * 100**4, S_req * 100**3, img_dist

inercia, modulo, imagen_a_cargar = calcular_requerimientos()

# =================================================================
# 4. DESPLIEGUE DE RESULTADOS E IMAGEN
# =================================================================
st.subheader("📊 Requerimientos Mínimos de Sección")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Inercia (Ix)", f"{inercia:.2f} cm⁴")
with c2:
    st.metric("Módulo (Sx)", f"{modulo:.2f} cm³")
with c3:
    st.metric("Criterio Δ", criterio_sugerido)

st.divider()

col_fig, col_txt = st.columns([1, 1])

with col_fig:
    st.markdown(f"**Distribución: {distribucion}**")
    if os.path.exists(imagen_a_cargar):
        st.image(imagen_a_cargar, use_column_width=True)
    else:
        st.warning(f"💡 Archivo '{imagen_a_cargar}' no encontrado.")
        

with col_txt:
    st.markdown(f"""
    <div class="result-box" style="margin-top:0;">
        <h3 style="margin-top:0;">✅ Especificación:</h3>
        <ul>
            <li><strong>Elemento:</strong> {distribucion}</li>
            <li><strong>Largo L:</strong> {L} mm</li>
            <li><strong>Deflexión límite:</strong> {df_admisible:.2f} mm</li>
            <li><strong>Inercia Req:</strong> {inercia:.2f} cm⁴</li>
        </ul>
        <hr>
        <p><small>Nota: Los travesaños deben verificar adicionalmente la deflexión en el eje 'y' debido al peso del vidrio (Iy).</small></p>
    </div>
    """, unsafe_allow_html=True)

# =================================================================
# 5. GRÁFICO DE SENSIBILIDAD
# =================================================================
st.subheader("📈 Sensibilidad Ix vs Longitud")
L_axis = np.linspace(1000, 6000, 50)
I_axis = []

for lx in L_axis:
    dfx = (lx / 175) if lx < 4115 else ((lx / 240) + 6.35)
    Ex = 7101002754 if material.startswith("Aluminio") else 21000000000
    
    # Lógica de la curva según tipo
    if "Trapezoidal" in distribucion:
        r = (B/1000) / (2 * (lx/1000))
        ix = ((5 / 384) * q * (B/1000) * (lx/1000)**4 / (Ex * (dfx/1000))) * (1 - (4/3)*r**2)
    else:
        ix = (5 / 384) * q * (B/1000) * (lx/1000)**4 / (Ex * (dfx/1000))
    I_axis.append(ix * 100**4)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(L_axis, I_axis, color='#003366', label=f'Ix ({distribucion})')
ax.axvline(4115, color='red', ls='--', alpha=0.5, label='Umbral 4115mm')
ax.scatter([L], [inercia], color='red', zorder=5)
ax.set_xlabel("L (mm)")
ax.set_ylabel("Ix (cm4)")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>AccuraWall Port | Mauricio Riquelme</div>", unsafe_allow_html=True)