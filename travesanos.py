# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os

# =================================================================
# 1. CONFIGURACIÓN, ESTILO Y TÍTULO
# =================================================================
st.set_page_config(page_title="AccuraWall | Prediseño de Travesaños", layout="wide")

# Estilo CSS personalizado para mejorar la visualización
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
    .guide-box {
        background-color: #fffaf0;
        padding: 15px;
        border: 1px solid #ff9900;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Prediseño de Travesaños (Horizontales)")
st.markdown("#### **Control de Deflexión Combinada y Especificación de Apoyos de Vidrio**")
st.divider()

# =================================================================
# 2. SIDEBAR: PARÁMETROS TÉCNICOS Y CRITERIOS
# =================================================================
st.sidebar.header("⚙️ Parámetros de Diseño")

# --- Geometría y Cargas ---
with st.sidebar.expander("📐 Geometría y Cargas", expanded=True):
    L = st.number_input("Longitud del Travesaño (L) [mm]", value=1500.0, step=10.0)
    U = st.number_input("Altura de Vidrio Superior (U) [mm]", value=2500.0, step=10.0)
    q_viento = st.number_input("Carga de Viento de Diseño (q) [kgf/m²]", value=100.0, step=5.0)
    e_vidrio = st.number_input("Espesor Total del Vidrio (e) [mm]", value=12.0)

# --- Criterio de Deformación HORIZONTAL (Carga de Viento) ---
# Lógica automática según longitud para deflexión horizontal
if L < 4115:
    crit_h_sug = "L/175"
    val_h_sug = L / 175
else:
    crit_h_sug = "L/240 + 6.35 mm"
    val_h_sug = (L / 240) + 6.35

with st.sidebar.expander("📏 Criterio Deformación HORIZONTAL", expanded=True):
    st.markdown(f"**Sugerido (Viento):** `{crit_h_sug}`")
    df_h_adm = st.number_input("Deflexión Horiz. Admisible [mm]", value=float(val_h_sug))

# --- Criterio de Deformación VERTICAL (Peso del Vidrio) ---
# El criterio estándar es L/360, limitado a un máximo de 3.18 mm para no dañar sellos
val_v_sug = min(L / 360, 3.18)

with st.sidebar.expander("📏 Criterio Deformación VERTICAL", expanded=True):
    st.markdown(f"**Estándar (Peso):** `min(L/360, 3.18mm)`")
    df_v_adm = st.number_input("Deflexión Vert. Admisible [mm]", value=float(val_v_sug))

# --- Material y Configuración de Apoyos ---
with st.sidebar.expander("🧪 Material y Setting Blocks", expanded=True):
    material = st.selectbox("Material del Perfil", 
                            ["Aluminio 6063 - T6", "Aluminio 6063 - T5", "Acero A42-27ES"])
    
    st.markdown("---")
    st.markdown("**Configuración de Setting Blocks (Calzos)**")
    mat_block = st.selectbox("Material del Calzo", 
                             ["Neopreno/EPDM/Silicona", "Plomo (Lead)", "Lock-strip Gasket"])
    pos_block = st.radio("Posición de Apoyo", ["L/4 (Preferida)", "L/8 (Alternativa)"])

# =================================================================
# 3. MOTOR DE CÁLCULO ACTUALIZADO
# =================================================================
def calcular_requerimientos_completos():
    # Propiedades del Material
    if material == "Aluminio 6063 - T6":
        E, Fcy = 7101002754, 17576739.5
    elif material == "Aluminio 6063 - T5":
        E, Fcy = 7101002754, 11249113.3
    else: # Acero
        E, Fcy = 21000000000, 27532337.75

    L_m, U_m, e_m = L / 1000, U / 1000, e_vidrio / 1000
    Df_h_m, Df_v_m = df_h_adm / 1000, df_v_adm / 1000

    # --- EJE X-X (Viento / Inercia Ix) ---
    M_viento = (1/8) * (q_viento * U_m) * (L_m)**2
    ratio_h = U_m / (2 * L_m)
    factor_h = (1 - (4/3) * (ratio_h**2)) if ratio_h < 1 else 1.0
    Ix_req = ((5 / 384) * q_viento * U_m * L_m**4 / (E * Df_h_m)) * factor_h

    # --- EJE Y-Y (Peso Vidrio / Inercia Iy) ---
    peso_vidrio_kgml = 2500 * e_m * U_m 
    M_peso = (1/8) * peso_vidrio_kgml * (L_m)**2
    Iy_req = (5 / 384) * peso_vidrio_kgml * L_m**4 / (E * Df_v_m)

    # --- MÓDULOS RESISTENTES (S = M / Fb) ---
    Fb = 0.6 * Fcy
    Sx_req = (M_viento / Fb) * 100**3 # cm3
    Sy_req = (M_peso / Fb) * 100**3   # cm3

    return Ix_req * 100**4, Iy_req * 100**4, Sx_req, Sy_req

ix, iy, sx, sy = calcular_requerimientos_completos()

# =================================================================
# 4. DESPLIEGUE EN DOS FILAS
# =================================================================
st.subheader("📊 Resumen de Requerimientos Mínimos de Sección")

# FILA 1: INERCIAS
fila1_c1, fila1_c2 = st.columns(2)
with fila1_c1:
    st.metric("Inercia Ix (Viento)", f"{ix:.2f} cm⁴")
with fila1_c2:
    st.metric("Inercia Iy (Peso Vidrio)", f"{iy:.2f} cm⁴")

# FILA 2: MÓDULOS SECCIONALES
fila2_c1, fila2_c2 = st.columns(2)
with fila2_c1:
    st.metric("Módulo Sx (Resistencia Viento)", f"{sx:.2f} cm³")
with fila2_c2:
    st.metric("Módulo Sy (Resistencia Peso)", f"{sy:.2f} cm³")

st.divider()

# =================================================================
# 5. GRÁFICOS DE SENSIBILIDAD (Ix e Iy vs LONGITUD)
# =================================================================
st.subheader("📈 Análisis de Sensibilidad de Inercia Requerida")
st.markdown("Visualización de cómo aumentan Ix e Iy al incrementar la longitud del travesaño (L), manteniendo fijos U y q.")

# Rango de longitudes para el eje X (2000mm a 6000mm)
L_axis = np.linspace(2000, 6000, 50)
Ix_axis = []
Iy_axis = []

# Módulo de elasticidad según material seleccionado
Ex = 21000000000 if material == "Acero A42-27ES" else 7101002754

# Parámetros fijos para el gráfico
U_m_plot = U / 1000
e_m_plot = e_vidrio / 1000

# Bucle para calcular inercias en cada punto de longitud
for lx in L_axis:
    lx_m = lx / 1000
    
    # --- Cálculo Ix (Viento) ---
    # Criterio de deflexión horizontal variable según longitud
    dfx_h = (lx / 175) if lx < 4115 else ((lx / 240) + 6.35)
    
    # Factor trapezoidal variable
    r_h = U_m_plot / (2 * lx_m)
    f_h = (1 - (4/3)*r_h**2) if r_h < 1 else 1.0
    
    # Ix requerida en cm4
    ix_plot = ((5 / 384) * q_viento * U_m_plot * lx_m**4 / (Ex * (dfx_h/1000))) * f_h
    Ix_axis.append(ix_plot * 100**4)
    
    # --- Cálculo Iy (Peso) ---
    # Criterio de deflexión vertical estándar variable min(L/360, 3.18)
    dfx_v = min(lx / 360, 3.18)
    
    # Iy requerida en cm4 (uniform load assumed for DL)
    peso_v = 2500 * e_m_plot * U_m_plot
    iy_plot = (5 / 384) * peso_v * lx_m**4 / (Ex * (dfx_v/1000))
    Iy_axis.append(iy_plot * 100**4)

# Creación de los gráficos
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Gráfico 1: Inercia Ix (Viento, Horizontal)
ax1.plot(L_axis, Ix_axis, color='#003366', linewidth=2, label=f'Ix Req. (Viento, U={U}mm)')
ax1.axvline(4115, color='red', ls='--', alpha=0.5, label='Umbral Cambio Criterio (4115mm)')
ax1.scatter([L], [ix], color='red', zorder=5, label='Punto de Diseño Actual')
ax1.set_xlabel("Longitud Travesaño L (mm)")
ax1.set_ylabel("Inercia Ix Req. (cm4)")
ax1.set_title("Ix Requerida ante Carga de Viento")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Gráfico 2: Inercia Iy (Peso, Vertical)
ax2.plot(L_axis, Iy_axis, color='#ff9900', linewidth=2, label=f'Iy Req. (Peso Vidrio, e={e_vidrio}mm)')
ax2.scatter([L], [iy], color='red', zorder=5, label='Punto de Diseño Actual')
ax2.set_xlabel("Longitud Travesaño L (mm)")
ax2.set_ylabel("Inercia Iy Req. (cm4)")
ax2.set_title("Iy Requerida ante Peso Propio del Vidrio")
ax2.legend()
ax2.grid(True, alpha=0.3)

# Desplegar los gráficos
st.pyplot(fig)

# Pie de página
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>AccuraWall Port | Mauricio Riquelme | Prediseño de Travesaños</div>", unsafe_allow_html=True)