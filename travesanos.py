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
# 3. MOTOR DE CÁLCULO ESTÁTICO
# =================================================================
def calcular_requerimientos_travesano():
    # Propiedades del Material (Módulo de Elasticidad E y Fluencia Fcy)
    if material == "Aluminio 6063 - T6":
        E, Fcy = 7101002754, 17576739.5 # kgf/m2
    elif material == "Aluminio 6063 - T5":
        E, Fcy = 7101002754, 11249113.3
    else: # Acero
        E, Fcy = 21000000000, 27532337.75

    # Conversión de unidades de entrada a metros
    L_m = L / 1000
    U_m = U / 1000
    e_m = e_vidrio / 1000
    Df_h_m = df_h_adm / 1000
    Df_v_m = df_v_adm / 1000

    # --- A. CÁLCULO ANTE CARGA DE VIENTO (Inercia Ix requerida) ---
    # Se asume carga trapezoidal real (como en el mullion anterior)
    # Ancho tributario para el travesaño es la altura del vidrio superior (U)
    M_viento = (1/8) * (q_viento * U_m) * (L_m)**2
    
    # Factor de ajuste para carga trapezoidal real (B/2L en mullion, aquí U/2L)
    ratio_h = U_m / (2 * L_m)
    factor_h = (1 - (4/3) * (ratio_h**2)) if ratio_h < 1 else 1.0 # ratio_h=1 para rectangular pura
    
    # Inercia Ix requerida para controlar deflexión horizontal
    Ix_req_m4 = ((5 / 384) * q_viento * U_m * L_m**4 / (E * Df_h_m)) * factor_h

    # --- B. CÁLCULO ANTE PESO PROPIO DEL VIDRIO (Inercia Iy requerida) ---
    # Densidad del vidrio ~2500 kgf/m3
    peso_vidrio_kgml = 2500 * e_m * U_m  # Carga lineal debida al peso
    
    # Momento flector debido al peso (Iy trabaja aquí)
    M_peso = (1/8) * peso_vidrio_kgml * (L_m)**2
    
    # Inercia Iy requerida para controlar deflexión vertical (L/360 o 3.18mm)
    # Se asume carga uniforme (DL) para el peso propio
    Iy_req_m4 = (5 / 384) * peso_vidrio_kgml * L_m**4 / (E * Df_v_m)

    # --- C. CÁLCULO DE SETTING BLOCKS ---
    # Área del vidrio en pies cuadrados (1 sq ft = 92903.04 mm2)
    area_glass_sqft = (L * U) / 92903.04
    
    # Longitud requerida por pulgada por sqft según material
    if mat_block == "Neopreno/EPDM/Silicona":
        len_inch = 0.1 * area_glass_sqft #
        min_len_inch = 4.0 if L > 1219.2 else 0.0  # L > 48"
    elif mat_block == "Plomo (Lead)":
        len_inch = 0.05 * area_glass_sqft #
        min_len_inch = 4.0 if L > 1219.2 else 0.0 #
    else: # Lock-strip Gasket
        len_inch = 0.5 * area_glass_sqft #
        min_len_inch = 6.0 #
    
    # Longitud final del bloque (pulgadas a mm)
    final_len_inch = max(len_inch, min_len_inch) #
    block_len_mm = final_len_inch * 25.4 #
    
    # Ubicación sugerida desde los extremos (L/4 o L/8)
    factor_pos = 0.25 if pos_block.startswith("L/4") else 0.125
    block_pos_mm = L * factor_pos #

    # Conversión de resultados finales a unidades cm
    Ix_req_cm4 = Ix_req_m4 * 100**4
    Iy_req_cm4 = Iy_req_m4 * 100**4
    
    # Requerimiento de Módulo Resistente (Sx) ante viento
    Fb = 0.6 * Fcy
    Sx_req_cm3 = (M_viento / Fb) * 100**3

    return Ix_req_cm4, Iy_req_cm4, Sx_req_cm3, block_len_mm, block_pos_mm, area_glass_sqft

# Ejecutar cálculos estáticos
ix, iy, sx, sb_len, sb_pos, glass_area = calcular_requerimientos_travesano()

# =================================================================
# 4. DESPLIEGUE DE RESULTADOS E IMÁGENES GUÍA
# =================================================================
st.subheader("📊 Resumen de Requerimientos Mínimos de Sección")

# Métricas principales de inercia
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Inercia Ix (Viento)", f"{ix:.2f} cm⁴", help=f"Controlada por {crit_h_sug}")
with c2:
    st.metric("Inercia Iy (Peso Vidrio)", f"{iy:.2f} cm⁴", help="Controlada por min(L/360, 3.18mm)")
with c3:
    st.metric("Módulo Sx (Resistencia)", f"{sx:.2f} cm³")

st.divider()

# Sección de Guías Visuales e Imágenes
col_guias, col_spec = st.columns([1.2, 1])

with col_guias:
    st.markdown("### 🖼️ Guías Visuales de Diseño")
    
    # Carga dinámica de imagen del travesaño (trav.jpg)
    img_trav = "trav.jpg"
    if os.path.exists(img_trav):
        st.image(img_trav, caption="Diagrama de Cargas del Travesaño", use_column_width=True)
    else:
        st.warning(f"💡 Archivo '{img_trav}' no encontrado en el repositorio. Sube la imagen del travesaño.")
    
    st.markdown("---")
    
    # Carga dinámica de imagen de setting blocks (setting.jpg)
    img_setting = "setting.jpg"
    if os.path.exists(img_setting):
        st.image(img_setting, caption="Guía de Posicionamiento de Setting Blocks (L/4 vs L/8)", use_column_width=True)
    else:
        st.warning(f"💡 Archivo '{img_setting}' no encontrado en el repositorio. Sube la imagen de los calzos.")

with col_spec:
    st.markdown("### ✅ Especificación Final y Apoyos")
    
    # Caja de resultados del perfil
    st.markdown(f"""
    <div class="result-box" style="margin-top:0;">
        <h4 style="margin-top:0;">Requerimientos del Perfil:</h4>
        <ul>
            <li><strong>Largo Travesaño L:</strong> {L:.0f} mm</li>
            <li><strong>Altura Superior U:</strong> {U:.0f} mm</li>
            <li><strong>Material:</strong> {material}</li>
            <li><strong>Inercia Ix Mínima:</strong> {ix:.2f} cm⁴</li>
            <li><strong>Inercia Iy Mínima:</strong> {iy:.2f} cm⁴</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Caja de resultados de los setting blocks
    pos_text = "L/4 (Preferida)" if sb_pos == L*0.25 else "L/8 (Alternativa)"
    st.markdown(f"""
    <div class="guide-box">
        <h4 style="margin-top:0; color: #ff9900;">Especificación de Setting Blocks:</h4>
        <ul>
            <li><strong>Área del Vidrio:</strong> {glass_area:.2f} ft²</li>
            <li><strong>Material Calzo:</strong> {mat_block}</li>
            <li><strong>Longitud cada bloque:</strong> {sb_len:.1f} mm</li>
            <li><strong>Ubicar a:</strong> {sb_pos:.1f} mm desde extremos</li>
            <li><strong>Criterio de Posición:</strong> {pos_text}</li>
        </ul>
        <p style="font-size: 0.8rem; color: #666; margin-top:10px;">
            Nota: La longitud mínima del bloque nunca debe ser menor a 4" (101.6mm) para anchos > 48".
        </p>
    </div>
    """, unsafe_allow_html=True)

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